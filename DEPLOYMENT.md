# Deployment Guide

## Goal

Deploy the ERP on a client-managed machine using Docker, PostgreSQL, Gunicorn, and Caddy.

This package is intended for:

- Linux Docker hosts
- Windows Docker Desktop installations

## Production files

- `docker-compose.prod.yml`
- `.env.production`
- `Caddyfile`

## Linux deployment

1. Install Docker Engine and Docker Compose.
2. Copy the project folder to the target machine.
3. Create the production env file:

```bash
cp .env.production.example .env.production
```

4. Update:
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `ERP_SITE_ADDRESS`
- `POSTGRES_PASSWORD`

5. Start the production stack:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d
```

6. Create the owner admin user:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py createsuperuser
```

7. Bootstrap the default role groups:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py bootstrap_roles
```

## Windows deployment

1. Install Docker Desktop.
2. Open the project folder in PowerShell or Command Prompt.
3. Copy the env file:

```powershell
copy .env.production.example .env.production
```

4. Update the same production values as the Linux flow.
5. Start the stack:

```powershell
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d
```

6. Run `createsuperuser` and `bootstrap_roles` through `docker compose exec web ...`.

## Notes

- `web` runs migrations and static collection on startup.
- PostgreSQL data, backups, media, and static files are persisted through named volumes.
- Caddy proxies traffic to the Django app and serves `/static/` and `/media/`.
- For LAN-only usage, `ERP_SITE_ADDRESS=localhost` or a private host/IP is acceptable.
- For public access, point a domain to the machine and set `ERP_SITE_ADDRESS` accordingly.
