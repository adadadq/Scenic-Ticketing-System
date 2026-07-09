CREATE TABLE IF NOT EXISTS admin_export_job (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL,
    export_type VARCHAR(40) NOT NULL,
    file_format VARCHAR(10) NOT NULL,
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    request_id VARCHAR(64),
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 1,
    next_attempt_at TIMESTAMP,
    requested_by_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id),
    requested_by_username VARCHAR(64) NOT NULL,
    requested_by_display_name VARCHAR(100) NOT NULL,
    requested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    file_name VARCHAR(160),
    storage_key VARCHAR(255),
    error_code VARCHAR(64),
    error_message VARCHAR(200),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_admin_export_job_job_id UNIQUE (job_id),
    CONSTRAINT ck_admin_export_job_type CHECK (
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
    ),
    CONSTRAINT ck_admin_export_job_format CHECK (file_format IN ('CSV', 'XLSX')),
    CONSTRAINT ck_admin_export_job_status CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED')),
    CONSTRAINT ck_admin_export_job_retry_counts CHECK (retry_count >= 0 AND max_retries >= 0)
);

CREATE INDEX IF NOT EXISTS idx_admin_export_job_requested_at
    ON admin_export_job (requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_requested_at
    ON admin_export_job (status, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_next_attempt_requested_at
    ON admin_export_job (status, next_attempt_at, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_started_at
    ON admin_export_job (status, started_at);
CREATE INDEX IF NOT EXISTS idx_admin_export_job_type_requested_at
    ON admin_export_job (export_type, requested_at DESC);
