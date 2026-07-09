const http = require('node:http');

const { createApp } = require('./app');
const { createDbPool, createPingDatabase, closeDbPool } = require('./config/db');
const { getAppConfig } = require('./config/env');
const { createHealthService } = require('./services/health.service');

function createServer(options = {}) {
  const { port } = getAppConfig(options);
  const dbPool = options.dbPool || createDbPool(options);
  const pingDatabase = options.pingDatabase || createPingDatabase(dbPool);
  const healthService = options.healthService || createHealthService({ pingDatabase });
  const app = createApp({ ...options, healthService, authRequired: true });
  const server = http.createServer(app);

  async function close() {
    await Promise.all([
      new Promise((resolve) => server.close(resolve)),
      closeDbPool(dbPool),
    ]);
  }

  return {
    app,
    close,
    dbPool,
    healthService,
    port,
    server,
  };
}

function startServer(options = {}) {
  const { port, server } = createServer(options);

  server.listen(port, () => {
    console.log(`Server listening on port ${port}`);
  });

  return server;
}

if (require.main === module) {
  startServer();
}

module.exports = {
  createServer,
  startServer,
};
