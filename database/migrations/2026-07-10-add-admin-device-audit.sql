ALTER TABLE admin_system_setting_audit_log ADD COLUMN device_id VARCHAR(32);
ALTER TABLE admin_system_setting_audit_log ADD COLUMN admin_session_id BIGINT;
ALTER TABLE admin_system_setting_audit_log ADD COLUMN user_agent VARCHAR(512);

ALTER TABLE check_in_audit_log ADD COLUMN source_ip VARCHAR(64);
ALTER TABLE check_in_audit_log ADD COLUMN device_id VARCHAR(32);
ALTER TABLE check_in_audit_log ADD COLUMN admin_session_id BIGINT;
ALTER TABLE check_in_audit_log ADD COLUMN user_agent VARCHAR(512);

ALTER TABLE check_in_failure_audit_log ADD COLUMN source_ip VARCHAR(64);
ALTER TABLE check_in_failure_audit_log ADD COLUMN device_id VARCHAR(32);
ALTER TABLE check_in_failure_audit_log ADD COLUMN admin_session_id BIGINT;
ALTER TABLE check_in_failure_audit_log ADD COLUMN user_agent VARCHAR(512);

ALTER TABLE refund_audit_log ADD COLUMN source_ip VARCHAR(64);
ALTER TABLE refund_audit_log ADD COLUMN device_id VARCHAR(32);
ALTER TABLE refund_audit_log ADD COLUMN admin_session_id BIGINT;
ALTER TABLE refund_audit_log ADD COLUMN user_agent VARCHAR(512);

CREATE TABLE admin_ticket_audit_log (
    id BIGSERIAL PRIMARY KEY,
    ticket_type_id BIGINT NOT NULL,
    ticket_name VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL,
    operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id),
    operator_username VARCHAR(64) NOT NULL,
    operator_display_name VARCHAR(100) NOT NULL,
    request_id VARCHAR(64),
    source_ip VARCHAR(64),
    device_id VARCHAR(32),
    admin_session_id BIGINT,
    user_agent VARCHAR(512),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_admin_ticket_audit_log_action CHECK (action IN ('CREATE', 'UPDATE', 'DELETE'))
);

CREATE INDEX idx_admin_ticket_audit_log_created ON admin_ticket_audit_log (created_at DESC);
