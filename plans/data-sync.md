# Data Sync Plan: DB ↔ CSV (Bidirectional)

## Context

The operator entered data via both Excel import and Django admin. The Excel workbook is now stale — the DB has moved ahead. The goal is a reproducible, git-friendly sync workflow so:
- Anyone can `git pull` + one command → get a fully-seeded local DB
- Any data added via admin can be pushed back to CSV files
- Any data updated in CSV files can be pulled back into DB
- Conflicts are flagged explicitly (never silently stomped)

Chosen approach: **CSV files in `data/` committed to git** (diffable, human-readable) as the canonical data interchange format. Two management commands — `export_data` (DB → CSV) and `import_data` (CSV → DB). No live/bidirectional auto-sync; the operator explicitly chooses which direction to push.

---

## CSV Format

One file per entity type. `erp_id` is the first column (DB primary key). All column names match `DEFAULT_MAPPINGS` in `migration_app/services.py` so the existing normalizers can be reused.

| File | Columns |
|------|---------|
| `data/parties.csv` | `erp_id, name, contact_person, phone, gst_number, address, is_active` |
| `data/invoices.csv` | `erp_id, party, invoice_number, invoice_date, amount, remarks` |
| `data/payments.csv` | `erp_id, party, payment_date, amount, mode, reference_number, remarks` |
| `data/challans.csv` | `erp_id, party, challan_number, challan_date, job_description, job_type, direction, weight_kg, amount, remarks` |
| `data/opening_balances.csv` | `erp_id, party, effective_date, balance_type, amount, remarks` |

---

## Natural Keys (for matching when erp_id is absent or stale)

| Entity | Primary natural key | Fallback |
|--------|-------------------|---------|
| Party | `name` | — |
| Invoice | `party + invoice_number` (if non-blank) | `party + invoice_date + amount` |
| Payment | `party + reference_number` (if non-blank) | `party + payment_date + amount` |
| Challan | `party + challan_number` (if non-blank) | `party + challan_date + amount` |
| OpeningBalance | `party + effective_date + balance_type + amount` | — |

---

## Row Classification

Each CSV row is classified into one of:
- **NEW** — no match in DB (by erp_id or natural key) → will be created
- **UNCHANGED** — matched, all field values identical → skipped
- **MODIFIED** — matched by erp_id, field values differ → will be updated (shows diff)
- **CONFLICT** — matched by natural key only (no erp_id or id mismatch), values differ → requires resolution
- **MISSING** — DB record exists but absent from CSV → warns only (requires `--delete-missing` to delete)

---

## Commands

### `export_data`

```
docker compose exec web python manage.py export_data [--output data/]
```

- Queries all 5 entity types from DB
- Writes each to its CSV file under `--output` (default: `data/`)
- Exports only active records (no soft-deleted, no internal fixture records unless explicitly included)
- Terminal output: counts per entity (e.g. "Parties: 21, Invoices: 367, ...")

### `import_data`

```
docker compose exec web python manage.py import_data [--input data/] [--dry-run] [--accept-csv] [--delete-missing]
```

- `--dry-run`: shows full report, nothing written
- `--accept-csv`: auto-resolves CONFLICT/MODIFIED by taking CSV values (no prompt)
- `--accept-db`: auto-skips CONFLICT/MODIFIED (DB wins, CSV rows ignored)
- `--delete-missing`: deletes DB records not present in CSV (default: warn only)
- Without `--dry-run`: shows report, prompts for confirmation on any CONFLICT rows, then commits atomically

Default interactive flow:
1. Parse all CSVs
2. Print report grouped by entity + row type
3. If CONFLICTs exist and no `--accept-*` flag: prompt per conflict (take CSV / keep DB / skip)
4. Print final plan (what will be created, updated, deleted)
5. Confirm (y/n)
6. Commit in a single `transaction.atomic()`

---

## Files to Create / Modify

### New files

| Path | Purpose |
|------|---------|
| `migration_app/management/commands/export_data.py` | `export_data` command |
| `migration_app/management/commands/import_data.py` | `import_data` command |
| `data/` | Directory for CSV data files (committed to git) |
| `data/README.md` | Workflow docs: how to export, import, resolve conflicts |

### Modified files

| Path | Change |
|------|--------|
| `Makefile` | Add `export-data`, `import-data-dry`, `import-data` targets |

### No changes needed

- `migration_app/services.py` — import `normalize_date`, `normalize_decimal`, `normalize_boolean` directly from here
- All model files — no schema changes

---

## Code Reuse from `migration_app/services.py`

```python
from migration_app.services import (
    normalize_date,       # handles %Y-%m-%d, %d-%m-%Y, %d/%m/%Y, %m/%d/%Y
    normalize_decimal,    # string → Decimal
    normalize_boolean,    # "0"/"false"/"no" → False, else True
)
```

The existing `detect_duplicate()` logic is adapted inline (not called directly) because we need the actual DB object back, not just a boolean.

The existing `_persist_row()` uses `get_or_create()` which silently skips — the new `import_data` needs the richer classification (NEW vs UNCHANGED vs MODIFIED), so it queries explicitly before deciding.

---

## Makefile Targets

```makefile
export-data:
	docker compose exec web python manage.py export_data

import-data-dry:
	docker compose exec web python manage.py import_data --dry-run

import-data:
	docker compose exec web python manage.py import_data
```

Standard workflow for "anyone getting latest data":
```
git pull
make import-data-dry   # review what will change
make import-data       # commit
```

Standard workflow for "pushing DB changes back to CSV":
```
make export-data
git add data/
git commit -m "sync: export latest DB state"
git push
```

---

## Conflict Example Output

```
INVOICES — 2 MODIFIED, 1 CONFLICT

  MODIFIED  erp_id=42  PW Test Party / PW-INV-001
    amount:  DB=5000.00  CSV=5200.00

  CONFLICT  no erp_id  PW Test Party / 2024-06-15 / 3000.00
    Matches DB record id=77 by natural key, but invoice_number differs.
    DB: invoice_number=""   CSV: invoice_number="BILL-099"

  Resolve CONFLICT id=77? [csv / db / skip]: 
```

---

## Deletion Safety

- `export_data` does NOT mark records as deleted in CSV. It simply omits them.
- `import_data` without `--delete-missing` prints: "WARNING: 3 DB records not found in CSV (parties: 0, invoices: 2, challans: 1). Run with --delete-missing to remove."
- `--delete-missing` only deletes records that have no FK dependents (respects `PROTECT` constraints — will show error and skip if dependencies exist).

---

## Verification

1. Run `make export-data` → check `data/*.csv` files exist with correct columns and row counts
2. Wipe the DB (or use a clean test DB), run `make import-data-dry` → verify row counts match export
3. Run `make import-data` → verify DB record counts match CSV
4. Manually change one invoice amount in `data/invoices.csv`, re-run `import-data-dry` → verify it shows as MODIFIED
5. Run `make export-data` again → verify MODIFIED record's new value is reflected in CSV
6. Add a new row in `data/parties.csv` with blank `erp_id`, run `import-data-dry` → verify it shows as NEW
7. Run existing Playwright tests to confirm no regressions
