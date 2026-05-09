# Gmail → Payment Sync Plan

## Context

HDFC bank sends email alerts for every credit/debit transaction. This plan builds a `/sync-gmail`
Claude Code skill that reads those emails and stages each transaction as an ApprovalRequest in the
ERP for operator review before it becomes a real Payment record.

**Gmail MCP servers configured (both connected):**
- `gmail-enterprise`: `npx -y @gongrzhe/server-gmail-autoauth-mcp`
- `gmail-zinc`: `npx -y @gongrzhe/server-gmail-autoauth-mcp`

**Why a skill (not a management command or Makefile target):**
Skills run inside Claude Code, which already has Gmail MCP available. No JSON piping, no OAuth
setup in Docker, no Node.js-in-container problem. The skill IS the orchestrator — it fetches,
parses, matches, and calls the Django DB layer directly.

---

## Architecture

```
User types: /sync-gmail [--days 30] [--dry-run]
        ↓
Claude Code skill loads (.claude/skills/sync-gmail.md)
        ↓
Skill uses gmail-enterprise MCP
  → search HDFC alert emails (last N days)
  → for each email: extract date, amount, direction, reference_number, narration, gmail_message_id
        ↓
Skill fetches party list for matching:
  docker compose exec web python manage.py shell -c "..."
        ↓
Skill fuzzy-matches narrations → Party names + confidence scores
        ↓
Skill calls management command with structured data:
  docker compose exec web python manage.py stage_gmail_payments --data '[...]'
        ↓
Management command: dedup + create ApprovalRequests (DB only, no Gmail logic)
        ↓
Skill reports: N staged, N skipped, N unmatched
        ↓
Operator visits /governance/approvals/ → reviews, approves → Payment created
```

---

## Part 1: The Skill

**File:** `.claude/skills/sync-gmail.md`

This file lives in the project repo — version-controlled, available to anyone with Claude Code
on this project.

### Skill instructions (what the skill file contains)

```markdown
# /sync-gmail — Gmail Payment Sync

Sync HDFC bank transaction alerts from Gmail into the ERP as staged ApprovalRequests.

## Steps

1. **Parse arguments** from user input:
   - `--days N` (default: 30) — how far back to look
   - `--dry-run` — report only, no DB writes
   - `--account enterprise|zinc` (default: enterprise) — which Gmail MCP to use

2. **Fetch HDFC emails** using the gmail-enterprise (or gmail-zinc) MCP:
   - Search query: `from:alerts@hdfcbank.com newer_than:{days}d`
   - Also try: `from:noreply@hdfcbank.com` and subject containing "debited OR credited OR transaction"
   - For each matching email, read the full body

3. **Extract transaction data** from each email body.
   Parse for:
   - Amount (e.g. "Rs.5,000.00" or "INR 5000")
   - Direction ("debited" → debit, "credited" → credit)
   - Date (look for DD-MM-YYYY or DD/MM/YYYY patterns)
   - Reference number (NEFT ref, UPI ref no, cheque number)
   - Narration / Info line (the line after "Info:" or "Remarks:")
   - Gmail message ID

   If an email cannot be parsed (format unrecognised), log it as PARSE_ERROR and continue.

4. **Fetch the party list** for matching:
   Run: `docker compose exec web python manage.py shell -c "
   from masters.models import Party; import json
   print(json.dumps(list(Party.objects.filter(is_active=True).values('id','name'))))
   "`

5. **Fuzzy-match** each narration against party names:
   - Tokenise the narration and the party name; look for shared meaningful words (>3 chars)
   - Score: proportion of party name words found in narration
   - Confidence ≥ 0.65 → auto-match; < 0.65 → leave party blank (UNMATCHED)

6. **Build JSON payload** — array of transaction objects:
   ```json
   [
     {
       "gmail_message_id": "18f3a2b1c4d5e6f7",
       "transaction_date": "2026-05-09",
       "amount": "5000.00",
       "direction": "credit",
       "reference_number": "NEFT123456789",
       "narration": "NEFT-ICICI-PREMCO INDIA-REF123",
       "mode": "bank",
       "party_id": 5,
       "confidence": 0.85
     }
   ]
   ```
   For UNMATCHED transactions, omit `party_id` and set `confidence` to the actual score.

7. **Call management command**:
   If `--dry-run`:
     `docker compose exec web python manage.py stage_gmail_payments --dry-run --data '<JSON>'`
   Otherwise:
     `docker compose exec web python manage.py stage_gmail_payments --data '<JSON>'`

8. **Report results** to the user — show the command output plus a summary table:

   | Status | Date | Direction | Amount | Party | Confidence |
   |--------|------|-----------|--------|-------|------------|
   | STAGED | 2026-05-09 | credit | Rs.5,000 | Premco India | 85% |
   | STAGED | 2026-05-08 | debit | Rs.1,200 | Fitwell Fasteners | 78% |
   | UNMATCHED | 2026-05-06 | credit | Rs.8,500 | — | 42% |
   | SKIPPED | 2026-05-05 | credit | Rs.3,000 | — | dup |

   End with: "Visit /governance/approvals/ to review and approve staged transactions."
```

---

## Part 2: The Management Command

**File:** `finance/management/commands/stage_gmail_payments.py`

Pure DB layer — no Gmail logic, no MCP calls. Accepts pre-processed JSON from the skill.

**No new pip dependencies.**

### Arguments

| Arg | Description |
|-----|-------------|
| `--data JSON` | JSON array of transactions (from skill) |
| `--dry-run` | Print what would happen, commit nothing |
| `--clear-staged` | Delete pending ApprovalRequests from prior Gmail syncs |

### Deduplication

```python
# Skip if Payment already committed with this reference
Payment.objects.filter(reference_number=txn["reference_number"],
                       payment_date=txn["transaction_date"]).exists()

# Skip if already staged (pending ApprovalRequest for this Gmail message)
ApprovalRequest.objects.filter(metadata__gmail_message_id=txn["gmail_message_id"],
                               status="pending").exists()
```

### ApprovalRequest creation

Uses existing `governance.services.create_approval_request()` — same pattern as the admin mixin.

```python
create_approval_request(
    action_type=ApprovalRequest.ActionType.CREATE,
    submitted_by=None,
    model_class=Payment,
    object_id=None,
    before_snapshot={},
    after_snapshot={
        "party_id": txn.get("party_id"),
        "payment_date": txn["transaction_date"],
        "amount": txn["amount"],
        "mode": txn.get("mode", "bank"),
        "reference_number": txn.get("reference_number", ""),
        "remarks": f"Gmail sync | {txn.get('narration','')} | msg:{txn['gmail_message_id']}",
    },
    metadata={
        "gmail_message_id": txn["gmail_message_id"],
        "direction": txn["direction"],
        "confidence": txn.get("confidence", 0),
        "narration": txn.get("narration", ""),
        "source": "gmail_sync",
    },
    reason=f"HDFC Gmail sync — {txn['direction']} Rs.{txn['amount']} on {txn['transaction_date']}",
)
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `.claude/skills/sync-gmail.md` | The `/sync-gmail` skill — Gmail fetch + parse + match orchestration |
| `finance/management/__init__.py` | Package marker |
| `finance/management/commands/__init__.py` | Package marker |
| `finance/management/commands/stage_gmail_payments.py` | DB-only: dedup + ApprovalRequest creation |

**No new pip dependencies. No changes to existing files.**

---

## Usage

```
/sync-gmail                    # sync last 30 days
/sync-gmail --days 7           # sync last 7 days only
/sync-gmail --dry-run          # preview, no DB writes
/sync-gmail --account zinc     # use gmail-zinc MCP instead
```

---

## Implementation Order

1. Create `finance/management/` package + `stage_gmail_payments.py`
2. Test command with hand-crafted JSON payload + `--dry-run`
3. Create `.claude/skills/sync-gmail.md`
4. Run `/sync-gmail --dry-run` in Claude Code — inspect Gmail fetch + parsing output
5. Tune narration parsing if HDFC email format differs from expected
6. Run `/sync-gmail` (live) — review ApprovalRequests at `/governance/approvals/`
7. Approve one test record → confirm Payment created correctly
8. Re-run → confirm duplicates skipped

---

## Verification

```bash
# 1. Management command standalone test
docker compose exec web python manage.py stage_gmail_payments --dry-run --data '[
  {"gmail_message_id":"test001","transaction_date":"2026-05-09","amount":"5000.00",
   "direction":"credit","reference_number":"NEFT-TEST-001","narration":"PREMCO INDIA",
   "party_id":1,"confidence":0.85}
]'

# 2. /sync-gmail --dry-run in Claude Code → no DB writes, shows parse + match results
# 3. /sync-gmail live → ApprovalRequests appear at /governance/approvals/
# 4. Approve one → Payment exists in /admin/finance/payment/
# 5. Re-run /sync-gmail → same transactions show as SKIPPED (dup)
# 6. Existing Playwright tests → all pass (no existing code changed)
```
