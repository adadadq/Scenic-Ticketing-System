const test = require('node:test');
const assert = require('node:assert/strict');

const { createOrderQuery } = require('../src/db/queries/order.query');
const { createOrderService } = require('../src/services/order.service');

test('createOrderService creates an order inside a transaction', async () => {
  const calls = [];
  const orderQuery = {
    withTransaction: async (work) => work({
      query: async (sql, params) => {
        calls.push({ sql, params });
        return { rows: [] };
      },
    }),
    findTicketTypeById: async (client, ticketTypeId) => {
      calls.push({ fn: 'findTicketTypeById', ticketTypeId });
      return {
        id: ticketTypeId,
        ticketTypeId,
        ticketName: '成人票',
        productName: '双人筏-单程-妙灵洞码头→骥马码头',
        tripType: 'ONE_WAY',
        raftCapacity: 2,
        windowPhone: '19877396225',
        scenicSpotId: 1,
        salePrice: '99.00',
      };
    },
    lockTimeSlotQuota: async (client, timeSlotId, visitDate) => {
      calls.push({ fn: 'lockTimeSlotQuota', timeSlotId, visitDate });
      return {
        id: timeSlotId,
        ticketTypeId: 1,
        visitDate,
        quotaTotal: 100,
        quotaSold: 25,
      };
    },
    insertOrder: async (client, orderInput) => {
      calls.push({ fn: 'insertOrder', orderInput });
      return {
        id: 101,
        orderNo: 'ORD202605010001',
      };
    },
    insertOrderItem: async (client, itemInput) => {
      calls.push({ fn: 'insertOrderItem', itemInput });
      return {
        id: 201,
        itemNo: 'ORD202605010001-01',
        ticketCode: 'TCORD20260501000101',
      };
    },
    updateTimeSlotQuotaSold: async (client, timeSlotId, soldCount) => {
      calls.push({ fn: 'updateTimeSlotQuotaSold', timeSlotId, soldCount });
      return {
        id: timeSlotId,
        quotaSold: 26,
      };
    },
  };

  const orderService = createOrderService({
    orderQuery,
  });

  const result = await orderService.createOrder({
    buyerName: '张三',
    buyerPhone: '13800000000',
    orderSource: 'ONLINE',
    items: [
      {
        ticketTypeId: 1,
        visitorId: 1,
        timeSlotId: 1,
        visitDate: '2026-05-01',
      },
    ],
  });

  assert.deepEqual(result, {
    success: true,
    message: 'order created',
    data: {
      orderId: 101,
      orderNo: 'ORD202605010001',
      totalAmount: 99,
      itemCount: 1,
      items: [
        {
          orderItemId: 201,
          itemNo: 'ORD202605010001-01',
          ticketCode: 'TCORD20260501000101',
          ticketTypeId: 1,
          productName: '双人筏-单程-妙灵洞码头→骥马码头',
          tripType: 'ONE_WAY',
          raftCapacity: 2,
          windowPhone: '19877396225',
        },
      ],
    },
  });
  assert.equal(calls[2].fn, 'insertOrder');
  assert.equal(calls[2].orderInput.scenicSpotId, 1);
  assert.equal(calls[2].orderInput.orderStatus, 'PAID');
  assert.equal(calls[2].orderInput.paymentStatus, 'PAID');
  assert.equal(calls[0].fn, 'findTicketTypeById');
  assert.equal(calls[1].fn, 'lockTimeSlotQuota');
  assert.equal(calls[3].fn, 'insertOrderItem');
  assert.equal(calls[4].fn, 'updateTimeSlotQuotaSold');
});

test('createOrderService rejects overselling the same time slot within one order', async () => {
  let insertOrderCalled = false;

  const orderService = createOrderService({
    orderQuery: {
      withTransaction: async (work) => work({}),
      findTicketTypeById: async (_client, ticketTypeId) => ({
        id: ticketTypeId,
        ticketTypeId,
        ticketName: '成人票',
        productName: '双人筏-单程-妙灵洞码头→骥马码头',
        tripType: 'ONE_WAY',
        raftCapacity: 2,
        windowPhone: '19877396225',
        scenicSpotId: 1,
        salePrice: '99.00',
      }),
      lockTimeSlotQuota: async (_client, timeSlotId, visitDate) => ({
        id: timeSlotId,
        ticketTypeId: 1,
        visitDate,
        quotaTotal: 1,
        quotaSold: 0,
      }),
      insertOrder: async () => {
        insertOrderCalled = true;
        throw new Error('should not insert order');
      },
      insertOrderItem: async () => {
        throw new Error('should not insert item');
      },
      updateTimeSlotQuotaSold: async () => {
        throw new Error('should not update quota');
      },
    },
  });

  await assert.rejects(
    orderService.createOrder({
      buyerName: '张三',
      buyerPhone: '13800000000',
      orderSource: 'ONLINE',
      items: [
        {
          ticketTypeId: 1,
          visitorId: 1,
          timeSlotId: 1,
          visitDate: '2026-05-01',
        },
        {
          ticketTypeId: 1,
          visitorId: 2,
          timeSlotId: 1,
          visitDate: '2026-05-01',
        },
      ],
    }),
    (error) => error.name === 'AppError' && error.statusCode === 409,
  );

  assert.equal(insertOrderCalled, false);
});

test('createOrderService falls back to ticket_name when route_product mapping is missing', async () => {
  const orderService = createOrderService({
    orderQuery: {
      withTransaction: async (work) => work({}),
      findTicketTypeById: async (_client, ticketTypeId) => ({
        id: ticketTypeId,
        ticketTypeId,
        ticketName: '成人票',
        productName: '成人票',
        tripType: null,
        raftCapacity: null,
        windowPhone: null,
        scenicSpotId: 1,
        salePrice: '99.00',
      }),
      lockTimeSlotQuota: async (_client, timeSlotId, visitDate) => ({
        id: timeSlotId,
        ticketTypeId: 1,
        visitDate,
        quotaTotal: 100,
        quotaSold: 0,
      }),
      insertOrder: async () => ({
        id: 101,
        orderNo: 'ORD202605010001',
      }),
      insertOrderItem: async () => ({
        id: 201,
        itemNo: 'ORD202605010001-01',
        ticketCode: 'TCORD20260501000101',
      }),
      updateTimeSlotQuotaSold: async (_client, timeSlotId) => ({
        id: timeSlotId,
        quotaSold: 1,
      }),
    },
  });

  const result = await orderService.createOrder({
    buyerName: '张三',
    buyerPhone: '13800000000',
    orderSource: 'ONLINE',
    items: [
      {
        ticketTypeId: 1,
        visitorId: 1,
        timeSlotId: 1,
        visitDate: '2026-05-01',
      },
    ],
  });

  assert.deepEqual(result.data.items[0], {
    orderItemId: 201,
    itemNo: 'ORD202605010001-01',
    ticketCode: 'TCORD20260501000101',
    ticketTypeId: 1,
    productName: '成人票',
    tripType: null,
    raftCapacity: null,
    windowPhone: null,
  });
});

test('createOrderQuery findTicketTypeById joins route_product and normalizes scenic semantics', async () => {
  const executed = [];
  const orderQuery = createOrderQuery({
    pool: {
      query: async (sql, params) => {
        executed.push({ sql, params });
        return {
          rows: [
            {
              id: '11',
              scenic_spot_id: '1',
              ticket_name: '成人票',
              sale_price: '118.00',
              route_product_name: '双人筏-单程-妙灵洞码头→骥马码头',
              trip_type: 'ONE_WAY',
              raft_capacity: '2',
              window_phone: '19877396225',
            },
          ],
        };
      },
    },
  });

  const result = await orderQuery.findTicketTypeById(null, 11);

  assert.equal(executed.length, 1);
  assert.match(executed[0].sql, /FROM ticket_type tt/i);
  assert.match(executed[0].sql, /LEFT JOIN route_product rp ON rp\.ticket_type_id = tt\.id/i);
  assert.deepEqual(executed[0].params, [11]);
  assert.deepEqual(result, {
    id: 11,
    ticketTypeId: 11,
    scenicSpotId: 1,
    ticketName: '成人票',
    productName: '双人筏-单程-妙灵洞码头→骥马码头',
    tripType: 'ONE_WAY',
    raftCapacity: 2,
    windowPhone: '19877396225',
    salePrice: 118,
  });
});

test('createOrderService rejects missing buyerName', async () => {
  const orderService = createOrderService({
    orderQuery: {
      withTransaction: async () => {
        throw new Error('should not run transaction');
      },
    },
  });

  await assert.rejects(
    orderService.createOrder({
      buyerPhone: '13800000000',
      orderSource: 'ONLINE',
      items: [],
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createOrderService rejects empty items', async () => {
  const orderService = createOrderService({
    orderQuery: {
      withTransaction: async () => {
        throw new Error('should not run transaction');
      },
    },
  });

  await assert.rejects(
    orderService.createOrder({
      buyerName: '张三',
      buyerPhone: '13800000000',
      orderSource: 'ONLINE',
      items: [],
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createOrderService rejects insufficient time slot quota', async () => {
  const orderService = createOrderService({
    orderQuery: {
      withTransaction: async (work) => work({}),
      findTicketTypeById: async () => ({
        id: 1,
        ticketName: '成人票',
        scenicSpotId: 1,
        salePrice: '99.00',
      }),
      lockTimeSlotQuota: async () => ({
        id: 1,
        ticketTypeId: 1,
        visitDate: '2026-05-01',
        quotaTotal: 1,
        quotaSold: 1,
      }),
      insertOrder: async () => {
        throw new Error('should not insert order');
      },
      insertOrderItem: async () => {
        throw new Error('should not insert item');
      },
      updateTimeSlotQuotaSold: async () => {
        throw new Error('should not update quota');
      },
    },
  });

  await assert.rejects(
    orderService.createOrder({
      buyerName: '张三',
      buyerPhone: '13800000000',
      orderSource: 'ONLINE',
      items: [
        {
          ticketTypeId: 1,
          visitorId: 1,
          timeSlotId: 1,
          visitDate: '2026-05-01',
        },
      ],
    }),
    (error) => error.name === 'AppError' && error.statusCode === 409,
  );
});

test('createOrderService rejects mixed scenic spots in one order', async () => {
  const orderService = createOrderService({
    orderQuery: {
      withTransaction: async (work) => work({}),
      findTicketTypeById: async (_client, ticketTypeId) => ({
        id: ticketTypeId,
        ticketName: ticketTypeId === 1 ? '成人票' : '亲子票',
        scenicSpotId: ticketTypeId === 1 ? 1 : 2,
        salePrice: '99.00',
      }),
      lockTimeSlotQuota: async () => ({
        id: 1,
        ticketTypeId: 1,
        visitDate: '2026-05-01',
        quotaTotal: 100,
        quotaSold: 0,
      }),
      insertOrder: async () => {
        throw new Error('should not insert order');
      },
      insertOrderItem: async () => {
        throw new Error('should not insert item');
      },
      updateTimeSlotQuotaSold: async () => {
        throw new Error('should not update quota');
      },
    },
  });

  await assert.rejects(
    orderService.createOrder({
      buyerName: '张三',
      buyerPhone: '13800000000',
      orderSource: 'ONLINE',
      items: [
        {
          ticketTypeId: 1,
          visitorId: 1,
          timeSlotId: 1,
          visitDate: '2026-05-01',
        },
        {
          ticketTypeId: 2,
          visitorId: 1,
          timeSlotId: 1,
          visitDate: '2026-05-01',
        },
      ],
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});
