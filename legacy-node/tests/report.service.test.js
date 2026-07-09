const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');

const { createApp } = require('../src/app');
const { createReportQuery } = require('../src/db/queries/report.query');
const { createReportService } = require('../src/services/report.service');

test('createReportService rejects missing report filters', async () => {
  const reportService = createReportService({
    reportQuery: {
      fetchSalesReport: async () => [],
    },
  });

  await assert.rejects(
    reportService.getSalesReport({
      ticketTypeId: '1',
      startDate: '2026-05-01',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createReportService rejects startDate after endDate', async () => {
  const reportService = createReportService({
    reportQuery: {
      fetchSalesReport: async () => [],
    },
  });

  await assert.rejects(
    reportService.getSalesReport({
      ticketTypeId: '1',
      startDate: '2026-05-07',
      endDate: '2026-05-01',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createReportService normalizes sales report rows to numbers', async () => {
  const reportService = createReportService({
    reportQuery: {
      fetchSalesReport: async () => [
        {
          ticketTypeId: '1',
          visitDate: new Date('2026-05-01T00:00:00.000Z'),
          soldCount: '3',
          soldAmount: '297.50',
        },
      ],
    },
  });

  const result = await reportService.getSalesReport({
    ticketTypeId: '1',
    startDate: '2026-05-01',
    endDate: '2026-05-07',
  });

  assert.deepEqual(result, {
    success: true,
    message: 'sales report loaded',
    data: {
      items: [
        {
          ticketTypeId: 1,
          visitDate: '2026-05-01',
          soldCount: 3,
          soldAmount: 297.5,
        },
      ],
      ticketTypeId: 1,
      startDate: '2026-05-01',
      endDate: '2026-05-07',
    },
  });
});

test('createReportService preserves business date when query returns UTC midnight conversion', async () => {
  const reportService = createReportService({
    reportQuery: {
      fetchSalesReport: async () => [
        {
          ticketTypeId: '1',
          visitDate: new Date('2026-04-30T16:00:00.000Z'),
          soldCount: '4',
          soldAmount: '396.00',
        },
      ],
    },
  });

  const result = await reportService.getSalesReport({
    ticketTypeId: '1',
    startDate: '2026-05-01',
    endDate: '2026-05-07',
  });

  assert.equal(result.data.items[0].visitDate, '2026-05-01');
});

test('createReportQuery excludes refunded and cancelled items in sales SQL', async () => {
  let capturedSql = '';
  let capturedParams = null;

  const reportQuery = createReportQuery({
    pool: {
      query: async (sql, params) => {
        capturedSql = sql;
        capturedParams = params;

        return {
          rows: [
            {
              ticket_type_id: '1',
              visit_date: '2026-05-01',
              sold_count: '2',
              sold_amount: '198.00',
            },
          ],
        };
      },
    },
  });

  const rows = await reportQuery.fetchSalesReport({
    ticketTypeId: 1,
    startDate: '2026-05-01',
    endDate: '2026-05-07',
  });

  assert.equal(capturedParams[0], 1);
  assert.equal(capturedParams[1], '2026-05-01');
  assert.equal(capturedParams[2], '2026-05-07');
  assert.match(capturedSql, /item_status IN \('UNUSED', 'USED'\)/);
  assert.deepEqual(rows, [
    {
      ticketTypeId: 1,
      visitDate: '2026-05-01',
      soldCount: 2,
      soldAmount: 198,
    },
  ]);
});

test('createReportService returns offline sale notices', async () => {
  const reportService = createReportService({
    reportQuery: {
      fetchOfflineSaleNotices: async () => [
        {
          routeProductId: '1',
          ticketTypeId: '11',
          productName: '双人筏-单程-妙灵洞码头→骥马码头',
          businessDate: '2026-04-25',
          saleStatus: 'ON_SALE',
          tripType: 'ONE_WAY',
          windowPhone: '19877396225',
          remark: '正常售票',
        },
      ],
    },
  });

  const result = await reportService.getOfflineSaleNotices({
    businessDate: '2026-04-25',
  });

  assert.deepEqual(result, {
    success: true,
    message: 'offline sale notices loaded',
    data: [
      {
        routeProductId: 1,
        ticketTypeId: 11,
        productName: '双人筏-单程-妙灵洞码头→骥马码头',
        businessDate: '2026-04-25',
        saleStatus: 'ON_SALE',
        tripType: 'ONE_WAY',
        windowPhone: '19877396225',
        remark: '正常售票',
      },
    ],
  });
});

test('createReportService rejects missing businessDate for offline sale notices', async () => {
  const reportService = createReportService({
    reportQuery: {
      fetchOfflineSaleNotices: async () => [],
    },
  });

  await assert.rejects(
    reportService.getOfflineSaleNotices({}),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createReportService rejects invalid businessDate format for offline sale notices', async () => {
  const reportService = createReportService({
    reportQuery: {
      fetchOfflineSaleNotices: async () => [],
    },
  });

  await assert.rejects(
    reportService.getOfflineSaleNotices({
      businessDate: '2026/04/25',
    }),
    (error) => error.name === 'AppError' && error.statusCode === 400,
  );
});

test('createReportQuery returns offline sale notices with route product semantics', async () => {
  let capturedSql = '';
  let capturedParams = null;

  const reportQuery = createReportQuery({
    pool: {
      query: async (sql, params) => {
        capturedSql = sql;
        capturedParams = params;

        return {
          rows: [
            {
              route_product_id: '1',
              ticket_type_id: '11',
              product_name: '双人筏-单程-妙灵洞码头→骥马码头',
              business_date: '2026-04-25',
              sale_status: 'ON_SALE',
              trip_type: 'ONE_WAY',
              window_phone: '19877396225',
              remark: '正常售票',
            },
          ],
        };
      },
    },
  });

  const rows = await reportQuery.fetchOfflineSaleNotices({
    businessDate: '2026-04-25',
  });

  assert.equal(capturedParams[0], '2026-04-25');
  assert.match(capturedSql, /FROM route_product rp/);
  assert.match(capturedSql, /LEFT JOIN offline_sale_notice osn/);
  assert.match(capturedSql, /osn\.business_date = \$1::date/);
  assert.deepEqual(rows, [
    {
      routeProductId: 1,
      ticketTypeId: 11,
      productName: '双人筏-单程-妙灵洞码头→骥马码头',
      businessDate: '2026-04-25',
      saleStatus: 'ON_SALE',
      tripType: 'ONE_WAY',
      windowPhone: '19877396225',
      remark: '正常售票',
    },
  ]);
});

test('createReportQuery returns every enabled route product with UNCONFIGURED fallback', async () => {
  const reportQuery = createReportQuery({
    pool: {
      query: async () => ({
        rows: [
          {
            route_product_id: '2',
            ticket_type_id: '12',
            product_name: '四人筏-往返-金龙桥码头→旧县码头',
            business_date: '2026-04-25',
            sale_status: 'UNCONFIGURED',
            trip_type: 'ROUND_TRIP',
            window_phone: '19800001111',
            remark: null,
          },
        ],
      }),
    },
  });

  const rows = await reportQuery.fetchOfflineSaleNotices({
    businessDate: '2026-04-25',
  });

  assert.deepEqual(rows, [
    {
      routeProductId: 2,
      ticketTypeId: 12,
      productName: '四人筏-往返-金龙桥码头→旧县码头',
      businessDate: '2026-04-25',
      saleStatus: 'UNCONFIGURED',
      tripType: 'ROUND_TRIP',
      windowPhone: '19800001111',
      remark: null,
    },
  ]);
});

test('GET /api/reports/sales forwards query params to report service', async () => {
  let receivedQuery = null;

  const app = createApp({
    reportService: {
      getSalesReport: async (query) => {
        receivedQuery = query;

        return {
          success: true,
          message: 'sales report loaded',
          data: {
            items: [],
            ticketTypeId: 1,
            startDate: '2026-05-01',
            endDate: '2026-05-07',
          },
        };
      },
    },
  });
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/reports/sales?ticketTypeId=1&startDate=2026-05-01&endDate=2026-05-07`);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.deepEqual(receivedQuery, {
      ticketTypeId: '1',
      startDate: '2026-05-01',
      endDate: '2026-05-07',
    });
    assert.deepEqual(body, {
      success: true,
      message: 'sales report loaded',
      data: {
        items: [],
        ticketTypeId: 1,
        startDate: '2026-05-01',
        endDate: '2026-05-07',
      },
    });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('GET /api/reports/sales returns 400 for invalid date range through error middleware', async () => {
  const app = createApp({
    reportService: createReportService({
      reportQuery: {
        fetchSalesReport: async () => [],
      },
    }),
  });
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/reports/sales?ticketTypeId=1&startDate=2026-05-07&endDate=2026-05-01`);
    const body = await response.json();

    assert.equal(response.status, 400);
    assert.deepEqual(body, {
      success: false,
      message: 'startDate must be less than or equal to endDate',
    });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('GET /api/reports/offline-sale-notices forwards businessDate to report service', async () => {
  let receivedQuery = null;

  const app = createApp({
    reportService: {
      getSalesReport: async () => ({
        success: true,
        message: 'sales report loaded',
        data: {
          items: [],
          ticketTypeId: 1,
          startDate: '2026-05-01',
          endDate: '2026-05-07',
        },
      }),
      getOfflineSaleNotices: async (query) => {
        receivedQuery = query;

        return {
          success: true,
          message: 'offline sale notices loaded',
          data: [
            {
              routeProductId: 1,
              ticketTypeId: 11,
              productName: '双人筏-单程-妙灵洞码头→骥马码头',
              businessDate: '2026-04-25',
              saleStatus: 'ON_SALE',
              tripType: 'ONE_WAY',
              windowPhone: '19877396225',
              remark: '正常售票',
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
    const response = await fetch(`http://127.0.0.1:${port}/api/reports/offline-sale-notices?businessDate=2026-04-25`);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.deepEqual(receivedQuery, {
      businessDate: '2026-04-25',
    });
    assert.deepEqual(body, {
      success: true,
      message: 'offline sale notices loaded',
      data: [
        {
          routeProductId: 1,
          ticketTypeId: 11,
          productName: '双人筏-单程-妙灵洞码头→骥马码头',
          businessDate: '2026-04-25',
          saleStatus: 'ON_SALE',
          tripType: 'ONE_WAY',
          windowPhone: '19877396225',
          remark: '正常售票',
        },
      ],
    });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
