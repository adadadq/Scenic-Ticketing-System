ALTER TABLE IF EXISTS admin_export_job
    ALTER COLUMN error_code TYPE VARCHAR(80),
    ALTER COLUMN error_message TYPE VARCHAR(500);

ALTER TABLE IF EXISTS admin_export_job_alert_event
    ALTER COLUMN error_code TYPE VARCHAR(80);
