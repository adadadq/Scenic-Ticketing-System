CREATE TABLE IF NOT EXISTS admin_system_setting (
    setting_key VARCHAR(64) PRIMARY KEY,
    setting_value VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_system_setting_audit_log (
    id BIGSERIAL PRIMARY KEY,
    changed_keys TEXT NOT NULL,
    action VARCHAR(255) NOT NULL,
    operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id),
    operator_username VARCHAR(64) NOT NULL,
    operator_display_name VARCHAR(100) NOT NULL,
    request_id VARCHAR(64),
    source_ip VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_system_setting_audit_log_created
    ON admin_system_setting_audit_log (created_at DESC);

INSERT INTO admin_system_setting (setting_key, setting_value)
VALUES
    ('scenic_name', '遇龙河景区'),
    ('service_time_start', '08:30'),
    ('service_time_end', '18:00'),
    ('ticket_time_start', '08:30'),
    ('ticket_time_end', '16:30'),
    ('check_in_time_start', '09:00'),
    ('check_in_time_end', '17:30'),
    ('per_order_limit', '10'),
    ('session_ttl_minutes', '30'),
    ('csrf_enabled', 'true'),
    ('login_guard_enabled', 'true'),
    ('sms_enabled', 'true'),
    ('mail_enabled', 'true'),
    ('refund_enabled', 'true'),
    ('stock_enabled', 'true'),
    ('audit_retention_days', '90'),
    ('last_backup_label', '今天 02:30')
ON CONFLICT (setting_key) DO NOTHING;
