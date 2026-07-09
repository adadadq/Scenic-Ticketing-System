class AppError extends Error {
  constructor(statusCode, message, options = {}) {
    super(message, options);
    this.name = 'AppError';
    this.statusCode = statusCode;
  }
}

module.exports = {
  AppError,
};
