ALTER TABLE IF EXISTS admin_export_job_alert_event
    ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS acknowledged_by_admin_user_id BIGINT REFERENCES admin_user(id),
    ADD COLUMN IF NOT EXISTS acknowledged_by_username VARCHAR(64),
    ADD COLUMN IF NOT EXISTS acknowledged_by_display_name VARCHAR(100),
    ADD COLUMN IF NOT EXISTS acknowledge_note VARCHAR(200);

CREATE INDEX IF NOT EXISTS idx_admin_export_job_alert_event_ack_created
    ON admin_export_job_alert_event (acknowledged_at, created_at DESC);
