ALTER TABLE ticket_order_item
    ADD COLUMN IF NOT EXISTS raft_no INTEGER,
    ADD COLUMN IF NOT EXISTS raft_seat_no INTEGER,
    ADD COLUMN IF NOT EXISTS raft_assigned_at TIMESTAMP;

ALTER TABLE ticket_order_item
    DROP CONSTRAINT IF EXISTS ck_ticket_order_item_raft_no,
    ADD CONSTRAINT ck_ticket_order_item_raft_no CHECK (raft_no IS NULL OR raft_no > 0),
    DROP CONSTRAINT IF EXISTS ck_ticket_order_item_raft_seat,
    ADD CONSTRAINT ck_ticket_order_item_raft_seat CHECK (raft_seat_no IS NULL OR raft_seat_no > 0);

CREATE INDEX IF NOT EXISTS idx_ticket_order_item_raft_slot
    ON ticket_order_item (product_id, time_slot_id, visit_date, raft_no, raft_seat_no)
    WHERE raft_no IS NOT NULL;
