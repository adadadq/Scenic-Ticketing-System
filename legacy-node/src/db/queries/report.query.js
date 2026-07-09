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

function formatBusinessDate(value) {
  if (!(value instanceof Date)) {
    return value;
  }

  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(value);
  const values = Object.fromEntries(
    parts
      .filter((part) => part.type !== 'literal')
      .map((part) => [part.type, part.value]),
  );

  return `${values.year}-${values.month}-${values.day}`;
}

function normalizeSalesReportRow(row) {
  return {
    ticketTypeId: Number(row.ticket_type_id),
    visitDate: formatBusinessDate(row.visit_date),
    soldCount: Number(row.sold_count),
    soldAmount: Number(row.sold_amount),
  };
}

function normalizeOfflineSaleNoticeRow(row) {
  return {
    routeProductId: Number(row.route_product_id),
    ticketTypeId: Number(row.ticket_type_id),
    productName: row.product_name,
    businessDate: formatBusinessDate(row.business_date),
    saleStatus: row.sale_status,
    tripType: row.trip_type,
    windowPhone: row.window_phone,
    remark: row.remark,
  };
}

function createReportQuery(options = {}) {
  const pool = options.pool || options.dbPool || createDbPool(options);
  const query = createQueryExecutor(pool);

  async function fetchSalesReport(filters = {}) {
    const result = await query(
      `
        SELECT
          toi.ticket_type_id AS ticket_type_id,
          toi.visit_date AS visit_date,
          COUNT(*) AS sold_count,
          SUM(toi.final_price)::numeric AS sold_amount
        FROM ticket_order_item toi
        WHERE toi.ticket_type_id = $1
          AND toi.visit_date BETWEEN $2::date AND $3::date
          AND toi.item_status IN ('UNUSED', 'USED')
        GROUP BY toi.ticket_type_id, toi.visit_date
        ORDER BY toi.visit_date ASC
      `,
      [filters.ticketTypeId, filters.startDate, filters.endDate],
    );

    return result.rows.map(normalizeSalesReportRow);
  }

  async function fetchOfflineSaleNotices(filters = {}) {
    const result = await query(
      `
        SELECT
          rp.id AS route_product_id,
          rp.ticket_type_id,
          rp.product_name,
          COALESCE(osn.business_date, $1::date) AS business_date,
          COALESCE(osn.sale_status, 'UNCONFIGURED') AS sale_status,
          rp.trip_type,
          rp.window_phone,
          osn.remark
        FROM route_product rp
        LEFT JOIN offline_sale_notice osn
          ON osn.route_product_id = rp.id
         AND osn.business_date = $1::date
        WHERE rp.status = 'ENABLED'
        ORDER BY rp.id
      `,
      [filters.businessDate],
    );

    return result.rows.map(normalizeOfflineSaleNoticeRow);
  }

  return {
    fetchSalesReport,
    fetchOfflineSaleNotices,
  };
}

module.exports = {
  createReportQuery,
  formatBusinessDate,
  normalizeOfflineSaleNoticeRow,
  normalizeSalesReportRow,
};
