const express = require('express');

const { createCheckinController } = require('../controllers/checkin.controller');

function createCheckinRouter(options = {}) {
  const checkinController = options.checkinController
    || createCheckinController({ checkinService: options.checkinService });
  const authMiddleware = options.authMiddleware || {};
  const requireAdmin = authMiddleware.requireAdmin || ((_req, _res, next) => next());

  const checkinRouter = express.Router();
  checkinRouter.post('/checkins', requireAdmin, checkinController.postCheckin);

  return checkinRouter;
}

module.exports = {
  createCheckinRouter,
};
