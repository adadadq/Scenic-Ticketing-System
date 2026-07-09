-- Development seed data for local demos.

INSERT INTO scenic_spot (id, spot_name, address, open_time, close_time)
VALUES (1, '遇龙河景区', '广西桂林阳朔遇龙河', '08:00', '18:30');

INSERT INTO visitor (id, visitor_name, id_type, id_number, phone, visitor_scope, username, password_hash)
VALUES
    (1, '演示临时游客', 'TEMP_PHONE', 'DEMO-TEMP-PHONE-0001', '19900000001', 'TEMP', NULL, NULL),
    (
        2,
        '演示实名游客',
        'ACCOUNT',
        'DEMO-ID-NOT-REAL-0002',
        '19900000002',
        'REGISTERED',
        'demo_visitor',
        'pbkdf2_sha256$260000$00112233445566778899aabbccddeeff$c342952f524f5a2d249492e6ec8eb722cb2b986eaa9fca479ce1ae024c741ab3'
    );

INSERT INTO ticket_type (
    id,
    scenic_spot_id,
    ticket_name,
    ticket_category,
    original_price,
    sale_price,
    description,
    refund_rule
) VALUES
    (1, 1, '遇龙河成人票', 'ADULT', 168.00, 128.00, '成人竹筏漂流票', '游玩日前一天18:00前可退'),
    (2, 1, '遇龙河儿童票', 'CHILD', 84.00, 68.00, '儿童竹筏漂流票', '游玩日前一天18:00前可退');

INSERT INTO pier (id, scenic_spot_id, pier_name, pier_type, contact_phone, sort_no)
VALUES
    (1, 1, '金龙桥码头', 'DEPARTURE', '0773-000001', 1),
    (2, 1, '旧县码头', 'ARRIVAL', '0773-000002', 2);

INSERT INTO route_product (
    id,
    scenic_spot_id,
    ticket_type_id,
    product_name,
    raft_capacity,
    trip_type,
    start_pier_id,
    end_pier_id,
    window_phone,
    sale_price
) VALUES
    (1, 1, 1, '金龙桥至旧县成人票', 2, 'ONE_WAY', 1, 2, '0773-1234567', 128.00),
    (2, 1, 2, '金龙桥至旧县儿童票', 2, 'ONE_WAY', 1, 2, '0773-1234567', 68.00);

INSERT INTO time_slot_quota (
    ticket_type_id,
    visit_date,
    slot_start_time,
    slot_end_time,
    quota_total,
    quota_sold
) VALUES
    (1, CURRENT_DATE, '08:30', '10:30', 40, 0),
    (1, CURRENT_DATE, '10:30', '12:30', 30, 0),
    (1, CURRENT_DATE, '13:30', '15:30', 96, 0),
    (1, CURRENT_DATE, '15:30', '17:30', 88, 0),
    (2, CURRENT_DATE, '08:30', '10:30', 20, 0),
    (2, CURRENT_DATE, '10:30', '12:30', 18, 0),
    (2, CURRENT_DATE, '13:30', '15:30', 48, 0),
    (2, CURRENT_DATE, '15:30', '17:30', 42, 0);

INSERT INTO admin_user (id, username, display_name, password_hash, role, status)
VALUES (
    1,
    'demo_admin',
    '演示管理员',
    'pbkdf2_sha256$260000$00112233445566778899aabbccddeeff$de623434a18780c2dcae68e5cbb9165c6e5aa5a2e73271d31f482802f5808a60',
    'SUPER_ADMIN',
    'ENABLED'
);

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
    ('last_backup_label', '今天 02:30');

SELECT setval(pg_get_serial_sequence('scenic_spot', 'id'), (SELECT MAX(id) FROM scenic_spot));
SELECT setval(pg_get_serial_sequence('visitor', 'id'), (SELECT MAX(id) FROM visitor));
SELECT setval(pg_get_serial_sequence('ticket_type', 'id'), (SELECT MAX(id) FROM ticket_type));
SELECT setval(pg_get_serial_sequence('pier', 'id'), (SELECT MAX(id) FROM pier));
SELECT setval(pg_get_serial_sequence('route_product', 'id'), (SELECT MAX(id) FROM route_product));
SELECT setval(pg_get_serial_sequence('time_slot_quota', 'id'), (SELECT MAX(id) FROM time_slot_quota));
SELECT setval(pg_get_serial_sequence('admin_user', 'id'), (SELECT MAX(id) FROM admin_user));
