const { sendJson } = require('../utils/response');

function notFoundMiddleware(_req, res) {
  sendJson(res, 404, {
    success: false,
    message: 'Not Found',
  });
}

module.exports = {
  notFoundMiddleware,
};
