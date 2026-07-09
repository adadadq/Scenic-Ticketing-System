ALTER TABLE admin_export_job
    ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_next_attempt_requested_at
    ON admin_export_job (status, next_attempt_at, requested_at DESC);
