const express = require('express');

const { createOrderController } = require('../controllers/order.controller');

function createOrderRouter(options = {}) {
  const orderController = options.orderController
    || createOrderController({ orderService: options.orderService });
  const authMiddleware = options.authMiddleware || {};
  const requireRegisteredVisitor = authMiddleware.requireRegisteredVisitor || ((_req, _res, next) => next());

  const orderRouter = express.Router();
  orderRouter.post('/orders', requireRegisteredVisitor, orderController.createOrder);

  return orderRouter;
}

module.exports = {
  createOrderRouter,
};
