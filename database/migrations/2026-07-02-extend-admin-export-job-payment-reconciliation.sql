ALTER TABLE admin_export_job
    DROP CONSTRAINT IF EXISTS ck_admin_export_job_type;

ALTER TABLE admin_export_job
    ADD CONSTRAINT ck_admin_export_job_type CHECK (
        export_type IN (
            'ORDER_DETAIL',
            'CHECK_IN_AUDIT',
            'CHECK_IN_FAILURE_AUDIT',
            'REFUND_AUDIT',
            'PAYMENT_RECONCILIATION',
            'PRODUCT_BREAKDOWN',
            'DAILY_TREND',
            'HOURLY_TREND',
            'MONTHLY_TREND'
        )
    );
