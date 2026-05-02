# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dev Commands

All commands assume Docker is running. The `web` container runs Django; `postgres` runs the DB.

```bash
make build          # docker compose up -d --build
make run            # docker compose up -d (no rebuild)
make stop           # docker compose down

make mm APP=<app>   # makemigrations for a specific app
make m              # migrate
make revert APP=<app> TARGET=<migration>  # revert to a specific migration

# Arbitrary management commands:
docker compose exec web python manage.py <cmd>

# Run Django tests:
docker compose exec web python manage.py test

# Run Playwright UI tests (always headed, 1 s slowMo so actions are clearly visible):
cd tests && npm test

# Seed default role groups (once, after first migrate):
docker compose exec web python manage.py bootstrap_roles
```

SQLite is used if `USE_POSTGRES` is not set in `.env`. The `.env` file also controls `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, and company branding (`ERP_COMPANY_NAME`, `ERP_COMPANY_ADDRESS`, `ERP_COMPANY_GSTIN`) used in PDF headers.

## Architecture

Six Django apps, no Celery/Redis — everything is synchronous.

| App | Models | Purpose |
|-----|--------|---------|
| `masters` | `Party` | Core reference entity: customers and suppliers |
| `production` | `Challan` (Direction: IN/OUT) | Production/delivery notes |
| `finance` | `OpeningBalance`, `Invoice`, `Payment` | Ledger entries; all extend `ImportedModelMixin` |
| `reporting` | — | Views only: ledger, outstanding summary, production dashboard, PDF exports |
| `migration_app` | `MigrationBatch`, `MigrationRowError`, `MigrationMappingProfile` | Excel import pipeline with per-batch rollback |
| `governance` | `ApprovalRequest`, `BackupSnapshot`, `AuditEvent` | Approval queue, DB backups, audit trail |

**URL map:**
- `/` and `/reports/` → reporting views (ledger, outstanding, production dashboard, receipts, blank templates)
- `/admin/` → Django admin
- `/imports/` → Excel import pipeline
- `/governance/` → approvals, audit log, backups

## Key Patterns

**`ImportedModelMixin`** (`finance/models.py`) — abstract base class that links `OpeningBalance`, `Invoice`, and `Payment` records to their source `MigrationBatch`. This is what enables batch rollback in `migration_app`.

**PDF generation** — two libraries in use:
- `reportlab`: programmatic PDF construction (receipts, ledger statements)
- `weasyprint`: HTML→PDF rendering (process/inspection templates)

PDF logic lives in `reporting/pdf_exports.py`.

**Excel import pipeline** (`migration_app`) — `openpyxl` parses uploaded `.xlsx` files. Each import creates a `MigrationBatch`; row errors go to `MigrationRowError`. A batch rollback deletes all finance records linked to that batch via `ImportedModelMixin`.
