const test = require('node:test');
const assert = require('node:assert/strict');

const { createCheckinService } = require('../src/services/checkin.service');
const { createRefundService } = require('../src/services/refund.service');

test('performCheckin rejects USED ticket items', async () => {
  const checkinService = createCheckinService({
    checkinQuery: {
      withTransaction: async (work) => work({
        query: async () => ({ rows: [] }),
      }),
      findOrderItemByTicketCode: async () => ({
        id: 11,
        ticketCode: 'TC001',
        itemStatus: 'USED',
        timeSlotId: 21,
      }),
    },
  });

  await assert.rejects(
    checkinService.performCheckin({
      ticketCode: 'TC001',
      operatorId: 7,
      checkinGate: 'A1',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 409,
  );
});

test('performCheckin runs the transaction flow in order', async () => {
  const calls = [];
  const checkinService = createCheckinService({
    checkinQuery: {
      withTransaction: async (work) => work({
        query: async () => ({ rows: [] }),
      }),
      findOrderItemByTicketCode: async (client, ticketCode) => {
        calls.push({ fn: 'findOrderItemByTicketCode', ticketCode });
        return {
          id: 11,
          ticketCode,
          itemStatus: 'UNUSED',
          timeSlotId: 21,
        };
      },
      insertCheckinRecord: async (client, input) => {
        calls.push({ fn: 'insertCheckinRecord', input });
        return {
          checkinNo: 'CHK202605010001',
        };
      },
      markOrderItemUsed: async (client, orderItemId) => {
        calls.push({ fn: 'markOrderItemUsed', orderItemId });
        return {
          id: orderItemId,
          itemStatus: 'USED',
        };
      },
      incrementCheckedIn: async (client, timeSlotId) => {
        calls.push({ fn: 'incrementCheckedIn', timeSlotId });
        return {
          id: timeSlotId,
          quotaCheckedIn: 1,
        };
      },
    },
  });

  const result = await checkinService.performCheckin({
    ticketCode: 'TC001',
    operatorId: 7,
    checkinGate: 'A1',
  });

  assert.deepEqual(result, {
    success: true,
    message: 'checkin completed',
    data: {
      orderItemId: 11,
      checkinNo: 'CHK202605010001',
      itemStatus: 'USED',
      checkinGate: 'A1',
    },
  });
  assert.deepEqual(calls.map((call) => call.fn), [
    'findOrderItemByTicketCode',
    'insertCheckinRecord',
    'markOrderItemUsed',
    'incrementCheckedIn',
  ]);
  assert.equal(calls[1].input.orderItemId, 11);
  assert.equal(calls[1].input.operatorId, 7);
  assert.equal(calls[1].input.checkinResult, 'PASS');
  assert.equal(calls[1].input.checkinGate, 'A1');
});

test('insertCheckinRecord SQL omits updated_at', async () => {
  let capturedSql = '';
  const checkinQuery = require('../src/db/queries/checkin.query').createCheckinQuery({
    pool: {
      query: async (sql) => {
        capturedSql = sql;
        return {
          rows: [
            {
              order_item_id: 11,
              checkin_no: 'CHK202605010001',
              checkin_result: 'PASS',
              checkin_gate: 'A1',
            },
          ],
        };
      },
    },
  });

  await checkinQuery.insertCheckinRecord(null, {
    orderItemId: 11,
    operatorId: 7,
    checkinNo: 'CHK202605010001',
    checkinResult: 'PASS',
    checkinGate: 'A1',
  });

  assert.equal(capturedSql.includes('updated_at'), false);
});

test('applyRefund calls the stored procedure with normalized parameters', async () => {
  const calls = [];
  const refundService = createRefundService({
    refundQuery: {
      withTransaction: async (work) => work({
        query: async () => ({ rows: [] }),
      }),
      callApplyRefund: async (client, orderItemId, operatorId, reason) => {
        calls.push({ orderItemId, operatorId, reason });
        return {
          orderItemId,
        };
      },
    },
  });

  const result = await refundService.applyRefund({
    orderItemId: '19',
    operatorId: '7',
    reason: 'customer request',
  });

  assert.deepEqual(result, {
    success: true,
    message: 'refund applied',
    data: {
      orderItemId: 19,
    },
  });
  assert.deepEqual(calls, [
    {
      orderItemId: 19,
      operatorId: 7,
      reason: 'customer request',
    },
  ]);
});

test('refund service rejects missing required parameters with AppError 400', async () => {
  const refundService = createRefundService({
    refundQuery: {
      withTransaction: async () => {
        throw new Error('should not run transaction');
      },
      callApplyRefund: async () => {
        throw new Error('should not call stored procedure');
      },
    },
  });

  await assert.rejects(
    refundService.applyRefund({
      operatorId: 7,
      reason: 'customer request',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});
