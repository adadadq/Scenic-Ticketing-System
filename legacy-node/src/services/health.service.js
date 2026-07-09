const { AppError } = require('../utils/app-error');
const unavailablePingDatabase = async () => {
  throw new AppError(503, 'database is unavailable');
};

function createHealthService(options = {}) {
  const pingDatabase = options.pingDatabase || unavailablePingDatabase;

  async function getServiceHealth() {
    return {
      success: true,
      message: 'service is running',
    };
  }

  async function getDatabaseHealth() {
    try {
      const isHealthy = await pingDatabase();
      if (!isHealthy) {
        throw new Error('database ping returned false');
      }

      return {
        success: true,
        message: 'database is running',
      };
    } catch (error) {
      throw new AppError(503, 'database is unavailable', { cause: error });
    }
  }

  return {
    getDatabaseHealth,
    getServiceHealth,
  };
}

module.exports = {
  createHealthService,
};
