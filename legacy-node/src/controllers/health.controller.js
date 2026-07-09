const { sendJson } = require('../utils/response');
const { createHealthService } = require('../services/health.service');

function createHealthController(options = {}) {
  const healthService = options.healthService || createHealthService(options);

  async function getHealth(_req, res, next) {
    try {
      const payload = await healthService.getServiceHealth();
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getDbHealth(_req, res, next) {
    try {
      const payload = await healthService.getDatabaseHealth();
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    getDbHealth,
    getHealth,
  };
}

module.exports = {
  createHealthController,
};
