-- Scenic ticket system MVP schema for FastAPI backend.
-- Target dialect: openGauss / PostgreSQL style SQL.

CREATE TABLE scenic_spot (
    id BIGSERIAL PRIMARY KEY,
    spot_name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ENABLED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_scenic_spot_open_close CHECK (close_time > open_time),
    CONSTRAINT ck_scenic_spot_status CHECK (status IN ('ENABLED', 'DISABLED'))
);

CREATE TABLE visitor (
    id BIGSERIAL PRIMARY KEY,
    visitor_name VARCHAR(50) NOT NULL,
    id_type VARCHAR(20) NOT NULL,
    id_number VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    username VARCHAR(64),
    password_hash VARCHAR(255),
    gender VARCHAR(10),
    birth_date DATE,
    visitor_scope VARCHAR(20) NOT NULL DEFAULT 'TEMP',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_visitor_id_doc UNIQUE (id_type, id_number),
    CONSTRAINT uk_visitor_phone UNIQUE (phone),
    CONSTRAINT uk_visitor_username UNIQUE (username),
    CONSTRAINT ck_visitor_scope CHECK (visitor_scope IN ('TEMP', 'REGISTERED')),
    CONSTRAINT ck_visitor_account_credentials CHECK (
        (username IS NULL AND password_hash IS NULL)
        OR (username IS NOT NULL AND password_hash IS NOT NULL)
    )
);

CREATE TABLE visitor_passenger_template (
    id BIGSERIAL PRIMARY KEY,
    owner_visitor_id BIGINT NOT NULL REFERENCES visitor(id),
    passenger_name VARCHAR(50) NOT NULL,
    id_type VARCHAR(20) NOT NULL,
    id_number VARCHAR(50) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_passenger_template_owner_doc UNIQUE (owner_visitor_id, id_type, id_number)
);

CREATE TABLE ticket_type (
    id BIGSERIAL PRIMARY KEY,
    scenic_spot_id BIGINT NOT NULL REFERENCES scenic_spot(id),
    ticket_name VARCHAR(100) NOT NULL,
    ticket_category VARCHAR(50) NOT NULL,
    original_price NUMERIC(10,2) NOT NULL CHECK (original_price >= 0),
    sale_price NUMERIC(10,2) NOT NULL CHECK (sale_price >= 0),
    description VARCHAR(255),
    refund_rule VARCHAR(255),
    is_real_name_required BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) NOT NULL DEFAULT 'ENABLED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_ticket_type_spot_name UNIQUE (scenic_spot_id, ticket_name),
    CONSTRAINT ck_ticket_type_sale_not_over_original CHECK (sale_price <= original_price),
    CONSTRAINT ck_ticket_type_status CHECK (status IN ('ENABLED', 'DISABLED'))
);

CREATE TABLE pier (
    id BIGSERIAL PRIMARY KEY,
    scenic_spot_id BIGINT NOT NULL REFERENCES scenic_spot(id),
    pier_name VARCHAR(100) NOT NULL,
    pier_type VARCHAR(20) NOT NULL,
    contact_phone VARCHAR(20),
    status VARCHAR(20) NOT NULL DEFAULT 'ENABLED',
    sort_no INTEGER NOT NULL DEFAULT 0 CHECK (sort_no >= 0),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_pier_scenic_name UNIQUE (scenic_spot_id, pier_name),
    CONSTRAINT ck_pier_type CHECK (pier_type IN ('DEPARTURE', 'ARRIVAL', 'BOTH')),
    CONSTRAINT ck_pier_status CHECK (status IN ('ENABLED', 'DISABLED'))
);

CREATE TABLE route_product (
    id BIGSERIAL PRIMARY KEY,
    scenic_spot_id BIGINT NOT NULL REFERENCES scenic_spot(id),
    ticket_type_id BIGINT NOT NULL REFERENCES ticket_type(id),
    product_name VARCHAR(100) NOT NULL,
    raft_capacity INTEGER NOT NULL,
    trip_type VARCHAR(20) NOT NULL,
    start_pier_id BIGINT NOT NULL REFERENCES pier(id),
    end_pier_id BIGINT NOT NULL REFERENCES pier(id),
    window_phone VARCHAR(20) NOT NULL,
    sale_price NUMERIC(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ENABLED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_route_product_ticket_type UNIQUE (ticket_type_id),
    CONSTRAINT uq_route_product_id_ticket_type UNIQUE (id, ticket_type_id),
    CONSTRAINT ck_route_product_distinct_pier CHECK (start_pier_id <> end_pier_id),
    CONSTRAINT ck_route_product_trip_type CHECK (trip_type IN ('ONE_WAY', 'ROUND_TRIP')),
    CONSTRAINT ck_route_product_sale_price CHECK (sale_price >= 0),
    CONSTRAINT ck_route_product_raft_capacity CHECK (raft_capacity > 0),
    CONSTRAINT ck_route_product_status CHECK (status IN ('ENABLED', 'DISABLED'))
);

CREATE TABLE time_slot_quota (
    id BIGSERIAL PRIMARY KEY,
    ticket_type_id BIGINT NOT NULL REFERENCES ticket_type(id),
    visit_date DATE NOT NULL,
    slot_start_time TIME NOT NULL,
    slot_end_time TIME NOT NULL,
    quota_total INTEGER NOT NULL CHECK (quota_total >= 0),
    quota_sold INTEGER NOT NULL DEFAULT 0 CHECK (quota_sold >= 0),
    quota_checked_in INTEGER NOT NULL DEFAULT 0 CHECK (quota_checked_in >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'ENABLED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_time_slot_quota UNIQUE (ticket_type_id, visit_date, slot_start_time, slot_end_time),
    CONSTRAINT uk_time_slot_quota_id_type_date UNIQUE (id, ticket_type_id, visit_date),
    CONSTRAINT ck_quota_sold_not_over_total CHECK (quota_sold <= quota_total),
    CONSTRAINT ck_quota_checked_not_over_sold CHECK (quota_checked_in <= quota_sold),
    CONSTRAINT ck_time_slot_order CHECK (slot_end_time > slot_start_time),
    CONSTRAINT ck_time_slot_status CHECK (status IN ('ENABLED', 'DISABLED'))
);

CREATE TABLE ticket_order (
    id BIGSERIAL PRIMARY KEY,
    order_no VARCHAR(32) NOT NULL,
    visitor_id BIGINT NOT NULL REFERENCES visitor(id),
    scenic_spot_id BIGINT NOT NULL REFERENCES scenic_spot(id),
    buyer_name VARCHAR(50) NOT NULL,
    buyer_phone VARCHAR(20) NOT NULL,
    order_source VARCHAR(20) NOT NULL DEFAULT 'ONLINE',
    order_status VARCHAR(20) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL CHECK (total_amount >= 0),
    discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    payable_amount NUMERIC(10,2) NOT NULL CHECK (payable_amount >= 0),
    paid_amount NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (paid_amount >= 0),
    order_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP,
    cancel_time TIMESTAMP,
    remark VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_ticket_order_order_no UNIQUE (order_no),
    CONSTRAINT ck_ticket_order_paid_not_over_payable CHECK (paid_amount <= payable_amount),
    CONSTRAINT ck_ticket_order_payable_relation CHECK (payable_amount = total_amount - discount_amount),
    CONSTRAINT ck_ticket_order_source CHECK (order_source IN ('ONLINE', 'OFFLINE')),
    CONSTRAINT ck_ticket_order_status CHECK (order_status IN ('CREATED', 'PAID', 'CANCELLED', 'COMPLETED', 'REFUNDING', 'REFUNDED')),
    CONSTRAINT ck_ticket_order_payment_status CHECK (payment_status IN ('UNPAID', 'PAID', 'PARTIAL_REFUND', 'REFUNDED', 'FAILED'))
);

CREATE TABLE ticket_order_item (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES ticket_order(id),
    ticket_type_id BIGINT NOT NULL REFERENCES ticket_type(id),
    product_id BIGINT NOT NULL,
    visitor_id BIGINT NOT NULL REFERENCES visitor(id),
    time_slot_id BIGINT NOT NULL,
    passenger_template_id BIGINT REFERENCES visitor_passenger_template(id),
    passenger_name VARCHAR(50) NOT NULL,
    passenger_id_type VARCHAR(20) NOT NULL,
    passenger_id_number VARCHAR(50) NOT NULL,
    passenger_phone VARCHAR(20) NOT NULL,
    raft_no INTEGER,
    raft_seat_no INTEGER,
    raft_assigned_at TIMESTAMP,
    item_no VARCHAR(32) NOT NULL,
    visit_date DATE NOT NULL,
    original_price NUMERIC(10,2) NOT NULL CHECK (original_price >= 0),
    discount_amount NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (discount_amount >= 0),
    final_price NUMERIC(10,2) NOT NULL CHECK (final_price >= 0),
    item_status VARCHAR(20) NOT NULL,
    ticket_code VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_ticket_order_item_item_no UNIQUE (item_no),
    CONSTRAINT uk_ticket_order_item_ticket_code UNIQUE (ticket_code),
    CONSTRAINT uk_ticket_order_item_order_id_id UNIQUE (order_id, id),
    CONSTRAINT fk_ticket_order_item_slot_match FOREIGN KEY (time_slot_id, ticket_type_id, visit_date)
        REFERENCES time_slot_quota(id, ticket_type_id, visit_date),
    CONSTRAINT fk_ticket_order_item_product_match FOREIGN KEY (product_id, ticket_type_id)
        REFERENCES route_product(id, ticket_type_id),
    CONSTRAINT ck_ticket_order_item_price_relation CHECK (final_price = original_price - discount_amount),
    CONSTRAINT ck_ticket_order_item_raft_seat CHECK (raft_seat_no IS NULL OR raft_seat_no > 0),
    CONSTRAINT ck_ticket_order_item_raft_no CHECK (raft_no IS NULL OR raft_no > 0),
    CONSTRAINT ck_ticket_order_item_status CHECK (item_status IN ('PENDING_PAYMENT', 'UNUSED', 'USED', 'REFUNDED', 'CANCELLED'))
);

CREATE TABLE payment_record (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES ticket_order(id),
    payment_no VARCHAR(32) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL,
    payment_method VARCHAR(20) NOT NULL,
    payment_amount NUMERIC(10,2) NOT NULL CHECK (payment_amount > 0),
    payment_status VARCHAR(20) NOT NULL,
    transaction_no VARCHAR(64),
    paid_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_payment_record_payment_no UNIQUE (payment_no),
    CONSTRAINT uk_payment_record_order_idempotency UNIQUE (order_id, idempotency_key),
    CONSTRAINT ck_payment_record_method CHECK (payment_method IN ('MOCK', 'CASH', 'WECHAT', 'ALIPAY', 'BANK_CARD')),
    CONSTRAINT ck_payment_record_status CHECK (payment_status IN ('PENDING', 'SUCCESS', 'FAILED', 'REFUNDED')),
    CONSTRAINT ck_payment_record_paid_at CHECK (
        (payment_status IN ('SUCCESS', 'REFUNDED') AND paid_at IS NOT NULL)
        OR (payment_status IN ('PENDING', 'FAILED') AND paid_at IS NULL)
    )
);

CREATE TABLE admin_user (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(64) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ENABLED',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_admin_user_username UNIQUE (username),
    CONSTRAINT ck_admin_user_role CHECK (role IN ('SUPER_ADMIN', 'OPERATOR')),
    CONSTRAINT ck_admin_user_status CHECK (status IN ('ENABLED', 'DISABLED'))
);

CREATE TABLE refund_audit_log (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES ticket_order(id),
    order_no VARCHAR(32) NOT NULL,
    refund_type VARCHAR(20) NOT NULL,
    refunded_amount NUMERIC(10,2) NOT NULL CHECK (refunded_amount > 0),
    refunded_item_count INTEGER NOT NULL CHECK (refunded_item_count > 0),
    refunded_item_nos JSONB NOT NULL,
    reason VARCHAR(100),
    operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id),
    operator_username VARCHAR(64) NOT NULL,
    operator_display_name VARCHAR(100) NOT NULL,
    request_id VARCHAR(64),
    source_ip VARCHAR(64),
    device_id VARCHAR(32),
    admin_session_id BIGINT,
    user_agent VARCHAR(512),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_refund_audit_log_type CHECK (refund_type IN ('FULL', 'PARTIAL'))
);

CREATE TABLE check_in_audit_log (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES ticket_order(id),
    order_item_id BIGINT NOT NULL,
    order_no VARCHAR(32) NOT NULL,
    item_no VARCHAR(32) NOT NULL,
    ticket_code VARCHAR(64) NOT NULL,
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
    CONSTRAINT fk_check_in_audit_log_order_item FOREIGN KEY (order_id, order_item_id)
        REFERENCES ticket_order_item(order_id, id),
    CONSTRAINT ck_check_in_audit_log_action CHECK (action IN ('CHECK_IN', 'UNDO_CHECK_IN'))
);

CREATE TABLE check_in_failure_audit_log (
    id BIGSERIAL PRIMARY KEY,
    ticket_code VARCHAR(64) NOT NULL,
    action VARCHAR(20) NOT NULL,
    failure_code VARCHAR(40) NOT NULL,
    failure_message VARCHAR(100) NOT NULL,
    operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id),
    operator_username VARCHAR(64) NOT NULL,
    operator_display_name VARCHAR(100) NOT NULL,
    request_id VARCHAR(64),
    source_ip VARCHAR(64),
    device_id VARCHAR(32),
    admin_session_id BIGINT,
    user_agent VARCHAR(512),
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

CREATE TABLE admin_export_job (
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
    error_code VARCHAR(80),
    error_message VARCHAR(500),
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

CREATE TABLE admin_export_job_alert_event (
    id BIGSERIAL PRIMARY KEY,
    job_id VARCHAR(36) NOT NULL REFERENCES admin_export_job(job_id),
    export_type VARCHAR(40) NOT NULL,
    file_format VARCHAR(10) NOT NULL,
    error_code VARCHAR(80) NOT NULL,
    error_message VARCHAR(500) NOT NULL,
    alert_source VARCHAR(40) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by_admin_user_id BIGINT REFERENCES admin_user(id),
    acknowledged_by_username VARCHAR(64),
    acknowledged_by_display_name VARCHAR(100),
    acknowledge_note VARCHAR(200),
    closed_at TIMESTAMP,
    closed_by_admin_user_id BIGINT REFERENCES admin_user(id),
    closed_by_username VARCHAR(64),
    closed_by_display_name VARCHAR(100),
    close_note VARCHAR(200),
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    last_seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_admin_export_job_alert_event_occurrence_count CHECK (occurrence_count >= 1),
    CONSTRAINT ck_admin_export_job_alert_event_source CHECK (alert_source IN ('WORKER_FINAL_FAILURE'))
);

CREATE TABLE admin_system_setting (
    setting_key VARCHAR(64) PRIMARY KEY,
    setting_value VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admin_system_setting_audit_log (
    id BIGSERIAL PRIMARY KEY,
    changed_keys TEXT NOT NULL,
    action VARCHAR(255) NOT NULL,
    operator_admin_user_id BIGINT NOT NULL REFERENCES admin_user(id),
    operator_username VARCHAR(64) NOT NULL,
    operator_display_name VARCHAR(100) NOT NULL,
    request_id VARCHAR(64),
    source_ip VARCHAR(64),
    device_id VARCHAR(32),
    admin_session_id BIGINT,
    user_agent VARCHAR(512),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE user_session (
    id BIGSERIAL PRIMARY KEY,
    session_token_hash VARCHAR(128) NOT NULL,
    csrf_token_hash VARCHAR(128) NOT NULL,
    account_type VARCHAR(20) NOT NULL,
    visitor_id BIGINT REFERENCES visitor(id),
    admin_user_id BIGINT REFERENCES admin_user(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    CONSTRAINT uk_user_session_token_hash UNIQUE (session_token_hash),
    CONSTRAINT ck_user_session_account_type CHECK (account_type IN ('VISITOR', 'ADMIN')),
    CONSTRAINT ck_user_session_owner CHECK (
        (account_type = 'VISITOR' AND visitor_id IS NOT NULL AND admin_user_id IS NULL)
        OR (account_type = 'ADMIN' AND admin_user_id IS NOT NULL AND visitor_id IS NULL)
    )
);

CREATE INDEX idx_visitor_phone ON visitor (phone);
CREATE INDEX idx_passenger_template_owner ON visitor_passenger_template (owner_visitor_id);
CREATE INDEX idx_ticket_order_visitor_time ON ticket_order (visitor_id, order_time);
CREATE INDEX idx_ticket_order_buyer_phone_order_time ON ticket_order (buyer_phone, order_time);
CREATE INDEX idx_ticket_order_item_ticket_type_visit_date ON ticket_order_item (ticket_type_id, visit_date);
CREATE INDEX idx_ticket_order_item_product_id ON ticket_order_item (product_id);
CREATE INDEX idx_ticket_order_item_time_slot_id ON ticket_order_item (time_slot_id);
CREATE INDEX idx_ticket_order_item_raft_slot ON ticket_order_item (product_id, time_slot_id, visit_date, raft_no, raft_seat_no)
    WHERE raft_no IS NOT NULL;
CREATE UNIQUE INDEX uq_ticket_order_item_passenger_slot
    ON ticket_order_item (ticket_type_id, time_slot_id, visit_date, passenger_id_type, passenger_id_number)
    WHERE item_status IN ('PENDING_PAYMENT', 'UNUSED', 'USED');
CREATE INDEX idx_payment_record_status_paid_at ON payment_record (payment_status, paid_at);
CREATE UNIQUE INDEX uq_payment_record_mockpay_event_idempotency
    ON payment_record (idempotency_key)
    WHERE idempotency_key LIKE 'mockpay:%';
CREATE INDEX idx_refund_audit_log_order_created ON refund_audit_log (order_id, created_at DESC);
CREATE INDEX idx_refund_audit_log_created ON refund_audit_log (created_at DESC);
CREATE INDEX idx_check_in_audit_log_ticket_created ON check_in_audit_log (ticket_code, created_at DESC);
CREATE INDEX idx_check_in_audit_log_order_created ON check_in_audit_log (order_id, created_at DESC);
CREATE INDEX idx_check_in_audit_log_created ON check_in_audit_log (created_at DESC);
CREATE INDEX idx_check_in_failure_audit_log_ticket_created
    ON check_in_failure_audit_log (ticket_code, created_at DESC);
CREATE INDEX idx_check_in_failure_audit_log_code_created
    ON check_in_failure_audit_log (failure_code, created_at DESC);
CREATE INDEX idx_check_in_failure_audit_log_created ON check_in_failure_audit_log (created_at DESC);
CREATE INDEX idx_admin_export_job_requested_at ON admin_export_job (requested_at DESC);
CREATE INDEX idx_admin_export_job_status_requested_at ON admin_export_job (status, requested_at DESC);
CREATE INDEX idx_admin_export_job_status_next_attempt_requested_at
    ON admin_export_job (status, next_attempt_at, requested_at DESC);
CREATE INDEX idx_admin_export_job_status_started_at ON admin_export_job (status, started_at);
CREATE INDEX idx_admin_export_job_type_requested_at ON admin_export_job (export_type, requested_at DESC);
CREATE INDEX idx_admin_export_job_alert_event_job_created
    ON admin_export_job_alert_event (job_id, created_at DESC);
CREATE INDEX idx_admin_export_job_alert_event_code_created
    ON admin_export_job_alert_event (error_code, created_at DESC);
CREATE INDEX idx_admin_export_job_alert_event_ack_created
    ON admin_export_job_alert_event (acknowledged_at, created_at DESC);
CREATE INDEX idx_admin_export_job_alert_event_closed_created
    ON admin_export_job_alert_event (closed_at, created_at DESC);
CREATE UNIQUE INDEX uk_admin_export_job_alert_event_open_dedupe
    ON admin_export_job_alert_event (job_id, error_code, alert_source)
    WHERE closed_at IS NULL;
CREATE INDEX idx_admin_system_setting_audit_log_created ON admin_system_setting_audit_log (created_at DESC);
CREATE INDEX idx_admin_ticket_audit_log_created ON admin_ticket_audit_log (created_at DESC);
CREATE INDEX idx_admin_user_status ON admin_user (status);
CREATE INDEX idx_route_product_status ON route_product (status);
CREATE INDEX idx_route_product_piers ON route_product (start_pier_id, end_pier_id);
CREATE INDEX idx_user_session_visitor ON user_session (visitor_id);
CREATE INDEX idx_user_session_admin ON user_session (admin_user_id);
CREATE INDEX idx_user_session_expires_at ON user_session (expires_at);
