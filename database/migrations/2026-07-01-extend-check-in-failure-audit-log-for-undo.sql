-- Extend check-in failure audit log for undo check-in failures.
-- Safe to run more than once on PostgreSQL/openGauss-style databases.

BEGIN;

ALTER TABLE check_in_failure_audit_log
    DROP CONSTRAINT IF EXISTS ck_check_in_failure_audit_log_action;
ALTER TABLE check_in_failure_audit_log
    ADD CONSTRAINT ck_check_in_failure_audit_log_action
    CHECK (action IN ('CHECK_IN', 'UNDO_CHECK_IN'));

ALTER TABLE check_in_failure_audit_log
    DROP CONSTRAINT IF EXISTS ck_check_in_failure_audit_log_code;
ALTER TABLE check_in_failure_audit_log
    ADD CONSTRAINT ck_check_in_failure_audit_log_code
    CHECK (
        failure_code IN (
            'TICKET_NOT_FOUND',
            'TICKET_ALREADY_USED',
            'TICKET_NOT_CHECKABLE',
            'TICKET_NOT_CHECKED_IN',
            'TICKET_UNDO_NOT_ALLOWED'
        )
    );

COMMIT;
