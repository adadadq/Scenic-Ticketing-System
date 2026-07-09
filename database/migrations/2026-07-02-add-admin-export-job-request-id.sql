ALTER TABLE admin_export_job
    ADD COLUMN IF NOT EXISTS request_id VARCHAR(64);
