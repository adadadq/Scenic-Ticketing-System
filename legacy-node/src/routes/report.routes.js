const express = require('express');

const { createReportController } = require('../controllers/report.controller');

function createReportRouter(options = {}) {
  const reportController = options.reportController
    || createReportController({ reportService: options.reportService });
  const authMiddleware = options.authMiddleware || {};
  const requireSession = authMiddleware.requireSession || ((_req, _res, next) => next());
  const requireAdmin = authMiddleware.requireAdmin || ((_req, _res, next) => next());

  const reportRouter = express.Router();
  reportRouter.get('/reports/sales', requireAdmin, reportController.getSales);
  reportRouter.get('/reports/offline-sale-notices', requireSession, reportController.getOfflineSaleNotices);

  return reportRouter;
}

module.exports = {
  createReportRouter,
};
