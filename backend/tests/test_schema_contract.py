from pathlib import Path


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "database" / "schema.sql"
SEED_PATH = Path(__file__).resolve().parents[2] / "database" / "seed.sql"
CHECK_IN_FAILURE_AUDIT_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-01-add-check-in-failure-audit-log.sql"
)
UNDO_CHECK_IN_FAILURE_AUDIT_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-01-extend-check-in-failure-audit-log-for-undo.sql"
)
CHECK_IN_AUDIT_REASON_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-01-add-check-in-audit-log-reason.sql"
)
ADMIN_EXPORT_JOB_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-01-add-admin-export-job.sql"
)
ADMIN_EXPORT_JOB_REQUEST_ID_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-add-admin-export-job-request-id.sql"
)
ADMIN_EXPORT_JOB_PAYMENT_RECONCILIATION_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-extend-admin-export-job-payment-reconciliation.sql"
)
ADMIN_EXPORT_JOB_AUTO_RETRY_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-add-admin-export-job-auto-retry.sql"
)
ADMIN_EXPORT_JOB_RETRY_BACKOFF_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-add-admin-export-job-retry-backoff.sql"
)
ADMIN_EXPORT_JOB_RUNNING_TIMEOUT_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-add-admin-export-job-running-timeout.sql"
)
ADMIN_EXPORT_JOB_ALERT_EVENT_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-add-admin-export-job-alert-event.sql"
)
ADMIN_EXPORT_JOB_ERROR_FIELD_LENGTHS_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-align-admin-export-job-error-field-lengths.sql"
)
ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-add-admin-export-job-alert-event-acknowledgement.sql"
)
ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-add-admin-export-job-alert-event-close.sql"
)
ADMIN_EXPORT_JOB_ALERT_EVENT_DEDUPE_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "database"
    / "migrations"
    / "2026-07-02-add-admin-export-job-alert-event-dedupe.sql"
)


def load_schema() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def load_seed() -> str:
    return SEED_PATH.read_text(encoding="utf-8")


def load_check_in_failure_audit_migration() -> str:
    return CHECK_IN_FAILURE_AUDIT_MIGRATION_PATH.read_text(encoding="utf-8")


def load_undo_check_in_failure_audit_migration() -> str:
    return UNDO_CHECK_IN_FAILURE_AUDIT_MIGRATION_PATH.read_text(encoding="utf-8")


def load_check_in_audit_reason_migration() -> str:
    return CHECK_IN_AUDIT_REASON_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_migration() -> str:
    return ADMIN_EXPORT_JOB_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_request_id_migration() -> str:
    return ADMIN_EXPORT_JOB_REQUEST_ID_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_payment_reconciliation_migration() -> str:
    return ADMIN_EXPORT_JOB_PAYMENT_RECONCILIATION_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_auto_retry_migration() -> str:
    return ADMIN_EXPORT_JOB_AUTO_RETRY_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_retry_backoff_migration() -> str:
    return ADMIN_EXPORT_JOB_RETRY_BACKOFF_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_running_timeout_migration() -> str:
    return ADMIN_EXPORT_JOB_RUNNING_TIMEOUT_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_alert_event_migration() -> str:
    return ADMIN_EXPORT_JOB_ALERT_EVENT_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_error_field_lengths_migration() -> str:
    return ADMIN_EXPORT_JOB_ERROR_FIELD_LENGTHS_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_alert_event_ack_migration() -> str:
    return ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_alert_event_close_migration() -> str:
    return ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_MIGRATION_PATH.read_text(encoding="utf-8")


def load_admin_export_job_alert_event_dedupe_migration() -> str:
    return ADMIN_EXPORT_JOB_ALERT_EVENT_DEDUPE_MIGRATION_PATH.read_text(encoding="utf-8")


def test_schema_contains_mvp_tables():
    schema = load_schema()

    for table_name in [
        "scenic_spot",
        "visitor",
        "ticket_type",
        "pier",
        "route_product",
        "time_slot_quota",
        "ticket_order",
        "ticket_order_item",
        "payment_record",
        "refund_audit_log",
        "check_in_audit_log",
        "check_in_failure_audit_log",
        "admin_export_job",
        "admin_export_job_alert_event",
        "admin_system_setting",
        "admin_system_setting_audit_log",
        "admin_user",
        "user_session",
    ]:
        assert f"CREATE TABLE {table_name}" in schema


def test_schema_contains_order_ownership_and_payment_idempotency():
    schema = load_schema()

    assert "visitor_id BIGINT NOT NULL REFERENCES visitor(id)" in schema
    assert "product_id BIGINT NOT NULL" in schema
    assert "idx_ticket_order_item_product_id ON ticket_order_item (product_id)" in schema
    assert "uq_route_product_id_ticket_type UNIQUE (id, ticket_type_id)" in schema
    assert "fk_ticket_order_item_product_match FOREIGN KEY (product_id, ticket_type_id)" in schema
    assert "REFERENCES route_product(id, ticket_type_id)" in schema
    assert "PENDING_PAYMENT" in schema
    assert "idempotency_key VARCHAR(128) NOT NULL" in schema
    assert "uk_payment_record_order_idempotency UNIQUE (order_id, idempotency_key)" in schema
    assert "uq_payment_record_mockpay_event_idempotency" in schema
    assert "WHERE idempotency_key LIKE 'mockpay:%'" in schema


def test_schema_contains_session_security_fields():
    schema = load_schema()

    assert "session_token_hash VARCHAR(128) NOT NULL" in schema
    assert "csrf_token_hash VARCHAR(128) NOT NULL" in schema
    assert "expires_at TIMESTAMP NOT NULL" in schema
    assert "revoked_at TIMESTAMP" in schema
    assert "account_type VARCHAR(20) NOT NULL" in schema
    assert "visitor_id BIGINT REFERENCES visitor(id)" in schema
    assert "admin_user_id BIGINT REFERENCES admin_user(id)" in schema


def test_schema_contains_admin_user_authentication_baseline():
    schema = load_schema()

    assert "CREATE TABLE admin_user" in schema
    assert "username VARCHAR(64) NOT NULL" in schema
    assert "password_hash VARCHAR(255) NOT NULL" in schema
    assert "CONSTRAINT uk_admin_user_username UNIQUE (username)" in schema
    assert "CONSTRAINT ck_admin_user_role CHECK (role IN ('SUPER_ADMIN', 'OPERATOR'))" in schema
    assert "CONSTRAINT ck_admin_user_status CHECK (status IN ('ENABLED', 'DISABLED'))" in schema
    assert "idx_admin_user_status ON admin_user (status)" in schema
    assert "idx_user_session_admin ON user_session (admin_user_id)" in schema


def test_schema_contains_refund_audit_log_baseline():
    schema = load_schema()

    assert "CREATE TABLE refund_audit_log" in schema
    assert schema.index("CREATE TABLE admin_user") < schema.index("CREATE TABLE refund_audit_log")
    assert "order_id BIGINT NOT NULL REFERENCES ticket_order(id)" in schema
    assert "operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id)" in schema
    assert "refunded_item_nos JSONB NOT NULL" in schema
    assert "CONSTRAINT ck_refund_audit_log_type CHECK (refund_type IN ('FULL', 'PARTIAL'))" in schema
    assert "idx_refund_audit_log_order_created ON refund_audit_log (order_id, created_at DESC)" in schema
    assert "idx_refund_audit_log_created ON refund_audit_log (created_at DESC)" in schema


def test_schema_contains_check_in_audit_log_baseline():
    schema = load_schema()

    assert "CREATE TABLE check_in_audit_log" in schema
    assert schema.index("CREATE TABLE admin_user") < schema.index("CREATE TABLE check_in_audit_log")
    assert "order_id BIGINT NOT NULL REFERENCES ticket_order(id)" in schema
    assert "order_item_id BIGINT NOT NULL" in schema
    assert "reason VARCHAR(100)" in schema
    assert "operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id)" in schema
    assert "CONSTRAINT fk_check_in_audit_log_order_item FOREIGN KEY (order_id, order_item_id)" in schema
    assert "REFERENCES ticket_order_item(order_id, id)" in schema
    assert "CONSTRAINT ck_check_in_audit_log_action CHECK (action IN ('CHECK_IN', 'UNDO_CHECK_IN'))" in schema
    assert "idx_check_in_audit_log_ticket_created ON check_in_audit_log (ticket_code, created_at DESC)" in schema
    assert "idx_check_in_audit_log_order_created ON check_in_audit_log (order_id, created_at DESC)" in schema
    assert "idx_check_in_audit_log_created ON check_in_audit_log (created_at DESC)" in schema


def test_schema_contains_check_in_failure_audit_log_baseline():
    schema = load_schema()

    assert "CREATE TABLE check_in_failure_audit_log" in schema
    assert schema.index("CREATE TABLE admin_user") < schema.index("CREATE TABLE check_in_failure_audit_log")
    assert "ticket_code VARCHAR(64) NOT NULL" in schema
    assert "failure_code VARCHAR(40) NOT NULL" in schema
    assert "failure_message VARCHAR(100) NOT NULL" in schema
    assert "operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id)" in schema
    assert "CONSTRAINT ck_check_in_failure_audit_log_action CHECK (action IN ('CHECK_IN', 'UNDO_CHECK_IN'))" in schema
    assert (
        "'TICKET_NOT_FOUND',\n            'TICKET_ALREADY_USED',\n            'TICKET_NOT_CHECKABLE',\n"
        "            'TICKET_NOT_CHECKED_IN',\n            'TICKET_UNDO_NOT_ALLOWED'"
        in schema
    )
    assert "idx_check_in_failure_audit_log_ticket_created" in schema
    assert "idx_check_in_failure_audit_log_code_created" in schema
    assert "idx_check_in_failure_audit_log_created ON check_in_failure_audit_log (created_at DESC)" in schema


def test_schema_contains_admin_export_job_baseline():
    schema = load_schema()

    assert "CREATE TABLE admin_export_job" in schema
    assert schema.index("CREATE TABLE admin_user") < schema.index("CREATE TABLE admin_export_job")
    assert "job_id VARCHAR(36) NOT NULL" in schema
    assert "filters JSONB NOT NULL DEFAULT '{}'::jsonb" in schema
    assert "request_id VARCHAR(64)" in schema
    assert "retry_count INTEGER NOT NULL DEFAULT 0" in schema
    assert "max_retries INTEGER NOT NULL DEFAULT 1" in schema
    assert "next_attempt_at TIMESTAMP" in schema
    assert "error_code VARCHAR(80)" in schema
    assert "error_message VARCHAR(500)" in schema
    assert "requested_by_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id)" in schema
    assert "CONSTRAINT uk_admin_export_job_job_id UNIQUE (job_id)" in schema
    assert "CONSTRAINT ck_admin_export_job_type CHECK" in schema
    assert "'ORDER_DETAIL'" in schema
    assert "'CHECK_IN_AUDIT'" in schema
    assert "'CHECK_IN_FAILURE_AUDIT'" in schema
    assert "'REFUND_AUDIT'" in schema
    assert "'PAYMENT_RECONCILIATION'" in schema
    assert "'PRODUCT_BREAKDOWN'" in schema
    assert "'DAILY_TREND'" in schema
    assert "'HOURLY_TREND'" in schema
    assert "'MONTHLY_TREND'" in schema
    assert "CONSTRAINT ck_admin_export_job_format CHECK (file_format IN ('CSV', 'XLSX'))" in schema
    assert "CONSTRAINT ck_admin_export_job_status CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED'))" in schema
    assert "CONSTRAINT ck_admin_export_job_retry_counts CHECK (retry_count >= 0 AND max_retries >= 0)" in schema
    assert "idx_admin_export_job_requested_at ON admin_export_job (requested_at DESC)" in schema
    assert "idx_admin_export_job_status_requested_at ON admin_export_job (status, requested_at DESC)" in schema
    assert "idx_admin_export_job_status_next_attempt_requested_at" in schema
    assert "ON admin_export_job (status, next_attempt_at, requested_at DESC)" in schema
    assert "idx_admin_export_job_status_started_at ON admin_export_job (status, started_at)" in schema
    assert "idx_admin_export_job_type_requested_at ON admin_export_job (export_type, requested_at DESC)" in schema


def test_schema_contains_admin_export_job_alert_event_baseline():
    schema = load_schema()

    assert "CREATE TABLE admin_export_job_alert_event" in schema
    assert schema.index("CREATE TABLE admin_export_job") < schema.index(
        "CREATE TABLE admin_export_job_alert_event"
    )
    assert "job_id VARCHAR(36) NOT NULL REFERENCES admin_export_job(job_id)" in schema
    assert "export_type VARCHAR(40) NOT NULL" in schema
    assert "file_format VARCHAR(10) NOT NULL" in schema
    assert "error_code VARCHAR(80) NOT NULL" in schema
    assert "error_message VARCHAR(500) NOT NULL" in schema
    assert "alert_source VARCHAR(40) NOT NULL" in schema
    assert "acknowledged_at TIMESTAMP" in schema
    assert "acknowledged_by_admin_user_id BIGINT REFERENCES admin_user(id)" in schema
    assert "acknowledged_by_username VARCHAR(64)" in schema
    assert "acknowledged_by_display_name VARCHAR(100)" in schema
    assert "acknowledge_note VARCHAR(200)" in schema
    assert "closed_at TIMESTAMP" in schema
    assert "closed_by_admin_user_id BIGINT REFERENCES admin_user(id)" in schema
    assert "closed_by_username VARCHAR(64)" in schema
    assert "closed_by_display_name VARCHAR(100)" in schema
    assert "close_note VARCHAR(200)" in schema
    assert "occurrence_count INTEGER NOT NULL DEFAULT 1" in schema
    assert "last_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP" in schema
    assert "CONSTRAINT ck_admin_export_job_alert_event_occurrence_count CHECK" in schema
    assert "CONSTRAINT ck_admin_export_job_alert_event_source CHECK" in schema
    assert "'WORKER_FINAL_FAILURE'" in schema
    assert "idx_admin_export_job_alert_event_job_created" in schema
    assert "ON admin_export_job_alert_event (job_id, created_at DESC)" in schema
    assert "idx_admin_export_job_alert_event_code_created" in schema
    assert "ON admin_export_job_alert_event (error_code, created_at DESC)" in schema
    assert "idx_admin_export_job_alert_event_ack_created" in schema
    assert "ON admin_export_job_alert_event (acknowledged_at, created_at DESC)" in schema
    assert "idx_admin_export_job_alert_event_closed_created" in schema
    assert "ON admin_export_job_alert_event (closed_at, created_at DESC)" in schema
    assert "CREATE UNIQUE INDEX uk_admin_export_job_alert_event_open_dedupe" in schema
    assert "ON admin_export_job_alert_event (job_id, error_code, alert_source)" in schema
    assert "WHERE closed_at IS NULL" in schema


def test_check_in_failure_audit_log_migration_supports_existing_databases():
    migration = load_check_in_failure_audit_migration()

    assert "CREATE TABLE IF NOT EXISTS check_in_failure_audit_log" in migration
    assert "operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id)" in migration
    assert "CONSTRAINT ck_check_in_failure_audit_log_action CHECK (action IN ('CHECK_IN', 'UNDO_CHECK_IN'))" in migration
    assert (
        "'TICKET_NOT_FOUND',\n            'TICKET_ALREADY_USED',\n            'TICKET_NOT_CHECKABLE',\n"
        "            'TICKET_NOT_CHECKED_IN',\n            'TICKET_UNDO_NOT_ALLOWED'"
        in migration
    )
    assert "CREATE INDEX IF NOT EXISTS idx_check_in_failure_audit_log_ticket_created" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_check_in_failure_audit_log_code_created" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_check_in_failure_audit_log_created" in migration


def test_undo_check_in_failure_audit_log_migration_extends_existing_constraints():
    migration = load_undo_check_in_failure_audit_migration()

    assert "ALTER TABLE check_in_failure_audit_log" in migration
    assert "DROP CONSTRAINT IF EXISTS ck_check_in_failure_audit_log_action" in migration
    assert "DROP CONSTRAINT IF EXISTS ck_check_in_failure_audit_log_code" in migration
    assert "CHECK (action IN ('CHECK_IN', 'UNDO_CHECK_IN'))" in migration
    assert (
        "'TICKET_NOT_FOUND',\n            'TICKET_ALREADY_USED',\n            'TICKET_NOT_CHECKABLE',\n"
        "            'TICKET_NOT_CHECKED_IN',\n            'TICKET_UNDO_NOT_ALLOWED'"
        in migration
    )


def test_check_in_audit_log_reason_migration_supports_existing_databases():
    migration = load_check_in_audit_reason_migration()

    assert "ALTER TABLE check_in_audit_log" in migration
    assert "ADD COLUMN IF NOT EXISTS reason VARCHAR(100)" in migration


def test_admin_export_job_migration_supports_existing_databases():
    migration = load_admin_export_job_migration()

    assert "CREATE TABLE IF NOT EXISTS admin_export_job" in migration
    assert "requested_by_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id)" in migration
    assert "filters JSONB NOT NULL DEFAULT '{}'::jsonb" in migration
    assert "retry_count INTEGER NOT NULL DEFAULT 0" in migration
    assert "max_retries INTEGER NOT NULL DEFAULT 1" in migration
    assert "next_attempt_at TIMESTAMP" in migration
    assert "CONSTRAINT ck_admin_export_job_type CHECK" in migration
    assert "'PAYMENT_RECONCILIATION'" in migration
    assert "CONSTRAINT ck_admin_export_job_format CHECK (file_format IN ('CSV', 'XLSX'))" in migration
    assert "CONSTRAINT ck_admin_export_job_status CHECK (status IN ('PENDING', 'RUNNING', 'SUCCEEDED', 'FAILED'))" in migration
    assert "CONSTRAINT ck_admin_export_job_retry_counts CHECK (retry_count >= 0 AND max_retries >= 0)" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_requested_at" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_requested_at" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_next_attempt_requested_at" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_started_at" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_type_requested_at" in migration


def test_admin_export_job_request_id_migration_supports_existing_databases():
    migration = load_admin_export_job_request_id_migration()

    assert "ALTER TABLE admin_export_job" in migration
    assert "ADD COLUMN IF NOT EXISTS request_id VARCHAR(64)" in migration


def test_admin_export_job_payment_reconciliation_migration_extends_existing_type_constraint():
    migration = load_admin_export_job_payment_reconciliation_migration()

    assert "ALTER TABLE admin_export_job" in migration
    assert "DROP CONSTRAINT IF EXISTS ck_admin_export_job_type" in migration
    assert "ADD CONSTRAINT ck_admin_export_job_type CHECK" in migration
    assert "'PAYMENT_RECONCILIATION'" in migration


def test_admin_export_job_auto_retry_migration_supports_existing_databases():
    migration = load_admin_export_job_auto_retry_migration()

    assert "ALTER TABLE admin_export_job" in migration
    assert "ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0" in migration
    assert "ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 1" in migration
    assert "DROP CONSTRAINT IF EXISTS ck_admin_export_job_retry_counts" in migration
    assert "ADD CONSTRAINT ck_admin_export_job_retry_counts CHECK" in migration


def test_admin_export_job_retry_backoff_migration_supports_existing_databases():
    migration = load_admin_export_job_retry_backoff_migration()

    assert "ALTER TABLE admin_export_job" in migration
    assert "ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMP" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_next_attempt_requested_at" in migration
    assert "ON admin_export_job (status, next_attempt_at, requested_at DESC)" in migration


def test_admin_export_job_running_timeout_migration_supports_existing_databases():
    migration = load_admin_export_job_running_timeout_migration()

    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_status_started_at" in migration
    assert "ON admin_export_job (status, started_at)" in migration


def test_admin_export_job_alert_event_migration_supports_existing_databases():
    migration = load_admin_export_job_alert_event_migration()

    assert "CREATE TABLE IF NOT EXISTS admin_export_job_alert_event" in migration
    assert "job_id VARCHAR(36) NOT NULL REFERENCES admin_export_job(job_id)" in migration
    assert "error_message VARCHAR(500) NOT NULL" in migration
    assert "CONSTRAINT ck_admin_export_job_alert_event_source CHECK" in migration
    assert "'WORKER_FINAL_FAILURE'" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_alert_event_job_created" in migration
    assert "ON admin_export_job_alert_event (job_id, created_at DESC)" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_alert_event_code_created" in migration
    assert "ON admin_export_job_alert_event (error_code, created_at DESC)" in migration


def test_admin_export_job_error_field_lengths_migration_supports_existing_databases():
    migration = load_admin_export_job_error_field_lengths_migration()

    assert "ALTER TABLE IF EXISTS admin_export_job" in migration
    assert "ALTER COLUMN error_code TYPE VARCHAR(80)" in migration
    assert "ALTER COLUMN error_message TYPE VARCHAR(500)" in migration
    assert "ALTER TABLE IF EXISTS admin_export_job_alert_event" in migration
    assert "ALTER COLUMN error_code TYPE VARCHAR(80)" in migration


def test_admin_export_job_alert_event_ack_migration_supports_existing_databases():
    migration = load_admin_export_job_alert_event_ack_migration()

    assert "ALTER TABLE IF EXISTS admin_export_job_alert_event" in migration
    assert "ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP" in migration
    assert "ADD COLUMN IF NOT EXISTS acknowledged_by_admin_user_id BIGINT REFERENCES admin_user(id)" in migration
    assert "ADD COLUMN IF NOT EXISTS acknowledged_by_username VARCHAR(64)" in migration
    assert "ADD COLUMN IF NOT EXISTS acknowledged_by_display_name VARCHAR(100)" in migration
    assert "ADD COLUMN IF NOT EXISTS acknowledge_note VARCHAR(200)" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_alert_event_ack_created" in migration
    assert "ON admin_export_job_alert_event (acknowledged_at, created_at DESC)" in migration


def test_admin_export_job_alert_event_close_migration_supports_existing_databases():
    migration = load_admin_export_job_alert_event_close_migration()

    assert "ALTER TABLE IF EXISTS admin_export_job_alert_event" in migration
    assert "ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP" in migration
    assert "ADD COLUMN IF NOT EXISTS closed_by_admin_user_id BIGINT REFERENCES admin_user(id)" in migration
    assert "ADD COLUMN IF NOT EXISTS closed_by_username VARCHAR(64)" in migration
    assert "ADD COLUMN IF NOT EXISTS closed_by_display_name VARCHAR(100)" in migration
    assert "ADD COLUMN IF NOT EXISTS close_note VARCHAR(200)" in migration
    assert "CREATE INDEX IF NOT EXISTS idx_admin_export_job_alert_event_closed_created" in migration
    assert "ON admin_export_job_alert_event (closed_at, created_at DESC)" in migration


def test_admin_export_job_alert_event_dedupe_migration_supports_existing_databases():
    migration = load_admin_export_job_alert_event_dedupe_migration()

    assert "ALTER TABLE IF EXISTS admin_export_job_alert_event" in migration
    assert "ADD COLUMN IF NOT EXISTS occurrence_count INTEGER NOT NULL DEFAULT 1" in migration
    assert "ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP" in migration
    assert "SET last_seen_at = created_at" in migration
    assert "ALTER COLUMN last_seen_at SET DEFAULT CURRENT_TIMESTAMP" in migration
    assert "ALTER COLUMN last_seen_at SET NOT NULL" in migration
    assert "ck_admin_export_job_alert_event_occurrence_count" in migration
    assert "CHECK (occurrence_count >= 1)" in migration
    assert "PARTITION BY job_id, error_code, alert_source" in migration
    assert "SUM(occurrence_count)" in migration
    assert "MAX(last_seen_at)" in migration
    assert "deduplicated by migration" in migration
    assert "CREATE UNIQUE INDEX IF NOT EXISTS uk_admin_export_job_alert_event_open_dedupe" in migration
    assert "ON admin_export_job_alert_event (job_id, error_code, alert_source)" in migration
    assert "WHERE closed_at IS NULL" in migration


def test_seed_resets_sequences_after_explicit_ids():
    seed = load_seed()

    for table_name in [
        "scenic_spot",
        "visitor",
        "ticket_type",
        "pier",
        "route_product",
        "time_slot_quota",
        "admin_user",
    ]:
        assert f"pg_get_serial_sequence('{table_name}', 'id')" in seed


def test_seed_uses_obvious_demo_identity_values():
    seed = load_seed()

    required_demo_values = [
        "演示临时游客",
        "演示实名游客",
        "DEMO-TEMP-PHONE-0001",
        "DEMO-ID-NOT-REAL-0002",
        "19900000001",
        "19900000002",
    ]
    for value in required_demo_values:
        assert value in seed

    forbidden_realistic_values = [
        "张三",
        "450321199901018885",
        "13911112222",
        "13888888888",
    ]
    for value in forbidden_realistic_values:
        assert value not in seed


def test_seed_contains_only_hashed_demo_admin_password():
    seed = load_seed()
    admin_seed = seed[seed.index("INSERT INTO admin_user") :]

    assert "demo_admin" in admin_seed
    assert "pbkdf2_sha256$260000$00112233445566778899aabbccddeeff$" in admin_seed
    for plaintext in [
        "AdminDemo!2026",
        "admin123",
        "123456",
        "ddx20060220.",
        "LEGACY_DEMO_PASSWORD",
    ]:
        assert plaintext not in admin_seed


def test_database_sql_files_do_not_define_environment_or_privileged_state():
    combined_sql = f"{load_schema()}\n{load_seed()}".upper()

    forbidden_fragments = [
        "CREATE ROLE",
        "CREATE USER",
        "ALTER SYSTEM",
        "DROP DATABASE",
        "DROP SCHEMA",
        "WITH PASSWORD",
        "IDENTIFIED BY",
        "DB_PASSWORD",
        ".ENV",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in combined_sql
