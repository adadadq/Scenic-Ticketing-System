const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');

const { createApp } = require('../src/app');
const { createTicketQuery } = require('../src/db/queries/ticket.query');
const { createTicketService } = require('../src/services/ticket.service');

test('createTicketService returns ticket types from the query layer', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTicketTypes: async () => [
        {
          id: 1,
          scenicSpotId: 2,
          ticketName: '成人票',
          ticketCategory: 'STANDARD',
          originalPrice: '120.00',
          salePrice: '99.00',
          description: 'desc',
          refundRule: 'rule',
          isRealNameRequired: true,
          status: 'ACTIVE',
        },
      ],
    },
  });

  const result = await ticketService.getTicketTypes();

  assert.deepEqual(result, {
    success: true,
    message: 'ticket types retrieved',
    data: [
      {
        id: 1,
        scenicSpotId: 2,
        ticketName: '成人票',
        ticketCategory: 'STANDARD',
        originalPrice: '120.00',
        salePrice: '99.00',
        description: 'desc',
        refundRule: 'rule',
        isRealNameRequired: true,
        status: 'ACTIVE',
      },
    ],
  });
});

test('createTicketService returns time slots for ticket type and date', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTimeSlotsByTicketTypeAndDate: async () => [
        {
          id: 9,
          ticketTypeId: 1,
          visitDate: '2026-05-01',
          slotStartTime: '09:00:00',
          slotEndTime: '10:00:00',
          quotaTotal: 100,
          quotaSold: 25,
          quotaCheckedIn: 10,
          status: 'ACTIVE',
        },
      ],
    },
  });

  const result = await ticketService.getTimeSlots({
    ticketTypeId: '1',
    visitDate: '2026-05-01',
  });

  assert.deepEqual(result, {
    success: true,
    message: 'time slots retrieved',
    data: [
      {
        id: 9,
        ticketTypeId: 1,
        visitDate: '2026-05-01',
        slotStartTime: '09:00:00',
        slotEndTime: '10:00:00',
        quotaTotal: 100,
        quotaSold: 25,
        quotaCheckedIn: 10,
        remainingQuota: 75,
        status: 'ACTIVE',
      },
    ],
  });
});

test('createTicketService formats time slot dates in Asia/Shanghai', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTimeSlotsByTicketTypeAndDate: async () => [
        {
          id: 9,
          ticketTypeId: 1,
          visitDate: new Date('2026-05-04T16:00:00.000Z'),
          slotStartTime: '09:00:00',
          slotEndTime: '10:00:00',
          quotaTotal: 100,
          quotaSold: 25,
          quotaCheckedIn: 10,
          status: 'ACTIVE',
        },
      ],
    },
  });

  const result = await ticketService.getTimeSlots({
    ticketTypeId: '1',
    visitDate: '2026-05-05',
  });

  assert.equal(result.data[0].visitDate, '2026-05-05');
});

test('createTicketService returns yulong route products', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findRouteProducts: async () => [
        {
          id: 1,
          ticketTypeId: 11,
          productName: '双人筏-单程-妙灵洞码头→骥马码头',
          tripType: 'ONE_WAY',
          raftCapacity: 2,
          windowPhone: '19877396225',
          saleStatus: 'ON_SALE',
        },
      ],
    },
  });

  const result = await ticketService.getRouteProducts();

  assert.deepEqual(result, {
    success: true,
    message: 'route products loaded',
    data: [
      {
        id: 1,
        ticketTypeId: 11,
        productName: '双人筏-单程-妙灵洞码头→骥马码头',
        tripType: 'ONE_WAY',
        raftCapacity: 2,
        windowPhone: '19877396225',
        saleStatus: 'ON_SALE',
      },
    ],
  });
});

test('createTicketService rejects invalid ticketTypeId', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTimeSlotsByTicketTypeAndDate: async () => [],
    },
  });

  await assert.rejects(
    ticketService.getTimeSlots({
      ticketTypeId: 'abc',
      visitDate: '2026-05-01',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createTicketService rejects zero ticketTypeId', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTimeSlotsByTicketTypeAndDate: async () => [],
    },
  });

  await assert.rejects(
    ticketService.getTimeSlots({
      ticketTypeId: '0',
      visitDate: '2026-05-01',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createTicketService rejects negative ticketTypeId', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTimeSlotsByTicketTypeAndDate: async () => [],
    },
  });

  await assert.rejects(
    ticketService.getTimeSlots({
      ticketTypeId: '-3',
      visitDate: '2026-05-01',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createTicketService rejects invalid visitDate', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTimeSlotsByTicketTypeAndDate: async () => [],
    },
  });

  await assert.rejects(
    ticketService.getTimeSlots({
      ticketTypeId: '1',
      visitDate: '2026-02-31',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createTicketService rejects missing ticket query dependencies', async () => {
  const ticketService = createTicketService({
    ticketQuery: {},
  });

  await assert.rejects(
    ticketService.getTicketTypes(),
    (error) => error.name === 'AppError' && error.statusCode === 503,
  );
});

test('createTicketService rejects missing time slot query dependency', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTicketTypes: async () => [],
    },
  });

  await assert.rejects(
    ticketService.getTimeSlots({
      ticketTypeId: '1',
      visitDate: '2026-05-01',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 503,
  );
});

test('createTicketService rejects non-function time slot query dependency', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findTimeSlotsByTicketTypeAndDate: true,
    },
  });

  await assert.rejects(
    ticketService.getTimeSlots({
      ticketTypeId: '1',
      visitDate: '2026-05-01',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 503,
  );
});

test('createTicketQuery rejects non-function pool query dependency through service access', async () => {
  const ticketQuery = createTicketQuery({
    pool: {},
  });
  const ticketService = createTicketService({ ticketQuery });

  await assert.rejects(
    ticketService.getTicketTypes(),
    (error) => error.name === 'AppError' && error.statusCode === 503,
  );
});

test('createTicketQuery rejects non-function pool query dependency for time slots', async () => {
  const ticketQuery = createTicketQuery({
    pool: {
      query: 'not-a-function',
    },
  });
  const ticketService = createTicketService({ ticketQuery });

  await assert.rejects(
    ticketService.getTimeSlots({
      ticketTypeId: '1',
      visitDate: '2026-05-01',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 503,
  );
});

test('createTicketQuery returns route products with yulong route fields', async () => {
  let capturedSql = '';

  const ticketQuery = createTicketQuery({
    pool: {
      query: async (sql) => {
        capturedSql = sql;

        return {
          rows: [
            {
              id: '1',
              ticket_type_id: '11',
              product_name: '双人筏-单程-妙灵洞码头→骥马码头',
              trip_type: 'ONE_WAY',
              raft_capacity: '2',
              window_phone: '19877396225',
              sale_status: 'ON_SALE',
            },
          ],
        };
      },
    },
  });

  const rows = await ticketQuery.findRouteProducts();

  assert.match(capturedSql, /FROM route_product rp/);
  assert.match(capturedSql, /LEFT JOIN offline_sale_notice osn/);
  assert.doesNotMatch(capturedSql, /rp\.sale_status/);
  assert.match(capturedSql, /COALESCE\(osn\.sale_status,\s*'UNCONFIGURED'\)/);
  assert.deepEqual(rows, [
    {
      id: 1,
      ticketTypeId: 11,
      productName: '双人筏-单程-妙灵洞码头→骥马码头',
      tripType: 'ONE_WAY',
      raftCapacity: 2,
      windowPhone: '19877396225',
      saleStatus: 'ON_SALE',
    },
  ]);
});

test('createTicketQuery returns UNCONFIGURED when current-day notice is absent', async () => {
  const ticketQuery = createTicketQuery({
    pool: {
      query: async () => ({
        rows: [
          {
            id: '2',
            ticket_type_id: '12',
            product_name: '四人筏-往返-金龙桥码头→旧县码头',
            trip_type: 'ROUND_TRIP',
            raft_capacity: '4',
            window_phone: '19800001111',
            sale_status: 'UNCONFIGURED',
          },
        ],
      }),
    },
  });

  const rows = await ticketQuery.findRouteProducts();

  assert.deepEqual(rows, [
    {
      id: 2,
      ticketTypeId: 12,
      productName: '四人筏-往返-金龙桥码头→旧县码头',
      tripType: 'ROUND_TRIP',
      raftCapacity: 4,
      windowPhone: '19800001111',
      saleStatus: 'UNCONFIGURED',
    },
  ]);
});

test('GET /api/route-products forwards request to ticket service', async () => {
  let called = false;

  const app = createApp({
    ticketService: {
      getTicketTypes: async () => ({ success: true, message: 'noop', data: [] }),
      getTimeSlots: async () => ({ success: true, message: 'noop', data: [] }),
      getRouteProducts: async () => {
        called = true;

        return {
          success: true,
          message: 'route products loaded',
          data: [
            {
              id: 1,
              ticketTypeId: 11,
              productName: '双人筏-单程-妙灵洞码头→骥马码头',
              tripType: 'ONE_WAY',
              raftCapacity: 2,
              windowPhone: '19877396225',
              saleStatus: 'ON_SALE',
            },
          ],
        };
      },
    },
  });
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/route-products`);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.equal(called, true);
    assert.deepEqual(body, {
      success: true,
      message: 'route products loaded',
      data: [
        {
          id: 1,
          ticketTypeId: 11,
          productName: '双人筏-单程-妙灵洞码头→骥马码头',
          tripType: 'ONE_WAY',
          raftCapacity: 2,
          windowPhone: '19877396225',
          saleStatus: 'ON_SALE',
        },
      ],
    });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('createTicketService returns piers for admin management', async () => {
  const ticketService = createTicketService({
    ticketQuery: {
      findPiers: async () => [
        {
          id: 1,
          scenicSpotId: 1,
          pierName: '妙灵洞码头',
          pierType: 'DEPARTURE',
          contactPhone: '400-800-8888',
          status: 'ENABLED',
          sortNo: 1,
        },
      ],
    },
  });

  const result = await ticketService.getPiers();

  assert.deepEqual(result, {
    success: true,
    message: 'piers retrieved',
    data: [
      {
        id: 1,
        scenicSpotId: 1,
        pierName: '妙灵洞码头',
        pierType: 'DEPARTURE',
        contactPhone: '400-800-8888',
        status: 'ENABLED',
        sortNo: 1,
      },
    ],
  });
});

test('createTicketService creates route products in a transaction', async () => {
  const calls = [];
  const ticketService = createTicketService({
    ticketQuery: {
      withTransaction: async (work) => work({
        query: async (sql, params) => {
          calls.push({ sql, params });
          return { rows: [] };
        },
      }),
      insertTicketType: async (_client, input) => {
        calls.push({ fn: 'insertTicketType', input });
        return {
          id: 11,
          ticketName: input.ticketName,
        };
      },
      insertRouteProduct: async (_client, input) => {
        calls.push({ fn: 'insertRouteProduct', input });
        return {
          id: 22,
          productName: input.productName,
          ticketTypeId: input.ticketTypeId,
          startPierId: input.startPierId,
          endPierId: input.endPierId,
          status: input.status,
        };
      },
    },
  });

  const result = await ticketService.createRouteProduct({
    productName: '妙灵洞码头至骥马码头测试线路',
    ticketName: '测试成人票',
    tripType: 'ONE_WAY',
    startPierId: '1',
    endPierId: '2',
    raftCapacity: '6',
    originalPrice: '168',
    salePrice: '128',
    windowPhone: '400-800-8899',
    ticketCategory: 'RAFT',
    description: '测试说明',
    refundRule: '发船前可退',
    isRealNameRequired: true,
    routeStatus: 'ENABLED',
  });

  assert.equal(result.success, true);
  assert.equal(result.message, 'route product created');
  assert.equal(result.data.ticketType.ticketName, '测试成人票');
  assert.equal(result.data.routeProduct.productName, '妙灵洞码头至骥马码头测试线路');
  assert.equal(calls.some((item) => item.fn === 'insertTicketType'), true);
  assert.equal(calls.some((item) => item.fn === 'insertRouteProduct'), true);
});

test('createTicketService rejects sale price above original price', async () => {
  const ticketService = createTicketService({
    ticketQuery: {},
  });

  await assert.rejects(
    ticketService.createRouteProduct({
      productName: '测试线路',
      ticketName: '测试票种',
      tripType: 'ONE_WAY',
      startPierId: 1,
      endPierId: 2,
      raftCapacity: 6,
      originalPrice: 100,
      salePrice: 120,
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createTicketService disables route products and linked ticket types', async () => {
  const calls = [];
  const ticketService = createTicketService({
    ticketQuery: {
      withTransaction: async (work) => work({
        query: async () => ({ rows: [] }),
      }),
      updateRouteProductStatus: async (_client, routeProductId, status) => {
        calls.push({ fn: 'updateRouteProductStatus', routeProductId, status });
        return {
          id: routeProductId,
          ticketTypeId: 11,
          status,
        };
      },
      updateTicketTypeStatus: async (_client, ticketTypeId, status) => {
        calls.push({ fn: 'updateTicketTypeStatus', ticketTypeId, status });
        return {
          id: ticketTypeId,
          status,
        };
      },
    },
  });

  const result = await ticketService.disableRouteProduct('22');

  assert.equal(result.success, true);
  assert.equal(result.message, 'route product disabled');
  assert.equal(calls[0].fn, 'updateRouteProductStatus');
  assert.equal(calls[1].fn, 'updateTicketTypeStatus');
});

test('createTicketService saves admin time slots by creating a new quota row', async () => {
  const calls = [];
  const ticketService = createTicketService({
    ticketQuery: {
      findAdminRouteProductById: async (routeProductId) => {
        calls.push({ fn: 'findAdminRouteProductById', routeProductId });
        return {
          id: routeProductId,
          ticketTypeId: 11,
          productName: '测试线路',
          ticketName: '测试票种',
        };
      },
      withTransaction: async (work) => work({
        query: async () => ({ rows: [] }),
      }),
      findTimeSlotQuotaByKey: async (_client, input) => {
        calls.push({ fn: 'findTimeSlotQuotaByKey', input });
        return null;
      },
      insertTimeSlotQuota: async (_client, input) => {
        calls.push({ fn: 'insertTimeSlotQuota', input });
        return {
          id: 9,
          ticketTypeId: input.ticketTypeId,
          visitDate: input.visitDate,
          slotStartTime: input.slotStartTime,
          slotEndTime: input.slotEndTime,
          quotaTotal: input.quotaTotal,
          quotaSold: 0,
          quotaCheckedIn: 0,
          status: input.status,
        };
      },
      updateTimeSlotQuota: async () => {
        throw new Error('should not update existing quota');
      },
    },
  });

  const result = await ticketService.saveAdminTimeSlot({
    routeProductId: 22,
    visitDate: '2026-05-12',
    slotStartTime: '09:00',
    slotEndTime: '10:00',
    quotaTotal: 120,
    status: 'ENABLED',
  });

  assert.equal(result.success, true);
  assert.equal(result.message, 'time slot created');
  assert.equal(result.data.routeProduct.id, 22);
  assert.equal(result.data.timeSlot.id, 9);
  assert.equal(calls[0].fn, 'findAdminRouteProductById');
  assert.equal(calls[1].fn, 'findTimeSlotQuotaByKey');
  assert.equal(calls[2].fn, 'insertTimeSlotQuota');
});

test('createTicketService updates admin time slots when the same slot exists', async () => {
  const calls = [];
  const ticketService = createTicketService({
    ticketQuery: {
      findAdminRouteProductById: async () => ({
        id: 22,
        ticketTypeId: 11,
        productName: '测试线路',
        ticketName: '测试票种',
      }),
      withTransaction: async (work) => work({
        query: async () => ({ rows: [] }),
      }),
      findTimeSlotQuotaByKey: async (_client, input) => {
        calls.push({ fn: 'findTimeSlotQuotaByKey', input });
        return {
          id: 9,
          ticketTypeId: input.ticketTypeId,
          visitDate: input.visitDate,
          slotStartTime: input.slotStartTime,
          slotEndTime: input.slotEndTime,
          quotaTotal: 80,
          quotaSold: 20,
          quotaCheckedIn: 5,
          status: 'ENABLED',
        };
      },
      insertTimeSlotQuota: async () => {
        throw new Error('should not insert new quota');
      },
      updateTimeSlotQuota: async (_client, timeSlotId, input) => {
        calls.push({ fn: 'updateTimeSlotQuota', timeSlotId, input });
        return {
          id: timeSlotId,
          ticketTypeId: input.ticketTypeId,
          visitDate: input.visitDate,
          slotStartTime: input.slotStartTime,
          slotEndTime: input.slotEndTime,
          quotaTotal: input.quotaTotal,
          quotaSold: 20,
          quotaCheckedIn: 5,
          status: input.status,
        };
      },
    },
  });

  const result = await ticketService.saveAdminTimeSlot({
    routeProductId: 22,
    visitDate: '2026-05-12',
    slotStartTime: '09:00',
    slotEndTime: '10:00',
    quotaTotal: 90,
    status: 'DISABLED',
  });

  assert.equal(result.success, true);
  assert.equal(result.message, 'time slot updated');
  assert.equal(result.data.timeSlot.quotaTotal, 90);
  assert.equal(calls[0].fn, 'findTimeSlotQuotaByKey');
  assert.equal(calls[1].fn, 'updateTimeSlotQuota');
});

test('GET and POST /api/admin/time-slots forward to ticket service', async () => {
  const calls = [];
  const app = createApp({
    authRequired: true,
    authService: {
      requireAdmin: () => (_req, _res, next) => next(),
      requireRegisteredVisitor: () => (_req, _res, next) => next(),
      requireSession: () => (_req, _res, next) => next(),
      requireVisitorOrAdmin: () => (_req, _res, next) => next(),
    },
    ticketService: {
      getTicketTypes: async () => ({ success: true, message: 'noop', data: [] }),
      getTimeSlots: async () => ({ success: true, message: 'noop', data: [] }),
      getRouteProducts: async () => ({ success: true, message: 'noop', data: [] }),
      getPiers: async () => ({ success: true, message: 'noop', data: [] }),
      getAdminRouteProducts: async () => ({ success: true, message: 'noop', data: [] }),
      getAdminTimeSlots: async (query) => {
        calls.push({ fn: 'getAdminTimeSlots', query });
        return {
          success: true,
          message: 'admin time slots retrieved',
          data: [
            {
              id: 1,
              ticketTypeId: 11,
              visitDate: '2026-05-12',
              slotStartTime: '09:00:00',
              slotEndTime: '10:00:00',
              quotaTotal: 100,
              quotaSold: 0,
              quotaCheckedIn: 0,
              remainingQuota: 100,
              status: 'ENABLED',
            },
          ],
        };
      },
      createRouteProduct: async () => ({ success: true, message: 'noop', data: {} }),
      saveAdminTimeSlot: async (body) => {
        calls.push({ fn: 'saveAdminTimeSlot', body });
        return {
          success: true,
          message: 'time slot created',
          data: {
            routeProduct: { id: 22, productName: '测试线路', ticketTypeId: 11 },
            timeSlot: {
              id: 9,
              ticketTypeId: 11,
              visitDate: '2026-05-12',
              slotStartTime: '09:00:00',
              slotEndTime: '10:00:00',
              quotaTotal: 100,
              quotaSold: 0,
              quotaCheckedIn: 0,
              remainingQuota: 100,
              status: 'ENABLED',
            },
          },
        };
      },
      disableRouteProduct: async () => ({ success: true, message: 'noop', data: {} }),
      restoreRouteProduct: async () => ({ success: true, message: 'noop', data: {} }),
    },
  });
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const getResponse = await fetch(`http://127.0.0.1:${port}/api/admin/time-slots?routeProductId=22&visitDate=2026-05-12`);
    const getBody = await getResponse.json();
    assert.equal(getResponse.status, 200);
    assert.equal(getBody.data.length, 1);

    const postResponse = await fetch(`http://127.0.0.1:${port}/api/admin/time-slots`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        routeProductId: 22,
        visitDate: '2026-05-12',
        slotStartTime: '09:00',
        slotEndTime: '10:00',
        quotaTotal: 100,
        status: 'ENABLED',
      }),
    });
    const postBody = await postResponse.json();

    assert.equal(postResponse.status, 201);
    assert.equal(postBody.message, 'time slot created');
    assert.equal(calls[0].fn, 'getAdminTimeSlots');
    assert.equal(calls[1].fn, 'saveAdminTimeSlot');
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
