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

function formatDate(value) {
  if (!(value instanceof Date)) {
    return value;
  }

  return value.toISOString().slice(0, 10);
}

function normalizeVisitorRow(row) {
  return {
    id: Number(row.id),
    visitorName: row.visitor_name,
    idType: row.id_type,
    idNumber: row.id_number,
    phone: row.phone,
    gender: row.gender,
    birthDate: formatDate(row.birth_date),
    status: row.status,
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

function normalizeRouteProductRow(row) {
  return {
    id: Number(row.id),
    scenicSpotId: Number(row.scenic_spot_id),
    ticketTypeId: Number(row.ticket_type_id),
    ticketName: row.ticket_name,
    productName: row.product_name,
    raftCapacity: Number(row.raft_capacity),
    tripType: row.trip_type,
    startPierId: Number(row.start_pier_id),
    startPierName: row.start_pier_name,
    endPierId: Number(row.end_pier_id),
    endPierName: row.end_pier_name,
    windowPhone: row.window_phone,
    salePrice: Number(row.sale_price),
    status: row.status,
    businessDate: formatDate(row.business_date),
    saleStatus: row.sale_status,
    remark: row.remark,
  };
}

function normalizeNoticeRow(row) {
  return {
    id: Number(row.id),
    routeProductId: Number(row.route_product_id),
    productName: row.product_name,
    businessDate: formatDate(row.business_date),
    saleStatus: row.sale_status,
    updatedAt: row.updated_at,
    remark: row.remark,
  };
}

function normalizeOrderSearchRow(row) {
  return {
    orderId: Number(row.order_id),
    orderNo: row.order_no,
    buyerName: row.buyer_name,
    buyerPhone: row.buyer_phone,
    orderSource: row.order_source,
    orderStatus: row.order_status,
    paymentStatus: row.payment_status,
    payableAmount: Number(row.payable_amount),
    paidAmount: Number(row.paid_amount),
    orderTime: row.order_time,
    orderItemId: Number(row.order_item_id),
    ticketTypeId: Number(row.ticket_type_id),
    ticketName: row.ticket_name,
    visitorName: row.visitor_name,
    itemStatus: row.item_status,
    ticketCode: row.ticket_code,
    visitDate: formatDate(row.visit_date),
    finalPrice: Number(row.final_price),
  };
}

function normalizeOperationLogRow(row) {
  return {
    id: Number(row.id),
    operatorId: Number(row.operator_id),
    moduleName: row.module_name,
    operationType: row.operation_type,
    targetTable: row.target_table,
    targetId: row.target_id,
    operationResult: row.operation_result,
    requestIp: row.request_ip,
    detailJson: row.detail_json,
    createdAt: row.created_at,
    operationTime: row.operation_time,
  };
}

function createManageQuery(options = {}) {
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
        // keep the original error
      }
      throw error;
    } finally {
      if (typeof client.release === 'function') {
        client.release();
      }
    }
  }

  async function listVisitors(filters = {}) {
    const values = [];
    const where = [];

    if (filters.phone) {
      values.push(`%${filters.phone}%`);
      where.push(`phone LIKE $${values.length}`);
    }

    if (filters.keyword) {
      values.push(`%${filters.keyword}%`);
      where.push(`(visitor_name LIKE $${values.length} OR id_number LIKE $${values.length})`);
    }

    const result = await query(
      `
        SELECT id, visitor_name, id_type, id_number, phone, gender, birth_date, status
        FROM visitor
        ${where.length ? `WHERE ${where.join(' AND ')}` : ''}
        ORDER BY id DESC
        LIMIT 50
      `,
      values,
    );

    return result.rows.map(normalizeVisitorRow);
  }

  async function findVisitorByIdentity(idType, idNumber) {
    const result = await query(
      `
        SELECT id, visitor_name, id_type, id_number, phone, gender, birth_date, status
        FROM visitor
        WHERE id_type = $1
          AND id_number = $2
        LIMIT 1
      `,
      [idType, idNumber],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function findVisitorById(id) {
    const result = await query(
      `
        SELECT id, visitor_name, id_type, id_number, phone, gender, birth_date, status
        FROM visitor
        WHERE id = $1
        LIMIT 1
      `,
      [id],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function insertVisitor(client, input) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        INSERT INTO visitor (
          visitor_name,
          id_type,
          id_number,
          phone,
          gender,
          birth_date,
          created_at,
          updated_at
        ) VALUES (
          $1,
          $2,
          $3,
          $4,
          $5,
          $6::date,
          NOW(),
          NOW()
        )
        RETURNING id, visitor_name, id_type, id_number, phone, gender, birth_date
      `,
      [
        input.visitorName,
        input.idType,
        input.idNumber,
        input.phone,
        input.gender,
        input.birthDate,
      ],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function listPiers() {
    const result = await query(
      `
        SELECT id, scenic_spot_id, pier_name, pier_type, contact_phone, status, sort_no
        FROM pier
        ORDER BY sort_no, id
      `,
    );

    return result.rows.map(normalizePierRow);
  }

  async function insertPier(client, input) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        INSERT INTO pier (
          scenic_spot_id,
          pier_name,
          pier_type,
          contact_phone,
          status,
          sort_no,
          created_at,
          updated_at
        ) VALUES (
          $1,
          $2,
          $3,
          $4,
          $5,
          $6,
          NOW(),
          NOW()
        )
        RETURNING id, scenic_spot_id, pier_name, pier_type, contact_phone, status, sort_no
      `,
      [
        input.scenicSpotId,
        input.pierName,
        input.pierType,
        input.contactPhone,
        input.status,
        input.sortNo,
      ],
    );

    return result.rows[0] ? normalizePierRow(result.rows[0]) : null;
  }

  async function updatePier(client, id, input) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE pier
        SET pier_name = $2,
            pier_type = $3,
            contact_phone = $4,
            status = $5,
            sort_no = $6,
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, scenic_spot_id, pier_name, pier_type, contact_phone, status, sort_no
      `,
      [
        id,
        input.pierName,
        input.pierType,
        input.contactPhone,
        input.status,
        input.sortNo,
      ],
    );

    return result.rows[0] ? normalizePierRow(result.rows[0]) : null;
  }

  async function disablePier(client, id) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE pier
        SET status = 'DISABLED',
            updated_at = NOW()
        WHERE id = $1
        RETURNING id, scenic_spot_id, pier_name, pier_type, contact_phone, status, sort_no
      `,
      [id],
    );

    return result.rows[0] ? normalizePierRow(result.rows[0]) : null;
  }

  async function listRouteProducts(filters = {}) {
    const values = [];
    let noticeJoin = '';

    if (filters.businessDate) {
      values.push(filters.businessDate);
      noticeJoin = `AND osn.business_date = $${values.length}::date`;
    }

    const result = await query(
      `
        SELECT
          rp.id,
          rp.scenic_spot_id,
          rp.ticket_type_id,
          tt.ticket_name,
          rp.product_name,
          rp.raft_capacity,
          rp.trip_type,
          rp.start_pier_id,
          sp.pier_name AS start_pier_name,
          rp.end_pier_id,
          ep.pier_name AS end_pier_name,
          rp.window_phone,
          rp.sale_price,
          rp.status,
          osn.business_date,
          COALESCE(osn.sale_status, 'ON_SALE') AS sale_status,
          osn.remark
        FROM route_product rp
        JOIN ticket_type tt ON tt.id = rp.ticket_type_id
        JOIN pier sp ON sp.id = rp.start_pier_id
        JOIN pier ep ON ep.id = rp.end_pier_id
        LEFT JOIN offline_sale_notice osn
          ON osn.route_product_id = rp.id
          ${noticeJoin}
        ORDER BY rp.id
      `,
      values,
    );

    return result.rows.map(normalizeRouteProductRow);
  }

  async function insertRouteProduct(client, input) {
    const executor = getExecutor(client, query);
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
          sale_price,
          status,
          NULL::varchar AS ticket_name,
          NULL::varchar AS start_pier_name,
          NULL::varchar AS end_pier_name,
          NULL::date AS business_date,
          NULL::varchar AS sale_status,
          NULL::varchar AS remark
      `,
      [
        input.scenicSpotId,
        input.ticketTypeId,
        input.productName,
        input.raftCapacity,
        input.tripType,
        input.startPierId,
        input.endPierId,
        input.windowPhone,
        input.salePrice,
        input.status,
      ],
    );

    return result.rows[0] ? normalizeRouteProductRow(result.rows[0]) : null;
  }

  async function updateRouteProduct(client, id, input) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE route_product
        SET ticket_type_id = $2,
            product_name = $3,
            raft_capacity = $4,
            trip_type = $5,
            start_pier_id = $6,
            end_pier_id = $7,
            window_phone = $8,
            sale_price = $9,
            status = $10,
            updated_at = NOW()
        WHERE id = $1
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
          sale_price,
          status,
          NULL::varchar AS ticket_name,
          NULL::varchar AS start_pier_name,
          NULL::varchar AS end_pier_name,
          NULL::date AS business_date,
          NULL::varchar AS sale_status,
          NULL::varchar AS remark
      `,
      [
        id,
        input.ticketTypeId,
        input.productName,
        input.raftCapacity,
        input.tripType,
        input.startPierId,
        input.endPierId,
        input.windowPhone,
        input.salePrice,
        input.status,
      ],
    );

    return result.rows[0] ? normalizeRouteProductRow(result.rows[0]) : null;
  }

  async function disableRouteProduct(client, id) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE route_product
        SET status = 'DISABLED',
            updated_at = NOW()
        WHERE id = $1
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
          sale_price,
          status,
          NULL::varchar AS ticket_name,
          NULL::varchar AS start_pier_name,
          NULL::varchar AS end_pier_name,
          NULL::date AS business_date,
          NULL::varchar AS sale_status,
          NULL::varchar AS remark
      `,
      [id],
    );

    return result.rows[0] ? normalizeRouteProductRow(result.rows[0]) : null;
  }

  async function listOfflineSaleNotices(filters = {}) {
    const values = [];
    const where = [];

    if (filters.businessDate) {
      values.push(filters.businessDate);
      where.push(`osn.business_date = $${values.length}::date`);
    }

    const result = await query(
      `
        SELECT
          osn.id,
          osn.route_product_id,
          rp.product_name,
          osn.business_date,
          osn.sale_status,
          osn.updated_at,
          osn.remark
        FROM offline_sale_notice osn
        JOIN route_product rp ON rp.id = osn.route_product_id
        ${where.length ? `WHERE ${where.join(' AND ')}` : ''}
        ORDER BY osn.business_date DESC, osn.id DESC
        LIMIT 100
      `,
      values,
    );

    return result.rows.map(normalizeNoticeRow);
  }

  async function findOfflineSaleNoticeByRouteDate(client, routeProductId, businessDate) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        SELECT
          osn.id,
          osn.route_product_id,
          rp.product_name,
          osn.business_date,
          osn.sale_status,
          osn.updated_at,
          osn.remark
        FROM offline_sale_notice osn
        JOIN route_product rp ON rp.id = osn.route_product_id
        WHERE osn.route_product_id = $1
          AND osn.business_date = $2::date
        LIMIT 1
      `,
      [routeProductId, businessDate],
    );

    return result.rows[0] ? normalizeNoticeRow(result.rows[0]) : null;
  }

  async function insertOfflineSaleNotice(client, input) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        INSERT INTO offline_sale_notice (
          route_product_id,
          business_date,
          sale_status,
          updated_at,
          remark
        ) VALUES (
          $1,
          $2::date,
          $3,
          NOW(),
          $4
        )
        RETURNING
          id,
          route_product_id,
          NULL::varchar AS product_name,
          business_date,
          sale_status,
          updated_at,
          remark
      `,
      [input.routeProductId, input.businessDate, input.saleStatus, input.remark],
    );

    return result.rows[0] ? normalizeNoticeRow(result.rows[0]) : null;
  }

  async function updateOfflineSaleNotice(client, id, input) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE offline_sale_notice
        SET sale_status = $2,
            remark = $3,
            updated_at = NOW()
        WHERE id = $1
        RETURNING
          id,
          route_product_id,
          NULL::varchar AS product_name,
          business_date,
          sale_status,
          updated_at,
          remark
      `,
      [id, input.saleStatus, input.remark],
    );

    return result.rows[0] ? normalizeNoticeRow(result.rows[0]) : null;
  }

  async function closeOfflineSaleNotice(client, id) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        UPDATE offline_sale_notice
        SET sale_status = 'CLOSED',
            updated_at = NOW()
        WHERE id = $1
        RETURNING
          id,
          route_product_id,
          NULL::varchar AS product_name,
          business_date,
          sale_status,
          updated_at,
          remark
      `,
      [id],
    );

    return result.rows[0] ? normalizeNoticeRow(result.rows[0]) : null;
  }

  async function listOrdersByPhone(buyerPhone) {
    const result = await query(
      `
        SELECT
          o.id AS order_id,
          o.order_no,
          o.buyer_name,
          o.buyer_phone,
          o.order_source,
          o.order_status,
          o.payment_status,
          o.payable_amount,
          o.paid_amount,
          o.order_time,
          i.id AS order_item_id,
          i.ticket_type_id,
          tt.ticket_name,
          v.visitor_name,
          i.item_status,
          i.ticket_code,
          i.visit_date,
          i.final_price
        FROM ticket_order o
        JOIN ticket_order_item i ON i.order_id = o.id
        JOIN ticket_type tt ON tt.id = i.ticket_type_id
        LEFT JOIN visitor v ON v.id = i.visitor_id
        WHERE o.buyer_phone = $1
        ORDER BY o.order_time DESC, i.id DESC
        LIMIT 50
      `,
      [buyerPhone],
    );

    return result.rows.map(normalizeOrderSearchRow);
  }

  async function listOrdersByVisitorId(visitorId) {
    const result = await query(
      `
        SELECT
          o.id AS order_id,
          o.order_no,
          o.buyer_name,
          o.buyer_phone,
          o.order_source,
          o.order_status,
          o.payment_status,
          o.payable_amount,
          o.paid_amount,
          o.order_time,
          i.id AS order_item_id,
          i.ticket_type_id,
          tt.ticket_name,
          v.visitor_name,
          i.item_status,
          i.ticket_code,
          i.visit_date,
          i.final_price
        FROM ticket_order_item i
        JOIN ticket_order o ON o.id = i.order_id
        JOIN ticket_type tt ON tt.id = i.ticket_type_id
        LEFT JOIN visitor v ON v.id = i.visitor_id
        WHERE i.visitor_id = $1
        ORDER BY o.order_time DESC, i.id DESC
        LIMIT 50
      `,
      [visitorId],
    );

    return result.rows.map(normalizeOrderSearchRow);
  }

  async function listInventory(filters = {}) {
    const values = [];
    const where = [];

    if (filters.ticketTypeId) {
      values.push(filters.ticketTypeId);
      where.push(`tsq.ticket_type_id = $${values.length}`);
    }

    if (filters.visitDate) {
      values.push(filters.visitDate);
      where.push(`tsq.visit_date = $${values.length}::date`);
    }

    const result = await query(
      `
        SELECT
          tsq.id,
          tsq.ticket_type_id,
          tt.ticket_name,
          tsq.visit_date,
          tsq.slot_start_time,
          tsq.slot_end_time,
          tsq.quota_total,
          tsq.quota_sold,
          tsq.quota_checked_in,
          tsq.status
        FROM time_slot_quota tsq
        JOIN ticket_type tt ON tt.id = tsq.ticket_type_id
        ${where.length ? `WHERE ${where.join(' AND ')}` : ''}
        ORDER BY tsq.visit_date DESC, tsq.slot_start_time, tsq.id
        LIMIT 100
      `,
      values,
    );

    return result.rows.map((row) => ({
      id: Number(row.id),
      ticketTypeId: Number(row.ticket_type_id),
      ticketName: row.ticket_name,
      visitDate: formatDate(row.visit_date),
      slotStartTime: row.slot_start_time,
      slotEndTime: row.slot_end_time,
      quotaTotal: Number(row.quota_total),
      quotaSold: Number(row.quota_sold),
      quotaCheckedIn: Number(row.quota_checked_in),
      remainingQuota: Number(row.quota_total) - Number(row.quota_sold),
      status: row.status,
    }));
  }

  async function listOperationLogs(limit = 50) {
    const result = await query(
      `
        SELECT
          id,
          operator_id,
          module_name,
          operation_type,
          target_table,
          target_id,
          operation_result,
          request_ip,
          detail_json,
          created_at,
          operation_time
        FROM operation_log
        ORDER BY COALESCE(operation_time, created_at) DESC, id DESC
        LIMIT $1
      `,
      [limit],
    );

    return result.rows.map(normalizeOperationLogRow);
  }

  async function insertOperationLog(client, input) {
    const executor = getExecutor(client, query);
    const result = await executor(
      `
        INSERT INTO operation_log (
          operator_id,
          module_name,
          operation_type,
          target_table,
          target_id,
          operation_result,
          request_ip,
          detail_json,
          created_at,
          operation_time
        ) VALUES (
          $1,
          $2,
          $3,
          $4,
          $5,
          $6,
          $7,
          $8,
          NOW(),
          NOW()
        )
        RETURNING
          id,
          operator_id,
          module_name,
          operation_type,
          target_table,
          target_id,
          operation_result,
          request_ip,
          detail_json,
          created_at,
          operation_time
      `,
      [
        input.operatorId || 1,
        input.moduleName,
        input.operationType,
        input.targetTable,
        String(input.targetId || ''),
        input.operationResult || 'SUCCESS',
        input.requestIp || '127.0.0.1',
        input.detailJson || '{}',
      ],
    );

    return result.rows[0] ? normalizeOperationLogRow(result.rows[0]) : null;
  }

  return {
    closeOfflineSaleNotice,
    disablePier,
    disableRouteProduct,
    findVisitorById,
    findOfflineSaleNoticeByRouteDate,
    findVisitorByIdentity,
    insertOfflineSaleNotice,
    insertOperationLog,
    insertPier,
    insertRouteProduct,
    insertVisitor,
    listOfflineSaleNotices,
    listOperationLogs,
    listOrdersByPhone,
    listPiers,
    listRouteProducts,
    listVisitors,
    updateOfflineSaleNotice,
    updatePier,
    updateRouteProduct,
    withTransaction,
  };
}

module.exports = {
  createManageQuery,
};
