const fs = require('node:fs');
const path = require('node:path');

function parseEnvFile(content) {
  const entries = {};

  for (const rawLine of content.split(/\r?\n/)) {
    const line = rawLine.trim();

    if (!line || line.startsWith('#')) {
      continue;
    }

    const equalsIndex = line.indexOf('=');
    if (equalsIndex === -1) {
      continue;
    }

    const key = line.slice(0, equalsIndex).trim();
    let value = line.slice(equalsIndex + 1).trim();

    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }

    entries[key] = value;
  }

  return entries;
}

function loadEnvFile(envPath = path.resolve(process.cwd(), '.env')) {
  if (!fs.existsSync(envPath)) {
    return {};
  }

  return parseEnvFile(fs.readFileSync(envPath, 'utf8'));
}

function parseNumber(value, fallback) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) ? numericValue : fallback;
}

function parseBoolean(value, fallback = false) {
  if (value === undefined) {
    return fallback;
  }

  const normalized = String(value).trim().toLowerCase();
  if (['1', 'true', 'yes', 'on'].includes(normalized)) {
    return true;
  }

  if (['0', 'false', 'no', 'off'].includes(normalized)) {
    return false;
  }

  return fallback;
}

function getAppConfig(options = {}) {
  const fileEnv = loadEnvFile(options.envPath);
  const env = {
    ...fileEnv,
    ...process.env,
    ...(options.env || {}),
  };

  return {
    port: parseNumber(env.PORT, 3000),
    db: {
      host: env.DB_HOST || '127.0.0.1',
      port: parseNumber(env.DB_PORT, 15432),
      database: env.DB_NAME || 'scenic_ticket_final',
      user: env.DB_USER || 'scenic_app_login',
      password: env.DB_PASSWORD || '',
      max: parseNumber(env.DB_POOL_MAX, 10),
      ssl: parseBoolean(env.DB_SSL, false),
    },
  };
}

module.exports = {
  getAppConfig,
  loadEnvFile,
};
