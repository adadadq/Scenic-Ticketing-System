const express = require('express');

const { createRefundController } = require('../controllers/refund.controller');

function createRefundRouter(options = {}) {
  const refundController = options.refundController
    || createRefundController({ refundService: options.refundService });
  const authMiddleware = options.authMiddleware || {};
  const requireAdmin = authMiddleware.requireAdmin || ((_req, _res, next) => next());

  const refundRouter = express.Router();
  refundRouter.post('/refunds', requireAdmin, refundController.postRefund);

  return refundRouter;
}

module.exports = {
  createRefundRouter,
};
