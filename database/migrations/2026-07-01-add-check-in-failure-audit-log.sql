-- Add check-in failure audit log table for existing databases.
-- Safe to run more than once on PostgreSQL/openGauss-style databases.

BEGIN;

CREATE TABLE IF NOT EXISTS check_in_failure_audit_log (
    id BIGSERIAL PRIMARY KEY,
    ticket_code VARCHAR(64) NOT NULL,
    action VARCHAR(20) NOT NULL,
    failure_code VARCHAR(40) NOT NULL,
    failure_message VARCHAR(100) NOT NULL,
    operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id),
    operator_username VARCHAR(64) NOT NULL,
    operator_display_name VARCHAR(100) NOT NULL,
    request_id VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_check_in_failure_audit_log_action CHECK (action IN ('CHECK_IN', 'UNDO_CHECK_IN')),
    CONSTRAINT ck_check_in_failure_audit_log_code CHECK (
        failure_code IN (
            'TICKET_NOT_FOUND',
            'TICKET_ALREADY_USED',
            'TICKET_NOT_CHECKABLE',
            'TICKET_NOT_CHECKED_IN',
            'TICKET_UNDO_NOT_ALLOWED'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_check_in_failure_audit_log_ticket_created
    ON check_in_failure_audit_log (ticket_code, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_check_in_failure_audit_log_code_created
    ON check_in_failure_audit_log (failure_code, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_check_in_failure_audit_log_created
    ON check_in_failure_audit_log (created_at DESC);

COMMIT;
