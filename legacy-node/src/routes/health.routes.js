const express = require('express');

const { createHealthController } = require('../controllers/health.controller');

function createHealthRouter(options = {}) {
  const healthController = options.healthController
    || createHealthController({ healthService: options.healthService });

  const healthRouter = express.Router();
  healthRouter.get('/health', healthController.getHealth);
  healthRouter.get('/db/health', healthController.getDbHealth);

  return healthRouter;
}

module.exports = {
  createHealthRouter,
};
