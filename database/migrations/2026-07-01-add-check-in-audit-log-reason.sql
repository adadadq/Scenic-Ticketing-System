-- Add optional undo check-in reason to successful check-in audit log rows.

ALTER TABLE check_in_audit_log
    ADD COLUMN IF NOT EXISTS reason VARCHAR(100);
