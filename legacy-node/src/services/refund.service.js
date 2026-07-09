const { AppError } = require('../utils/app-error');
const { isNonEmptyString, parsePositiveInteger } = require('../utils/validators');
const { createRefundQuery } = require('../db/queries/refund.query');

function createRefundService(options = {}) {
  const refundQuery = options.refundQuery || createRefundQuery(options);

  function validateRefundPayload(payload = {}) {
    const orderItemId = payload.orderItemId;
    const operatorId = payload.operatorId;
    const reason = payload.reason;

    if (!isNonEmptyString(reason)) {
      throw new AppError(400, 'reason is required');
    }

    return {
      orderItemId: parsePositiveInteger(orderItemId, 'orderItemId'),
      operatorId: parsePositiveInteger(operatorId, 'operatorId'),
      reason: reason.trim(),
    };
  }

  function ensureRefundQueryFunction(name) {
    if (typeof refundQuery[name] !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }
  }

  async function applyRefund(payload = {}) {
    const normalized = validateRefundPayload(payload);

    ensureRefundQueryFunction('withTransaction');
    ensureRefundQueryFunction('callApplyRefund');

    return refundQuery.withTransaction(async (client) => {
      const result = await refundQuery.callApplyRefund(
        client,
        normalized.orderItemId,
        normalized.operatorId,
        normalized.reason,
      );

      return {
        success: true,
        message: 'refund applied',
        data: {
          orderItemId: result.orderItemId,
        },
      };
    });
  }

  return {
    applyRefund,
  };
}

module.exports = {
  createRefundService,
};
