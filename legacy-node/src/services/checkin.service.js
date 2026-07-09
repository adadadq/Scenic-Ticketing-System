const crypto = require('node:crypto');
const { AppError } = require('../utils/app-error');
const { isNonEmptyString, parsePositiveInteger } = require('../utils/validators');
const { createCheckinQuery } = require('../db/queries/checkin.query');

function generateCheckinNo() {
  const now = new Date();
  const timestamp = now.toISOString().replace(/[-:TZ.]/g, '');
  const randomSuffix = crypto.randomBytes(4).toString('hex').toUpperCase();

  return `CHK${timestamp}${randomSuffix}`;
}

function createCheckinService(options = {}) {
  const checkinQuery = options.checkinQuery || createCheckinQuery(options);

  function validateCheckinPayload(payload = {}) {
    const ticketCode = payload.ticketCode;
    const operatorId = payload.operatorId;
    const checkinGate = payload.checkinGate;

    if (!isNonEmptyString(ticketCode)) {
      throw new AppError(400, 'ticketCode is required');
    }

    if (!isNonEmptyString(checkinGate)) {
      throw new AppError(400, 'checkinGate is required');
    }

    return {
      ticketCode: ticketCode.trim(),
      operatorId: parsePositiveInteger(operatorId, 'operatorId'),
      checkinGate: checkinGate.trim(),
    };
  }

  function ensureCheckinQueryFunction(name) {
    if (typeof checkinQuery[name] !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }
  }

  async function performCheckin(payload = {}) {
    const normalized = validateCheckinPayload(payload);

    ensureCheckinQueryFunction('withTransaction');
    ensureCheckinQueryFunction('findOrderItemByTicketCode');

    return checkinQuery.withTransaction(async (client) => {
      const orderItem = await checkinQuery.findOrderItemByTicketCode(client, normalized.ticketCode);
      if (!orderItem) {
        throw new AppError(404, 'ticket not found');
      }

      if (orderItem.itemStatus === 'USED') {
        throw new AppError(409, 'ticket already used');
      }

      if (orderItem.itemStatus === 'REFUNDED' || orderItem.itemStatus === 'CANCELLED') {
        throw new AppError(409, 'ticket cannot be checked in');
      }

      ensureCheckinQueryFunction('insertCheckinRecord');
      ensureCheckinQueryFunction('markOrderItemUsed');
      ensureCheckinQueryFunction('incrementCheckedIn');

      const checkinNo = generateCheckinNo();
      const checkinRecord = await checkinQuery.insertCheckinRecord(client, {
        orderItemId: orderItem.id,
        operatorId: normalized.operatorId,
        checkinNo,
        checkinResult: 'PASS',
        checkinGate: normalized.checkinGate,
      });

      if (!checkinRecord) {
        throw new AppError(500, 'failed to create checkin record');
      }

      const updatedItem = await checkinQuery.markOrderItemUsed(client, orderItem.id);
      if (!updatedItem) {
        throw new AppError(500, 'failed to update ticket item');
      }

      const quotaUpdate = await checkinQuery.incrementCheckedIn(client, orderItem.timeSlotId);
      if (!quotaUpdate) {
        throw new AppError(500, 'failed to update time slot quota');
      }

      return {
        success: true,
        message: 'checkin completed',
        data: {
          orderItemId: orderItem.id,
          checkinNo: checkinRecord.checkinNo,
          itemStatus: updatedItem.itemStatus,
          checkinGate: normalized.checkinGate,
        },
      };
    });
  }

  return {
    performCheckin,
  };
}

module.exports = {
  createCheckinService,
};
