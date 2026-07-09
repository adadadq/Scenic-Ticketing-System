const { AppError } = require('../../utils/app-error');
const { formatDateInAsiaShanghai } = require('../../utils/date');
const { createDbPool } = require('../../config/db');

function unavailableQuery() {
  throw new AppError(503, 'database is unavailable');
}

function createQueryExecutor(pool) {
  if (!pool || typeof pool.query !== 'function') {
    return unavailableQuery;
  }

  return (sql, params) => pool.query(sql, params);
}

function getExecutor(client, fallbackQuery) {
  if (client && typeof client.query === 'function') {
    return client.query.bind(client);
  }

  return fallbackQuery;
}

function normalizeTicketTypeRow(row) {
  return {
    id: Number(row.id),
    ticketTypeId: Number(row.id),
    scenicSpotId: Number(row.scenic_spot_id),
    ticketName: row.ticket_name,
    productName: row.route_product_name || row.ticket_name,
    tripType: row.trip_type || null,
    raftCapacity: row.raft_capacity ? Number(row.raft_capacity) : null,
    windowPhone: row.window_phone || null,
    salePrice: Number(row.sale_price),
  };
}

function normalizeTimeSlotRow(row) {
  const quotaTotal = Number(row.quota_total);
  const quotaSold = Number(row.quota_sold);
  const quotaCheckedIn = Number(row.quota_checked_in);

  return {
    id: Number(row.id),
    ticketTypeId: Number(row.ticket_type_id),
    visitDate: formatDateInAsiaShanghai(row.visit_date),
    slotStartTime: row.slot_start_time,
    slotEndTime: row.slot_end_time,
    quotaTotal,
    quotaSold,
    quotaCheckedIn,
    status: row.status,
    remainingQuota: quotaTotal - quotaSold,
  };
}

function normalizeOrderRow(row) {
  return {
    id: Number(row.id),
    orderNo: row.order_no,
  };
}

function normalizeOrderItemRow(row) {
  return {
    id: Number(row.id),
    itemNo: row.item_no,
    ticketCode: row.ticket_code,
  };
}

function normalizeUpdatedQuotaRow(row) {
  return {
    id: Number(row.id),
    quotaSold: Number(row.quota_sold),
  };
}

function createOrderQuery(options = {}) {
  const pool = options.pool || options.dbPool || createDbPool(options);
  const query = createQueryExecutor(pool);

  async function withTransaction(work) {
    if (!pool || typeof pool.connect !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const client = await pool.connect();

    try {
      await client.query('BEGIN');
      const result = await work(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      try {
        await client.query('ROLLBACK');
      } catch (_rollbackError) {
        // ignore rollback failures so the original error surfaces
      }
      throw error;
    } finally {
      if (typeof client.release === 'function') {
        client.release();
      }
    }
  }

  async function findTicketTypeById(client, ticketTypeId) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        SELECT
          tt.id,
          tt.scenic_spot_id,
          tt.ticket_name,
          tt.sale_price,
          rp.product_name AS route_product_name,
          rp.trip_type,
          rp.raft_capacity,
          rp.window_phone
        FROM ticket_type tt
        LEFT JOIN route_product rp ON rp.ticket_type_id = tt.id
        WHERE tt.id = $1
          AND tt.status = 'ENABLED'
        LIMIT 1
      `,
      [ticketTypeId],
    );

    return result.rows[0] ? normalizeTicketTypeRow(result.rows[0]) : null;
  }

  async function lockTimeSlotQuota(client, timeSlotId, visitDate) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        SELECT
          id,
          ticket_type_id,
          visit_date,
          slot_start_time,
          slot_end_time,
          quota_total,
          quota_sold,
          quota_checked_in,
          status
        FROM time_slot_quota
        WHERE id = $1
          AND visit_date = $2::date
          AND status = 'ENABLED'
        FOR UPDATE
      `,
      [timeSlotId, visitDate],
    );

    return result.rows[0] ? normalizeTimeSlotRow(result.rows[0]) : null;
  }

  async function insertOrder(client, orderInput) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        INSERT INTO ticket_order (
          order_no,
          scenic_spot_id,
          buyer_name,
          buyer_phone,
          order_source,
          order_status,
          payment_status,
          total_amount,
          discount_amount,
          payable_amount,
          paid_amount,
          order_time,
          paid_at,
          cancel_time,
          remark,
          created_at,
          updated_at
        ) VALUES (
          $1,
          $2,
          $3,
          $4,
          $5,
          $6,
          $7,
          $8,
          $9,
          $10,
          $11,
          NOW(),
          $12,
          $13,
          $14,
          NOW(),
          NOW()
        )
        RETURNING id, order_no
      `,
      [
        orderInput.orderNo,
        orderInput.scenicSpotId,
        orderInput.buyerName,
        orderInput.buyerPhone,
        orderInput.orderSource,
        orderInput.orderStatus,
        orderInput.paymentStatus,
        orderInput.totalAmount,
        orderInput.discountAmount,
        orderInput.payableAmount,
        orderInput.paidAmount,
        orderInput.paidAt,
        orderInput.cancelTime,
        orderInput.remark,
      ],
    );

    return result.rows[0] ? normalizeOrderRow(result.rows[0]) : null;
  }

  async function insertOrderItem(client, itemInput) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        INSERT INTO ticket_order_item (
          order_id,
          ticket_type_id,
          visitor_id,
          time_slot_id,
          item_no,
          visit_date,
          original_price,
          discount_amount,
          final_price,
          item_status,
          ticket_code,
          created_at,
          updated_at
        ) VALUES (
          $1,
          $2,
          $3,
          $4,
          $5,
          $6::date,
          $7,
          $8,
          $9,
          $10,
          $11,
          NOW(),
          NOW()
        )
        RETURNING id, item_no, ticket_code
      `,
      [
        itemInput.orderId,
        itemInput.ticketTypeId,
        itemInput.visitorId,
        itemInput.timeSlotId,
        itemInput.itemNo,
        itemInput.visitDate,
        itemInput.originalPrice,
        itemInput.discountAmount,
        itemInput.finalPrice,
        itemInput.itemStatus,
        itemInput.ticketCode,
      ],
    );

    return result.rows[0] ? normalizeOrderItemRow(result.rows[0]) : null;
  }

  async function updateTimeSlotQuotaSold(client, timeSlotId, soldCount) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE time_slot_quota
        SET quota_sold = quota_sold + $2,
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, quota_sold
      `,
      [timeSlotId, soldCount],
    );

    return result.rows[0] ? normalizeUpdatedQuotaRow(result.rows[0]) : null;
  }

  return {
    findTicketTypeById,
    insertOrder,
    insertOrderItem,
    lockTimeSlotQuota,
    updateTimeSlotQuotaSold,
    withTransaction,
  };
}

module.exports = {
  createOrderQuery,
  normalizeOrderItemRow,
  normalizeOrderRow,
  normalizeTicketTypeRow,
  normalizeTimeSlotRow,
};
