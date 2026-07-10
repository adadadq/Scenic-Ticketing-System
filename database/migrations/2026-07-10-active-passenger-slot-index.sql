-- Limit one active ticket per passenger, ticket type, date, and time slot.
-- Cancelled/refunded items should not block a passenger from buying again.

DROP INDEX IF EXISTS uq_ticket_order_item_passenger_slot;

CREATE UNIQUE INDEX uq_ticket_order_item_passenger_slot
    ON ticket_order_item (ticket_type_id, time_slot_id, visit_date, passenger_id_type, passenger_id_number)
    WHERE item_status IN ('PENDING_PAYMENT', 'UNUSED', 'USED');
