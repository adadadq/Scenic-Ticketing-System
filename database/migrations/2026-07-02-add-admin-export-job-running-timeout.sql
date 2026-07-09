CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_started_at
    ON admin_export_job (status, started_at);
