const { AppError } = require('../../utils/app-error');
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

function normalizeOrderItemRow(row) {
  return {
    id: Number(row.id),
    orderId: Number(row.order_id),
    timeSlotId: Number(row.time_slot_id),
    itemStatus: row.item_status,
    ticketCode: row.ticket_code,
  };
}

function normalizeCheckinRecordRow(row) {
  return {
    orderItemId: Number(row.order_item_id),
    checkinNo: row.checkin_no,
    checkinResult: row.checkin_result,
    checkinGate: row.checkin_gate,
  };
}

function normalizeQuotaRow(row) {
  return {
    id: Number(row.id),
    quotaCheckedIn: Number(row.quota_checked_in),
  };
}

function createCheckinQuery(options = {}) {
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

  async function findOrderItemByTicketCode(client, ticketCode) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        SELECT
          id,
          order_id,
          time_slot_id,
          item_status,
          ticket_code
        FROM ticket_order_item
        WHERE ticket_code = $1
        LIMIT 1
      `,
      [ticketCode],
    );

    return result.rows[0] ? normalizeOrderItemRow(result.rows[0]) : null;
  }

  async function insertCheckinRecord(client, input) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        INSERT INTO checkin_record (
          order_item_id,
          operator_id,
          checkin_no,
          checkin_result,
          checkin_gate,
          created_at
        ) VALUES (
          $1,
          $2,
          $3,
          $4,
          $5,
          NOW()
        )
        RETURNING order_item_id, checkin_no, checkin_result, checkin_gate
      `,
      [
        input.orderItemId,
        input.operatorId,
        input.checkinNo,
        input.checkinResult,
        input.checkinGate,
      ],
    );

    return result.rows[0] ? normalizeCheckinRecordRow(result.rows[0]) : null;
  }

  async function markOrderItemUsed(client, orderItemId) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE ticket_order_item
        SET item_status = 'USED',
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, item_status
      `,
      [orderItemId],
    );

    return result.rows[0]
      ? {
        id: Number(result.rows[0].id),
        itemStatus: result.rows[0].item_status,
      }
      : null;
  }

  async function incrementCheckedIn(client, timeSlotId) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE time_slot_quota
        SET quota_checked_in = quota_checked_in + 1,
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, quota_checked_in
      `,
      [timeSlotId],
    );

    return result.rows[0] ? normalizeQuotaRow(result.rows[0]) : null;
  }

  return {
    findOrderItemByTicketCode,
    incrementCheckedIn,
    insertCheckinRecord,
    markOrderItemUsed,
    withTransaction,
  };
}

module.exports = {
  createCheckinQuery,
};
