const { AppError } = require('../../utils/app-error');
const { createDbPool } = require('../../config/db');

function unavailableQuery() {
  throw new AppError(503, 'database is unavailable');
}

function createQueryExecutor(pool) {
  if (!pool || typeof pool.query !== 'function') {
    return unavailableQuery;
  }

  return (sql, params) => pool.query(sql, params);
}

function getExecutor(client, fallbackQuery) {
  if (client && typeof client.query === 'function') {
    return client.query.bind(client);
  }

  return fallbackQuery;
}

function createRefundQuery(options = {}) {
  const pool = options.pool || options.dbPool || createDbPool(options);
  const query = createQueryExecutor(pool);

  async function withTransaction(work) {
    if (!pool || typeof pool.connect !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const client = await pool.connect();

    try {
      await client.query('BEGIN');
      const result = await work(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      try {
        await client.query('ROLLBACK');
      } catch (_rollbackError) {
        // ignore rollback failures so the original error surfaces
      }
      throw error;
    } finally {
      if (typeof client.release === 'function') {
        client.release();
      }
    }
  }

  async function callApplyRefund(client, orderItemId, operatorId, reason) {
    const executor = getExecutor(client, query);
    await executor(
      'CALL sp_apply_refund($1, $2, $3)',
      [orderItemId, operatorId, reason],
    );

    return {
      orderItemId,
    };
  }

  return {
    callApplyRefund,
    withTransaction,
  };
}

module.exports = {
  createRefundQuery,
};
