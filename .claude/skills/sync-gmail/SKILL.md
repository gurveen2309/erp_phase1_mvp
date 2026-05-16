---
name: sync-gmail
description: Sync HDFC bank transaction alert emails from Gmail into the ERP as staged ApprovalRequests.
---

# /sync-gmail — Gmail Payment Sync

Sync HDFC bank transaction alert emails from Gmail into the ERP as staged ApprovalRequests.

## Arguments

Parse from the user's invocation string:
- `--days N` (default: 30) — how far back to search
- `--dry-run` — report only, no DB writes
- `--account enterprise|zinc` (default: zinc) — which Gmail MCP to use

## Step 1 — Authenticate Gmail

Call `mcp__gmail-zinc__list_email_labels` (or the enterprise variant if `--account enterprise`) with no arguments. This triggers OAuth if the session is not already authenticated. Wait for it to succeed before proceeding.

## Step 2 — Fetch HDFC emails

Use `mcp__gmail-zinc__search_emails` (or `mcp__gmail-enterprise__search_emails` if `--account enterprise`).

Search query: `from:alerts@hdfcbank.bank.in newer_than:{days}d`

If that returns 0 results, also try:
- `subject:(debited OR credited OR transaction) newer_than:{days}d`

For each matching email, read the full body with `mcp__gmail-zinc__read_email` (or enterprise variant).

## Step 3 — Extract transaction data from each email body

Parse each email body for the following fields. HDFC alert emails typically look like:

```
Dear Customer, Rs.5,000.00 has been debited from your account XX1234 on 09-05-2026.
Info: NEFT-ICICI-PREMCO INDIA EXIM-NEFT2026050900123
Avl Bal: Rs.12,345.67
```

Or for credits:
```
Rs.8,500.00 has been credited to your A/c XX1234 on 08-05-2026.
Info: NEFT/UPI/RTGS ref details here
```

**Only process credit transactions.** Skip any email that contains "debited" — do not include it in the payload at all.

Additionally, skip UPI credit transactions where the sender name in the narration matches any of these personal names (case-insensitive):
- Gurveen Singh
- Kuldip Singh
- Mandeep Kaur
- Avneet Kaur

Extract:
| Field | How to find it |
|-------|---------------|
| `amount` | Number after "Rs." — strip commas, convert to decimal string |
| `direction` | Always `"credit"` (debits are excluded) |
| `transaction_date` | DD-MM-YYYY or DD/MM/YYYY pattern → reformat to YYYY-MM-DD |
| `reference_number` | Text on the Info/Ref line — grab the full token (NEFT ref, UPI ref, cheque no.) |
| `narration` | Full Info line content after "Info:" or "Remarks:" |
| `gmail_message_id` | The email's message ID from the search result |
| `mode` | Default `"bank"`; if "cheque" in narration → `"cheque"`; if "UPI" → `"bank"` |

If an email body cannot be parsed (unrecognised format), log it as PARSE_ERROR and continue.

## Step 4 — Fetch party list

```bash
docker compose exec web python manage.py shell -c "
from masters.models import Party; import json
print(json.dumps(list(Party.objects.filter(is_active=True).values('id','name'))))
"
```

## Step 5 — Fuzzy-match narrations to parties

For each transaction's `narration`, match against party names:

1. Tokenise both (split on spaces, `-`, `/`, `.`; lowercase; drop tokens ≤ 3 chars)
2. Score = number of party name tokens found in narration tokens / total party name tokens
3. Confidence ≥ 0.65 → set `party_id`; < 0.65 → leave `party_id` absent, mark UNMATCHED

Use the highest-scoring party. If two parties tie, leave UNMATCHED.

## Step 6 — Build JSON payload

Construct a JSON array:

```json
[
  {
    "gmail_message_id": "18f3a2b1c4d5e6f7",
    "transaction_date": "2026-05-09",
    "amount": "5000.00",
    "direction": "credit",
    "reference_number": "NEFT-ICICI-PREMCO-REF123",
    "narration": "NEFT-ICICI-PREMCO INDIA EXIM-NEFT123",
    "mode": "bank",
    "party_id": 5,
    "confidence": 0.85
  }
]
```

`direction` is always `"credit"`. Omit `party_id` for UNMATCHED transactions.

## Step 7 — Call the management command

```bash
docker compose exec web python manage.py stage_gmail_payments \
  --data '<JSON_ARRAY>' \
  [--dry-run]
```

Pass `--dry-run` if the user passed `--dry-run`.

## Step 8 — Report results

Show the command output, then a summary table:

| Status | Date | Amount | Party | Confidence |
|--------|------|--------|-------|------------|
| STAGED | 2026-05-09 | Rs.5,000 | Premco India | 85% |
| UNMATCHED | 2026-05-06 | Rs.8,500 | — | 42% |
| SKIPPED | 2026-05-05 | Rs.3,000 | — | dup |
| PARSE_ERROR | — | — | — | — |

End with: "Visit /governance/approvals/ to review and approve staged transactions."
