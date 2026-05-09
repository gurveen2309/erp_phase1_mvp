# Website Cover Plan: Public Marketing Homepage

## Context

Currently `/` is a staff-only Django view — no public presence exists. The project already has a
Next.js app (`dashboard/`) with Tailwind CSS. Rather than add a second frontend stack (Tailwind CDN
in Django templates), the better approach is to consolidate: **Next.js becomes the single
user-facing frontend** for both the public marketing page and the analytics dashboard. Django stays
as pure backend: API + admin. One frontend stack, no skeleton duplication.

---

## Architecture

```
Next.js (port 3000)
  /               → public marketing homepage (new)
  /dashboard      → analytics dashboard (existing page.tsx, moved here)

Django (port 8000)
  /admin/         → Django admin — staff data entry (unchanged)
  /reports/       → Django staff views (unchanged, staff-only)
  /imports/       → unchanged
  /governance/    → unchanged
  /reports/api/   → JSON API consumed by Next.js (unchanged)
```

**Auth flow:**
- Visitor lands on Next.js `/` → sees marketing page with "Back Office Login" button
- Button links directly to Django admin: `http://127.0.0.1:8000/admin/` (or the deployed domain)
- Staff log in via Django admin and work there for all data entry
- Staff visit Next.js `/dashboard` for analytics (already works — calls Django JSON API)
- No session sharing needed between Next.js and Django for the initial scope

---

## What the Marketing Page Contains

Content pulled from `next.config.ts` env vars (or hardcoded initially):

| Section | Content |
|---------|---------|
| **Nav** | Company name (left), "Back Office" login link (right, opens Django admin) |
| **Hero** | Company name, tagline, brief description of services |
| **What We Do** | 3–4 service cards: Heat Treatment, Surface Hardening, Quality Inspection, Production Tracking |
| **Why Choose Us** | GST registered, quality-focused, reliable, experienced |
| **Contact / Footer** | Address, GSTIN, city |

Company info (name, address, GSTIN) sourced from `NEXT_PUBLIC_COMPANY_*` env vars so it can be changed without touching code.

---

## Implementation Plan

### 1. Restructure Next.js routes

Current `dashboard/app/page.tsx` is the analytics dashboard. Move it:

```
dashboard/app/page.tsx          → dashboard/app/dashboard/page.tsx
dashboard/app/layout.tsx        → stays (root layout wraps both pages)
```

Create new `dashboard/app/page.tsx` as the public marketing homepage.

### 2. Add company env vars to dashboard

In `dashboard/.env.local` (and `.env.local.example`):

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/reports/api
NEXT_PUBLIC_COMPANY_NAME=Saini Enterprises
NEXT_PUBLIC_COMPANY_ADDRESS=2458, Sewak Pura, Kalsian Road, Ludhiana
NEXT_PUBLIC_COMPANY_GSTIN=03AKCPK1161E1ZW
NEXT_PUBLIC_ADMIN_URL=http://127.0.0.1:8000/admin/
```

### 3. Create `dashboard/app/page.tsx` (marketing homepage)

Public page — no API calls, no auth. Uses Tailwind (already installed). Sections:
- `<Navbar>` — company name + "Back Office" button linking to `NEXT_PUBLIC_ADMIN_URL`
- `<Hero>` — headline, subheading, CTA
- `<Services>` — 4 cards (can reuse Tailwind grid from existing dashboard)
- `<WhyUs>` — bullet highlights
- `<Footer>` — address, GSTIN

### 4. Move dashboard to `/dashboard`

`dashboard/app/dashboard/page.tsx` — exact copy of current `app/page.tsx`. No logic changes, just a path move.

Update any internal links (if any) from `/` to `/dashboard`.

### 5. Update `dashboard/next.config.ts`

No structural changes needed. Confirm `allowedDevOrigins` allows the port being used.

### 6. Django: no changes

The Django `/` route currently redirects unauthenticated users to `/admin/login/`. This is fine — staff who bookmark `/` on the Django port still land at login. The public-facing URL is the Next.js port (or the same domain via a reverse proxy at deploy time).

---

## Files to Create / Modify

| File | Action |
|------|--------|
| `dashboard/app/page.tsx` | Replace with marketing homepage |
| `dashboard/app/dashboard/page.tsx` | Create — move existing analytics page here |
| `dashboard/app/dashboard/` | Create directory |
| `dashboard/.env.local.example` | Update with `NEXT_PUBLIC_COMPANY_*` and `NEXT_PUBLIC_ADMIN_URL` |
| `dashboard/app/layout.tsx` | Minor — update title/metadata if needed |

**Nothing changes in Django.**

---

## What Does NOT Change

- Django `base.html`, all staff templates — untouched
- All `/reports/`, `/imports/`, `/governance/`, `/admin/` URLs — untouched
- Django JSON API endpoints — untouched
- Docker setup — untouched
- Playwright tests — untouched (they hit Django directly at port 8000)
- Tailwind config in `dashboard/` — already there, nothing to add

---

## Deployment Note (for later)

When deployed, put a reverse proxy (nginx / Caddy) in front:
- `yourdomain.com/` → Next.js (marketing + dashboard)
- `yourdomain.com/admin/` → Django admin
- `yourdomain.com/reports/api/` → Django API

Until then, dev workflow:
- `make run` starts Django on port 8000
- `cd dashboard && npm run dev` starts Next.js on port 3000
- Marketing homepage: `localhost:3000`
- Django admin (back office): `localhost:8000/admin/`

---

## Verification

1. `cd dashboard && npm run dev`
2. Visit `localhost:3000` → see marketing page (no login required)
3. Click "Back Office" → opens `localhost:8000/admin/` in browser
4. Visit `localhost:3000/dashboard` → see analytics dashboard (existing behavior)
5. `npm run build` in `dashboard/` → builds without errors
6. Existing Playwright tests at port 8000 → all pass (Django untouched)
