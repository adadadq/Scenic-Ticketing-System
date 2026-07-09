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

function normalizeAdminRow(row) {
  return {
    id: Number(row.id),
    username: row.username,
    displayName: row.display_name,
    phone: row.phone || null,
    passwordHash: row.password_hash,
    status: row.status,
  };
}

function createAuthQuery(options = {}) {
  const pool = options.pool || options.dbPool || createDbPool(options);
  const query = createQueryExecutor(pool);

  async function findAdminByUsername(username) {
    const result = await query(
      `
        SELECT
          id,
          username,
          display_name,
          phone,
          password_hash,
          status
        FROM admin_user
        WHERE username = $1
        LIMIT 1
      `,
      [username],
    );

    return result.rows[0] ? normalizeAdminRow(result.rows[0]) : null;
  }

  return {
    findAdminByUsername,
  };
}

module.exports = {
  createAuthQuery,
  normalizeAdminRow,
};
