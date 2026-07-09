const { AppError } = require('../utils/app-error');
const { parseDateString, parsePositiveInteger } = require('../utils/validators');
const { createReportQuery, formatBusinessDate } = require('../db/queries/report.query');

function normalizeSalesReportItem(item) {
  return {
    ticketTypeId: Number(item.ticketTypeId),
    visitDate: formatBusinessDate(item.visitDate),
    soldCount: Number(item.soldCount),
    soldAmount: Number(item.soldAmount),
  };
}

function normalizeOfflineSaleNoticeItem(item) {
  return {
    routeProductId: Number(item.routeProductId),
    ticketTypeId: Number(item.ticketTypeId),
    productName: item.productName,
    businessDate: formatBusinessDate(item.businessDate),
    saleStatus: item.saleStatus,
    tripType: item.tripType,
    windowPhone: item.windowPhone,
    remark: item.remark,
  };
}

function createReportService(options = {}) {
  const reportQuery = options.reportQuery || createReportQuery(options);

  function validateSalesFilters(filters = {}) {
    const ticketTypeId = parsePositiveInteger(filters.ticketTypeId, 'ticketTypeId');
    const startDate = parseDateString(filters.startDate, 'startDate');
    const endDate = parseDateString(filters.endDate, 'endDate');

    if (startDate > endDate) {
      throw new AppError(400, 'startDate must be less than or equal to endDate');
    }

    return {
      ticketTypeId,
      startDate,
      endDate,
    };
  }

  function ensureReportQueryFunction(name) {
    if (typeof reportQuery[name] !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }
  }

  async function getSalesReport(filters = {}) {
    const normalized = validateSalesFilters(filters);
    ensureReportQueryFunction('fetchSalesReport');

    const items = (await reportQuery.fetchSalesReport(normalized)).map(normalizeSalesReportItem);

    return {
      success: true,
      message: 'sales report loaded',
      data: {
        items,
        ticketTypeId: normalized.ticketTypeId,
        startDate: normalized.startDate,
        endDate: normalized.endDate,
      },
    };
  }

  async function getOfflineSaleNotices(filters = {}) {
    const businessDate = parseDateString(filters.businessDate, 'businessDate');
    ensureReportQueryFunction('fetchOfflineSaleNotices');

    const data = (await reportQuery.fetchOfflineSaleNotices({ businessDate }))
      .map(normalizeOfflineSaleNoticeItem);

    return {
      success: true,
      message: 'offline sale notices loaded',
      data,
    };
  }

  return {
    getSalesReport,
    getOfflineSaleNotices,
  };
}

module.exports = {
  createReportService,
};
