const { Pool } = require('pg');

const { getAppConfig } = require('./env');

function createDbPool(options = {}) {
  const { db } = getAppConfig(options);
  const poolConfig = {
    host: db.host,
    port: db.port,
    database: db.database,
    user: db.user,
    password: db.password,
    max: db.max,
    allowExitOnIdle: true,
  };

  if (db.ssl) {
    poolConfig.ssl = { rejectUnauthorized: false };
  }

  return new Pool(poolConfig);
}

function createPingDatabase(pool) {
  return async function pingDatabase() {
    const result = await pool.query('SELECT 1 AS ok');
    return Boolean(result.rows[0] && Number(result.rows[0].ok) === 1);
  };
}

async function pingDatabase(pool) {
  const result = await pool.query('SELECT 1 AS ok');
  return Boolean(result.rows[0] && Number(result.rows[0].ok) === 1);
}

async function closeDbPool(pool) {
  if (!pool) {
    return;
  }

  await pool.end();
}

module.exports = {
  closeDbPool,
  createDbPool,
  createPingDatabase,
  pingDatabase,
};
