# Operations Guide

## Role setup

After initial deployment:

1. Create users in Django admin.
2. Set `is_staff=True` for users who should access admin and governance pages.
3. Assign one of these groups:
- `OwnerAdmin`
- `Accountant`
- `Operator`
- `Viewer`

Run once to create/update groups:

```bash
python manage.py bootstrap_roles
```

## Backups

### Create from UI

- Open `/governance/backups/`
- Enter optional notes
- Click `Create Backup`

### Create from command line

```bash
python manage.py create_backup --notes "manual backup"
```

## Restore

- Only the owner/admin should run restore.
- Open `/governance/backups/`
- Choose a snapshot and confirm restore
- The system creates a pre-restore backup automatically
- Unsafe writes are blocked during restore with a maintenance lock file

Command line restore:

```bash
python manage.py restore_backup <snapshot_id> --notes "restore reason"
```

## Imports

### Normal import flow

1. Open `/imports/`
2. Upload file and preview it
3. If you are the owner/admin, confirm to commit directly
4. If you are not the owner/admin, confirm to submit an approval request

### Rollback imported batch

1. Open `/imports/history/`
2. Choose `Rollback` on the batch
3. Confirm rollback

Rollback is owner-only and removes imported rows tied to that batch in dependency-safe order.

## Approval queue

- Open `/governance/approvals/`
- Review pending finance and import requests
- Approve or reject from the detail page

## Party statement PDF

- Open `/reports/ledger/`
- Select the party and date range
- Click `Load Ledger`
- Click `Download PDF Statement`
- The exported PDF uses the configured company header and the selected party/date range

## Audit log

- Open `/governance/audit/`
- Review recent finance, import, backup, and restore events

## Upgrades

For application updates:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d
```

If model changes are included:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py migrate
```
