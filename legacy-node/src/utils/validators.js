const { AppError } = require('./app-error');

function isNonEmptyString(value) {
  return typeof value === 'string' && value.trim() !== '';
}

function parsePositiveInteger(value, fieldName) {
  const parsed = Number(value);

  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new AppError(400, `${fieldName} must be a positive integer`);
  }

  return parsed;
}

function parseDateString(value, fieldName) {
  if (!isNonEmptyString(value)) {
    throw new AppError(400, `${fieldName} must be a valid date in YYYY-MM-DD format`);
  }

  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new AppError(400, `${fieldName} must be a valid date in YYYY-MM-DD format`);
  }

  const date = new Date(`${value}T00:00:00.000Z`);
  if (Number.isNaN(date.getTime())) {
    throw new AppError(400, `${fieldName} must be a valid date in YYYY-MM-DD format`);
  }

  const [year, month, day] = value.split('-').map(Number);
  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() + 1 !== month ||
    date.getUTCDate() !== day
  ) {
    throw new AppError(400, `${fieldName} must be a valid date in YYYY-MM-DD format`);
  }

  return value;
}

module.exports = {
  isNonEmptyString,
  parseDateString,
  parsePositiveInteger,
};
