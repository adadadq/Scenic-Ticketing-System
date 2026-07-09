ALTER TABLE admin_export_job
    ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE admin_export_job
    ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 1;

ALTER TABLE admin_export_job
    DROP CONSTRAINT IF EXISTS ck_admin_export_job_retry_counts;

ALTER TABLE admin_export_job
    ADD CONSTRAINT ck_admin_export_job_retry_counts CHECK (retry_count >= 0 AND max_retries >= 0);
