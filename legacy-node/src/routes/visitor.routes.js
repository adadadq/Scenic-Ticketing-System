const express = require('express');

const { createVisitorController } = require('../controllers/visitor.controller');

function createVisitorRouter(options = {}) {
  const visitorController = options.visitorController
    || createVisitorController({ visitorService: options.visitorService, authService: options.authService });
  const authMiddleware = options.authMiddleware || {};
  const requireSession = authMiddleware.requireSession || ((_req, _res, next) => next());

  const visitorRouter = express.Router();
  visitorRouter.post('/visitors', visitorController.postVisitor);
  visitorRouter.get('/visitors/:visitorId/orders', requireSession, visitorController.getVisitorOrders);
  visitorRouter.get('/visitors/:visitorId', requireSession, visitorController.getVisitor);

  return visitorRouter;
}

module.exports = {
  createVisitorRouter,
};
