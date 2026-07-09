CREATE TABLE IF NOT EXISTS visitor_passenger_template (
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

ALTER TABLE ticket_order_item
    ADD COLUMN IF NOT EXISTS passenger_template_id BIGINT REFERENCES visitor_passenger_template(id),
    ADD COLUMN IF NOT EXISTS passenger_name VARCHAR(50),
    ADD COLUMN IF NOT EXISTS passenger_id_type VARCHAR(20),
    ADD COLUMN IF NOT EXISTS passenger_id_number VARCHAR(50),
    ADD COLUMN IF NOT EXISTS passenger_phone VARCHAR(20);

UPDATE ticket_order_item item
SET passenger_name = COALESCE(item.passenger_name, ticket_order.buyer_name),
    passenger_id_type = COALESCE(item.passenger_id_type, 'UNKNOWN'),
    passenger_id_number = COALESCE(item.passenger_id_number, item.item_no),
    passenger_phone = COALESCE(item.passenger_phone, ticket_order.buyer_phone)
FROM ticket_order
WHERE ticket_order.id = item.order_id
  AND (
    item.passenger_name IS NULL
    OR item.passenger_id_type IS NULL
    OR item.passenger_id_number IS NULL
    OR item.passenger_phone IS NULL
  );

ALTER TABLE ticket_order_item
    ALTER COLUMN passenger_name SET NOT NULL,
    ALTER COLUMN passenger_id_type SET NOT NULL,
    ALTER COLUMN passenger_id_number SET NOT NULL,
    ALTER COLUMN passenger_phone SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_passenger_template_owner ON visitor_passenger_template (owner_visitor_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_order_item_passenger_slot
    ON ticket_order_item (ticket_type_id, time_slot_id, visit_date, passenger_id_type, passenger_id_number)
    WHERE item_status <> 'CANCELLED';
