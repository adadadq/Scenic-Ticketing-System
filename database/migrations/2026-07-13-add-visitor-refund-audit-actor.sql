BEGIN;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'refund_audit_log'
          AND column_name = 'operator_type'
    ) THEN
        ALTER TABLE refund_audit_log ADD COLUMN operator_type VARCHAR(20);
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'refund_audit_log'
          AND column_name = 'operator_visitor_id'
    ) THEN
        ALTER TABLE refund_audit_log
            ADD COLUMN operator_visitor_id BIGINT REFERENCES visitor(id);
    END IF;
END
$$;

UPDATE refund_audit_log SET operator_type = 'ADMIN' WHERE operator_type IS NULL;

ALTER TABLE refund_audit_log ALTER COLUMN operator_type SET NOT NULL;
ALTER TABLE refund_audit_log ALTER COLUMN operator_admin_user_id DROP NOT NULL;

ALTER TABLE refund_audit_log DROP CONSTRAINT IF EXISTS ck_refund_audit_log_operator_type;
ALTER TABLE refund_audit_log DROP CONSTRAINT IF EXISTS ck_refund_audit_log_operator;
ALTER TABLE refund_audit_log
    ADD CONSTRAINT ck_refund_audit_log_operator_type CHECK (operator_type IN ('ADMIN', 'VISITOR'));
ALTER TABLE refund_audit_log
    ADD CONSTRAINT ck_refund_audit_log_operator CHECK (
        (operator_type = 'ADMIN' AND operator_admin_user_id IS NOT NULL AND operator_visitor_id IS NULL)
        OR (operator_type = 'VISITOR' AND operator_admin_user_id IS NULL AND operator_visitor_id IS NOT NULL)
    );

CREATE INDEX IF NOT EXISTS idx_refund_audit_log_visitor_created
    ON refund_audit_log (operator_visitor_id, created_at DESC);

COMMIT;
