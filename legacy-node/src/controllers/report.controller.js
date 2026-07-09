const { sendJson } = require('../utils/response');
const { createReportService } = require('../services/report.service');

function createReportController(options = {}) {
  const reportService = options.reportService || createReportService(options);

  async function getSales(req, res, next) {
    try {
      const payload = await reportService.getSalesReport(req.query);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getOfflineSaleNotices(req, res, next) {
    try {
      const payload = await reportService.getOfflineSaleNotices(req.query);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    getSales,
    getOfflineSaleNotices,
  };
}

module.exports = {
  createReportController,
};
