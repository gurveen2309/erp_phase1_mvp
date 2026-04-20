# ERP Phase 1 MVP

Laptop-first Django ERP MVP for party ledgers, challans, invoices, payments, reporting, and recurring Excel imports.

## Docker + PostgreSQL startup

Run these commands from `/Users/gsingh/Downloads/erp_phase1_mvp`.

1. Create the local environment file:

```bash
cp .env.example .env
```

2. Keep PostgreSQL enabled in `.env`:
- `USE_POSTGRES=1`
- `POSTGRES_DB=erp_phase1`
- `POSTGRES_USER=erp`
- `POSTGRES_PASSWORD=erp`
- `POSTGRES_HOST=postgres`
- `POSTGRES_PORT=5432`
- `POSTGRES_EXPOSE_PORT=5432`

3. Build and start the containers:

```bash
docker compose up --build
```

4. In a second terminal, create the database tables:

```bash
docker compose exec web python manage.py migrate
```

5. Create the admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

6. Bootstrap the default roles:

```bash
docker compose exec web python manage.py bootstrap_roles
```

7. Open the app:
- Admin: `http://127.0.0.1:8000/admin/`
- Reports: `http://127.0.0.1:8000/reports/ledger/`
- Imports: `http://127.0.0.1:8000/imports/`

8. To stop the stack:

```bash
docker compose down
```

## Notes

- This project is already configured so the `web` container talks to the `postgres` container through Docker Compose.
- PostgreSQL is also exposed to your Mac on `localhost:${POSTGRES_EXPOSE_PORT}` for tools like DBeaver.
- You only need to run `docker compose exec web python manage.py migrate` again when model changes introduce new migrations.
- Uploaded import files and PostgreSQL data remain available between restarts unless you remove the Docker volume.
- Run `docker compose exec web python manage.py bootstrap_roles` after first setup so the default role groups are available in admin.

## DBeaver connection

1. Start the stack with `docker compose up --build`.
2. Open DBeaver and create a new PostgreSQL connection.
3. Use these values:
- Host: `localhost`
- Port: `5432`
- Database: `erp_phase1`
- Username: `erp`
- Password: `erp`
4. Click `Test Connection`, then save.
5. Open the `public` schema to browse tables such as `masters_party`, `production_challan`, `finance_invoice`, `finance_payment`, and `migration_app_migrationbatch`.

If `5432` is already used on your machine, change `POSTGRES_EXPOSE_PORT` in `.env`, restart `docker compose`, and use that port in DBeaver instead.

## Key URLs

- `/admin/`
- `/reports/ledger/`
- `/reports/outstanding/`
- `/reports/production/`
- `/imports/`
- `/imports/history/`
- `/governance/approvals/`
- `/governance/audit/`
- `/governance/backups/`
