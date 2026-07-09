const { sendJson } = require('../utils/response');
const { createRefundService } = require('../services/refund.service');

function createRefundController(options = {}) {
  const refundService = options.refundService || createRefundService(options);

  async function postRefund(req, res, next) {
    try {
      const payload = await refundService.applyRefund(req.body);
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    postRefund,
  };
}

module.exports = {
  createRefundController,
};
