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

function normalizeVisitorRow(row) {
  return {
    id: Number(row.id),
    visitorName: row.visitor_name,
    idType: row.id_type,
    idNumber: row.id_number,
    phone: row.phone || null,
    gender: row.gender || null,
    birthDate: formatDateInAsiaShanghai(row.birth_date),
  };
}

function normalizeVisitorOrderRow(row) {
  return {
    orderId: Number(row.order_id),
    orderNo: row.order_no,
    orderStatus: row.order_status,
    paymentStatus: row.payment_status,
    orderSource: row.order_source,
    buyerName: row.buyer_name,
    buyerPhone: row.buyer_phone,
    totalAmount: Number(row.total_amount),
    discountAmount: Number(row.discount_amount),
    payableAmount: Number(row.payable_amount),
    paidAmount: Number(row.paid_amount),
    orderTime: formatDateInAsiaShanghai(row.order_time),
    paidAt: formatDateInAsiaShanghai(row.paid_at),
    cancelTime: formatDateInAsiaShanghai(row.cancel_time),
    orderItemId: Number(row.order_item_id),
    itemNo: row.item_no,
    ticketCode: row.ticket_code,
    visitDate: formatDateInAsiaShanghai(row.visit_date),
    originalPrice: Number(row.original_price),
    itemDiscountAmount: Number(row.item_discount_amount),
    finalPrice: Number(row.final_price),
    itemStatus: row.item_status,
    ticketTypeId: Number(row.ticket_type_id),
    ticketName: row.ticket_name,
    productName: row.product_name || row.ticket_name,
    tripType: row.trip_type || null,
    windowPhone: row.window_phone || null,
  };
}

function createVisitorQuery(options = {}) {
  const pool = options.pool || options.dbPool || createDbPool(options);
  const query = createQueryExecutor(pool);

  async function findVisitorById(visitorId) {
    const result = await query(
      `
        SELECT
          id,
          visitor_name,
          id_type,
          id_number,
          phone,
          gender,
          birth_date
        FROM visitor
        WHERE id = $1
        LIMIT 1
      `,
      [visitorId],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function findVisitorByIdentity(idType, idNumber) {
    const result = await query(
      `
        SELECT
          id,
          visitor_name,
          id_type,
          id_number,
          phone,
          gender,
          birth_date
        FROM visitor
        WHERE id_type = $1
          AND id_number = $2
        LIMIT 1
      `,
      [idType, idNumber],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function findVisitorByPhone(phone) {
    const result = await query(
      `
        SELECT
          id,
          visitor_name,
          id_type,
          id_number,
          phone,
          gender,
          birth_date
        FROM visitor
        WHERE phone = $1
        LIMIT 1
      `,
      [phone],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function insertVisitor(visitorInput) {
    const result = await query(
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
        RETURNING
          id,
          visitor_name,
          id_type,
          id_number,
          phone,
          gender,
          birth_date
      `,
      [
        visitorInput.visitorName,
        visitorInput.idType,
        visitorInput.idNumber,
        visitorInput.phone,
        visitorInput.gender,
        visitorInput.birthDate,
      ],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function updateVisitorByIdentity(visitorInput) {
    const result = await query(
      `
        UPDATE visitor
        SET visitor_name = $3,
            phone = $4,
            gender = $5,
            birth_date = $6::date,
            updated_at = NOW()
        WHERE id_type = $1
          AND id_number = $2
        RETURNING
          id,
          visitor_name,
          id_type,
          id_number,
          phone,
          gender,
          birth_date
      `,
      [
        visitorInput.idType,
        visitorInput.idNumber,
        visitorInput.visitorName,
        visitorInput.phone,
        visitorInput.gender,
        visitorInput.birthDate,
      ],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function updateVisitorByPhone(visitorInput) {
    const result = await query(
      `
        UPDATE visitor
        SET visitor_name = $2,
            id_type = $3,
            id_number = $4,
            gender = $5,
            birth_date = $6::date,
            updated_at = NOW()
        WHERE phone = $1
        RETURNING
          id,
          visitor_name,
          id_type,
          id_number,
          phone,
          gender,
          birth_date
      `,
      [
        visitorInput.phone,
        visitorInput.visitorName,
        visitorInput.idType,
        visitorInput.idNumber,
        visitorInput.gender,
        visitorInput.birthDate,
      ],
    );

    return result.rows[0] ? normalizeVisitorRow(result.rows[0]) : null;
  }

  async function listOrdersByVisitorId(visitorId) {
    const result = await query(
      `
        SELECT
          o.id AS order_id,
          o.order_no,
          o.order_status,
          o.payment_status,
          o.order_source,
          o.buyer_name,
          o.buyer_phone,
          o.total_amount,
          o.discount_amount,
          o.payable_amount,
          o.paid_amount,
          o.order_time,
          o.paid_at,
          o.cancel_time,
          toi.id AS order_item_id,
          toi.item_no,
          toi.ticket_code,
          toi.visit_date,
          toi.original_price,
          toi.discount_amount AS item_discount_amount,
          toi.final_price,
          toi.item_status,
          tt.id AS ticket_type_id,
          tt.ticket_name,
          rp.product_name,
          rp.trip_type,
          rp.window_phone
        FROM ticket_order_item toi
        JOIN ticket_order o ON o.id = toi.order_id
        JOIN ticket_type tt ON tt.id = toi.ticket_type_id
        LEFT JOIN route_product rp ON rp.ticket_type_id = tt.id
        WHERE toi.visitor_id = $1
        ORDER BY o.order_time DESC, o.id DESC, toi.id DESC
      `,
      [visitorId],
    );

    return result.rows.map(normalizeVisitorOrderRow);
  }

  return {
    findVisitorById,
    findVisitorByIdentity,
    findVisitorByPhone,
    insertVisitor,
    listOrdersByVisitorId,
    updateVisitorByPhone,
    updateVisitorByIdentity,
  };
}

module.exports = {
  createVisitorQuery,
  normalizeVisitorOrderRow,
  normalizeVisitorRow,
};
