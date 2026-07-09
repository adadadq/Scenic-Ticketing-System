ALTER TABLE IF EXISTS admin_export_job_alert_event
    ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS closed_by_admin_user_id BIGINT REFERENCES admin_user(id),
    ADD COLUMN IF NOT EXISTS closed_by_username VARCHAR(64),
    ADD COLUMN IF NOT EXISTS closed_by_display_name VARCHAR(100),
    ADD COLUMN IF NOT EXISTS close_note VARCHAR(200);

CREATE INDEX IF NOT EXISTS idx_admin_export_job_alert_event_closed_created
    ON admin_export_job_alert_event (closed_at, created_at DESC);
