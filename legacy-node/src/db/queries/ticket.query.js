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

function normalizeTicketTypeRow(row) {
  return {
    id: Number(row.id),
    scenicSpotId: Number(row.scenic_spot_id),
    ticketName: row.ticket_name,
    ticketCategory: row.ticket_category,
    originalPrice: row.original_price,
    salePrice: row.sale_price,
    description: row.description,
    refundRule: row.refund_rule,
    isRealNameRequired: row.is_real_name_required,
    status: row.status,
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
    remainingQuota: quotaTotal - quotaSold,
    status: row.status,
  };
}

function normalizeRouteProductRow(row) {
  return {
    id: Number(row.id),
    ticketTypeId: Number(row.ticket_type_id),
    productName: row.product_name,
    tripType: row.trip_type,
    raftCapacity: Number(row.raft_capacity),
    windowPhone: row.window_phone,
    saleStatus: row.sale_status,
  };
}

function normalizePierRow(row) {
  return {
    id: Number(row.id),
    scenicSpotId: Number(row.scenic_spot_id),
    pierName: row.pier_name,
    pierType: row.pier_type,
    contactPhone: row.contact_phone,
    status: row.status,
    sortNo: Number(row.sort_no),
  };
}

function normalizeAdminRouteProductRow(row) {
  return {
    id: Number(row.id),
    scenicSpotId: Number(row.scenic_spot_id),
    ticketTypeId: Number(row.ticket_type_id),
    productName: row.product_name,
    ticketName: row.ticket_name,
    ticketCategory: row.ticket_category,
    originalPrice: row.original_price,
    salePrice: row.sale_price,
    raftCapacity: Number(row.raft_capacity),
    tripType: row.trip_type,
    startPierId: Number(row.start_pier_id),
    startPierName: row.start_pier_name,
    endPierId: Number(row.end_pier_id),
    endPierName: row.end_pier_name,
    windowPhone: row.window_phone,
    routeStatus: row.route_status,
    ticketStatus: row.ticket_status,
    saleStatus: row.sale_status,
  };
}

function createTicketQuery(options = {}) {
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

  async function findTicketTypes() {
    const result = await query(`
      SELECT
        id,
        scenic_spot_id,
        ticket_name,
        ticket_category,
        original_price,
        sale_price,
        description,
        refund_rule,
        is_real_name_required,
        status
      FROM ticket_type
      WHERE status = 'ENABLED'
      ORDER BY id
    `);

    return result.rows.map(normalizeTicketTypeRow);
  }

  async function findTimeSlotsByTicketTypeAndDate(ticketTypeId, visitDate) {
    const result = await query(
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
        WHERE ticket_type_id = $1
          AND visit_date = $2::date
          AND status = 'ENABLED'
        ORDER BY slot_start_time, slot_end_time, id
      `,
      [ticketTypeId, visitDate],
    );

    return result.rows.map(normalizeTimeSlotRow);
  }

  async function findRouteProducts() {
    const result = await query(`
      SELECT
        rp.id,
        rp.ticket_type_id,
        rp.product_name,
        rp.trip_type,
        rp.raft_capacity,
        rp.window_phone,
        COALESCE(osn.sale_status, 'UNCONFIGURED') AS sale_status
      FROM route_product rp
      LEFT JOIN offline_sale_notice osn
        ON osn.route_product_id = rp.id
       AND osn.business_date = CURRENT_DATE
      WHERE rp.status = 'ENABLED'
      ORDER BY rp.id
    `);

    return result.rows.map(normalizeRouteProductRow);
  }

  async function findPiers() {
    const result = await query(`
      SELECT
        id,
        scenic_spot_id,
        pier_name,
        pier_type,
        contact_phone,
        status,
        sort_no
      FROM pier
      WHERE status = 'ENABLED'
      ORDER BY sort_no ASC, id ASC
    `);

    return result.rows.map(normalizePierRow);
  }

  async function findAdminRouteProducts() {
    const result = await query(`
      SELECT
        rp.id,
        rp.scenic_spot_id,
        rp.ticket_type_id,
        rp.product_name,
        tt.ticket_name,
        tt.ticket_category,
        tt.original_price,
        tt.sale_price,
        rp.raft_capacity,
        rp.trip_type,
        rp.start_pier_id,
        start_pier.pier_name AS start_pier_name,
        rp.end_pier_id,
        end_pier.pier_name AS end_pier_name,
        rp.window_phone,
        rp.status AS route_status,
        tt.status AS ticket_status,
        COALESCE(osn.sale_status, 'UNCONFIGURED') AS sale_status
      FROM route_product rp
      JOIN ticket_type tt ON tt.id = rp.ticket_type_id
      LEFT JOIN pier start_pier ON start_pier.id = rp.start_pier_id
      LEFT JOIN pier end_pier ON end_pier.id = rp.end_pier_id
      LEFT JOIN offline_sale_notice osn
        ON osn.route_product_id = rp.id
       AND osn.business_date = CURRENT_DATE
      ORDER BY rp.id
    `);

    return result.rows.map(normalizeAdminRouteProductRow);
  }

  async function findAdminRouteProductById(routeProductId) {
    const result = await query(
      `
        SELECT
          rp.id,
          rp.scenic_spot_id,
          rp.ticket_type_id,
          rp.product_name,
          tt.ticket_name,
          tt.ticket_category,
          tt.original_price,
          tt.sale_price,
          rp.raft_capacity,
          rp.trip_type,
          rp.start_pier_id,
          start_pier.pier_name AS start_pier_name,
          rp.end_pier_id,
          end_pier.pier_name AS end_pier_name,
          rp.window_phone,
          rp.status AS route_status,
          tt.status AS ticket_status,
          COALESCE(osn.sale_status, 'UNCONFIGURED') AS sale_status
        FROM route_product rp
        JOIN ticket_type tt ON tt.id = rp.ticket_type_id
        LEFT JOIN pier start_pier ON start_pier.id = rp.start_pier_id
        LEFT JOIN pier end_pier ON end_pier.id = rp.end_pier_id
        LEFT JOIN offline_sale_notice osn
          ON osn.route_product_id = rp.id
         AND osn.business_date = CURRENT_DATE
        WHERE rp.id = $1
        LIMIT 1
      `,
      [routeProductId],
    );

    return result.rows[0] ? normalizeAdminRouteProductRow(result.rows[0]) : null;
  }

  async function findAdminTimeSlotsByTicketTypeAndDate(ticketTypeId, visitDate) {
    const result = await query(
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
        WHERE ticket_type_id = $1
          AND visit_date = $2::date
        ORDER BY slot_start_time, slot_end_time, id
      `,
      [ticketTypeId, visitDate],
    );

    return result.rows.map(normalizeTimeSlotRow);
  }

  async function insertTicketType(client, ticketTypeInput) {
    const executor = client && typeof client.query === 'function'
      ? client.query.bind(client)
      : query;
    const result = await executor(
      `
        INSERT INTO ticket_type (
          scenic_spot_id,
          ticket_name,
          ticket_category,
          original_price,
          sale_price,
          description,
          refund_rule,
          is_real_name_required,
          status,
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
          NOW(),
          NOW()
        )
        RETURNING
          id,
          scenic_spot_id,
          ticket_name,
          ticket_category,
          original_price,
          sale_price,
          description,
          refund_rule,
          is_real_name_required,
          status
      `,
      [
        ticketTypeInput.scenicSpotId,
        ticketTypeInput.ticketName,
        ticketTypeInput.ticketCategory,
        ticketTypeInput.originalPrice,
        ticketTypeInput.salePrice,
        ticketTypeInput.description,
        ticketTypeInput.refundRule,
        ticketTypeInput.isRealNameRequired,
        ticketTypeInput.status,
      ],
    );

    return result.rows[0] ? normalizeTicketTypeRow(result.rows[0]) : null;
  }

  async function insertRouteProduct(client, routeProductInput) {
    const executor = client && typeof client.query === 'function'
      ? client.query.bind(client)
      : query;
    const result = await executor(
      `
        INSERT INTO route_product (
          scenic_spot_id,
          ticket_type_id,
          product_name,
          raft_capacity,
          trip_type,
          start_pier_id,
          end_pier_id,
          window_phone,
          sale_price,
          status,
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
          NOW(),
          NOW()
        )
        RETURNING
          id,
          scenic_spot_id,
          ticket_type_id,
          product_name,
          raft_capacity,
          trip_type,
          start_pier_id,
          end_pier_id,
          window_phone,
          status
      `,
      [
        routeProductInput.scenicSpotId,
        routeProductInput.ticketTypeId,
        routeProductInput.productName,
        routeProductInput.raftCapacity,
        routeProductInput.tripType,
        routeProductInput.startPierId,
        routeProductInput.endPierId,
        routeProductInput.windowPhone,
        routeProductInput.salePrice,
        routeProductInput.status,
      ],
    );

    return result.rows[0] ? {
      id: Number(result.rows[0].id),
      scenicSpotId: Number(result.rows[0].scenic_spot_id),
      ticketTypeId: Number(result.rows[0].ticket_type_id),
      productName: result.rows[0].product_name,
      raftCapacity: Number(result.rows[0].raft_capacity),
      tripType: result.rows[0].trip_type,
      startPierId: Number(result.rows[0].start_pier_id),
      endPierId: Number(result.rows[0].end_pier_id),
      windowPhone: result.rows[0].window_phone,
      status: result.rows[0].status,
    } : null;
  }

  async function updateRouteProductStatus(client, routeProductId, status) {
    const executor = client && typeof client.query === 'function'
      ? client.query.bind(client)
      : query;
    const result = await executor(
      `
        UPDATE route_product
        SET status = $2,
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, ticket_type_id, status
      `,
      [routeProductId, status],
    );

    return result.rows[0] ? {
      id: Number(result.rows[0].id),
      ticketTypeId: Number(result.rows[0].ticket_type_id),
      status: result.rows[0].status,
    } : null;
  }

  async function updateTicketTypeStatus(client, ticketTypeId, status) {
    const executor = client && typeof client.query === 'function'
      ? client.query.bind(client)
      : query;
    const result = await executor(
      `
        UPDATE ticket_type
        SET status = $2,
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, status
      `,
      [ticketTypeId, status],
    );

    return result.rows[0] ? {
      id: Number(result.rows[0].id),
      status: result.rows[0].status,
    } : null;
  }

  async function findTimeSlotQuotaByKey(client, timeSlotInput) {
    const executor = client && typeof client.query === 'function'
      ? client.query.bind(client)
      : query;
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
        WHERE ticket_type_id = $1
          AND visit_date = $2::date
          AND slot_start_time = $3::time
          AND slot_end_time = $4::time
        LIMIT 1
      `,
      [
        timeSlotInput.ticketTypeId,
        timeSlotInput.visitDate,
        timeSlotInput.slotStartTime,
        timeSlotInput.slotEndTime,
      ],
    );

    return result.rows[0] ? normalizeTimeSlotRow(result.rows[0]) : null;
  }

  async function insertTimeSlotQuota(client, timeSlotInput) {
    const executor = client && typeof client.query === 'function'
      ? client.query.bind(client)
      : query;
    const result = await executor(
      `
        INSERT INTO time_slot_quota (
          ticket_type_id,
          visit_date,
          slot_start_time,
          slot_end_time,
          quota_total,
          quota_sold,
          quota_checked_in,
          status,
          created_at,
          updated_at
        ) VALUES (
          $1,
          $2::date,
          $3::time,
          $4::time,
          $5,
          0,
          0,
          $6,
          NOW(),
          NOW()
        )
        RETURNING
          id,
          ticket_type_id,
          visit_date,
          slot_start_time,
          slot_end_time,
          quota_total,
          quota_sold,
          quota_checked_in,
          status
      `,
      [
        timeSlotInput.ticketTypeId,
        timeSlotInput.visitDate,
        timeSlotInput.slotStartTime,
        timeSlotInput.slotEndTime,
        timeSlotInput.quotaTotal,
        timeSlotInput.status,
      ],
    );

    return result.rows[0] ? normalizeTimeSlotRow(result.rows[0]) : null;
  }

  async function updateTimeSlotQuota(client, timeSlotId, timeSlotInput) {
    const executor = client && typeof client.query === 'function'
      ? client.query.bind(client)
      : query;
    const result = await executor(
      `
        UPDATE time_slot_quota
        SET quota_total = $2,
            status = $3,
            updated_at = NOW()
        WHERE id = $1
        RETURNING
          id,
          ticket_type_id,
          visit_date,
          slot_start_time,
          slot_end_time,
          quota_total,
          quota_sold,
          quota_checked_in,
          status
      `,
      [timeSlotId, timeSlotInput.quotaTotal, timeSlotInput.status],
    );

    return result.rows[0] ? normalizeTimeSlotRow(result.rows[0]) : null;
  }

  return {
    findAdminRouteProductById,
    findAdminRouteProducts,
    findAdminTimeSlotsByTicketTypeAndDate,
    findPiers,
    findTicketTypes,
    findTimeSlotsByTicketTypeAndDate,
    findTimeSlotQuotaByKey,
    findRouteProducts,
    insertRouteProduct,
    insertTicketType,
    insertTimeSlotQuota,
    updateRouteProductStatus,
    updateTicketTypeStatus,
    updateTimeSlotQuota,
    withTransaction,
  };
}

module.exports = {
  createTicketQuery,
  normalizeAdminRouteProductRow,
  normalizePierRow,
  normalizeRouteProductRow,
  normalizeTicketTypeRow,
  normalizeTimeSlotRow,
};
