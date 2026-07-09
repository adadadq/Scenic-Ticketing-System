# Database

This directory contains the SQL truth source for the Python backend rewrite.

## Files

- `schema.sql`: schema for visitor booking, simulated payment, server-side sessions, public catalog data, admin auth, check-in audit logs, check-in failure audit logs, and refund audit logs.
- `seed.sql`: small development seed data for local demos and API tests.
- `migrations/2026-07-01-add-check-in-failure-audit-log.sql`: idempotent migration for existing databases that need the check-in failure audit log table without recreating the schema.
- `migrations/2026-07-01-extend-check-in-failure-audit-log-for-undo.sql`: idempotent migration for existing databases that already have the check-in failure audit table and need undo failure codes.
- `migrations/2026-07-01-add-check-in-audit-log-reason.sql`: idempotent migration for existing databases that need successful undo check-in reasons in `check_in_audit_log`.

## Migration status

`schema.sql` is the first-stage rebuild baseline. It is safe for a freshly recreated local database.

If this schema is applied to an existing database with real `ticket_order_item` rows, write a separate migration first. For example, adding `ticket_order_item.product_id` requires an `ALTER TABLE`, backfilling from the current `ticket_type_id -> route_product` mapping, and only then adding the `NOT NULL` and composite foreign key constraints.

Existing databases that predate the check-in failure audit slice must run `migrations/2026-07-01-add-check-in-failure-audit-log.sql` before deploying the backend that reads or writes `check_in_failure_audit_log`. Existing databases that already have that table but predate undo failure auditing must then run `migrations/2026-07-01-extend-check-in-failure-audit-log-for-undo.sql` before deploying backend code that writes `UNDO_CHECK_IN` failure rows. Existing databases that predate undo reason auditing must run `migrations/2026-07-01-add-check-in-audit-log-reason.sql` before deploying backend code that inserts or reads `check_in_audit_log.reason`.

## Scope

The current schema intentionally covers:

- visitors
- scenic spots
- ticket types
- route products
- piers
- time slot quota
- ticket orders
- order items
- payment records
- admin users
- check-in audit logs
- check-in failure audit logs
- refund audit logs
- server-side sessions

Admin CRUD, real payment refunds, refund notifications, report snapshots, and broader operation logs are later phases.
