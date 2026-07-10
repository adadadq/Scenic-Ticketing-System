---
name: scenic-deploy-verify
description: Use when deploying, redeploying, hotfixing, or checking the online Scenic Ticket project. Forces post-deploy smoke tests for frontend, backend, database, visitor/admin paths, admin login, settings save, ticket save, nginx/systemd logs, and openGauss compatibility so the project is not merely deployed but usable.
---

# Scenic Deploy Verify

Use this skill after every deployment or production hotfix of this project.

Goal: do not say "deployed" until the deployed site proves the core visitor and admin flows work.

## Known Production Shape

- Server: `root@47.251.109.13`
- Public domain: `http://scenic.ddx123.xyz/`
- App root: `/opt/scenic-ticket/current`
- Service: `scenic-ticket.service`
- Backend: FastAPI on `127.0.0.1:8000`
- Nginx serves frontend and proxies `/api/`
- DB: openGauss container `scenic-ticket-opengauss`
- App DB/user: `scenic_ticket` / `scenic_app_login`

Do not print passwords, cookies, session tokens, CSRF tokens, or DB passwords in the final answer.

## Deployment Gate

Before deployment:

1. Run the smallest relevant local checks for the changed area.
2. If backend code changed, run at least:
   - `python -m py_compile` for edited Python files.
   - targeted pytest for edited modules.
3. For release-level changes, run full backend tests and frontend build/contract tests when feasible.

After deployment, run all smoke checks below. If any required check fails, the deployment is not complete.

## Smoke Checks

### 1. Process And Routing

On the server:

```bash
systemctl is-active scenic-ticket.service
curl -fsS http://127.0.0.1:8000/api/health
curl -fsS http://127.0.0.1:8000/api/health/db
curl -fsSI -H 'Host: scenic.ddx123.xyz' http://127.0.0.1/
curl -fsS -H 'Host: scenic.ddx123.xyz' http://127.0.0.1/api/health/db
```

From local/public network:

```bash
curl --noproxy '*' -fsSI http://scenic.ddx123.xyz/
curl --noproxy '*' -fsS http://scenic.ddx123.xyz/api/health/db
```

### 2. Admin Login And Write APIs

Use a cookie jar and real admin session. Do not expose credentials in output.

Required checks:

1. `GET /api/auth/csrf` returns 200 and sets CSRF cookie.
2. `POST /api/admin/auth/login` returns 200.
3. `GET /api/admin/settings` returns 200.
4. `PATCH /api/admin/settings` returns 200 using a harmless current/same value, for example `{"perOrderLimit": <current value>}`.
5. `GET /api/admin/tickets` returns 200 and at least one ticket.
6. `PATCH /api/admin/tickets/{id}` returns 200 using the same values from the first ticket, so the check is non-destructive.

If login credentials are unknown, do not bypass auth. Ask the user or inspect seeded/demo credentials only if they are already part of the project and not secrets.

### 3. Visitor Sanity

Check at least:

```bash
curl -fsS http://127.0.0.1:8000/api/announcements/current
curl --noproxy '*' -fsSI 'http://scenic.ddx123.xyz/#/visitor/booking'
```

If a changed area touches booking/orders/payment, run a real visitor flow or the smallest existing smoke/e2e script that covers it.

### 4. openGauss Compatibility

This project runs on openGauss, not vanilla PostgreSQL. Before/after backend deployment:

```bash
rg -n "ON CONFLICT|pg_sequences|CREATE INDEX IF NOT EXISTS" backend/app database -S
```

Rules:

- Do not use `INSERT ... ON CONFLICT` in production write paths unless it has been verified against this openGauss version.
- Prefer `UPDATE ...; if rowcount == 0: INSERT ...` for admin write upserts.
- Do not rely on PostgreSQL-only catalog views such as `pg_sequences`.
- If schema is imported as `omm`, change table owner to `scenic_app_login` or verify the app user can create indexes, insert, update, and select.

Owner check:

```bash
printf "select tablename, tableowner from pg_tables where schemaname='public' order by tablename;\n" \
  | docker exec -i scenic-ticket-opengauss su - omm -c "gsql -d scenic_ticket"
```

Key tables for admin availability:

- `admin_system_setting`
- `admin_system_setting_audit_log`
- `ticket_type`
- `route_product`
- `time_slot_quota`
- `user_session`
- `admin_user`

### 5. Logs Must Be Clean After Smoke

After smoke tests:

```bash
journalctl -u scenic-ticket.service --since '<deploy restart time>' --no-pager
tail -n 80 /var/log/nginx/error.log
```

Required: no new stack traces or 500s for the smoke paths. Old pre-fix errors are okay if clearly before the deploy restart time.

## Final Report Format

Keep the final short:

- What was deployed or changed.
- Exact smoke evidence: status codes for health, frontend, admin settings, admin tickets.
- Any caveats, especially DNS/HTTPS/openGauss owner issues.
- Backup path if a hotfix replaced server files.

Never claim production readiness from `systemctl active` alone.
