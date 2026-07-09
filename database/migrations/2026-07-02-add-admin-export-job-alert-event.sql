CREATE TABLE IF NOT EXISTS admin_export_job_alert_event (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES admin_export_job(job_id),
    export_type VARCHAR(40) NOT NULL,
    file_format VARCHAR(10) NOT NULL,
    error_code VARCHAR(64) NOT NULL,
    error_message VARCHAR(500) NOT NULL,
    alert_source VARCHAR(40) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_admin_export_job_alert_event_source CHECK (alert_source IN ('WORKER_FINAL_FAILURE'))
);

CREATE INDEX IF NOT EXISTS idx_admin_export_job_alert_event_job_created
    ON admin_export_job_alert_event (job_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_admin_export_job_alert_event_code_created
    ON admin_export_job_alert_event (error_code, created_at DESC);
