const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');

const { createApp } = require('../src/app');
const { createVisitorService } = require('../src/services/visitor.service');

test('registerVisitor updates an existing visitor by identity', async () => {
  const calls = [];
  const visitorService = createVisitorService({
    visitorQuery: {
      findVisitorByIdentity: async () => ({
        id: 9,
        visitorName: '旧名字',
        idType: 'ID_CARD',
        idNumber: '450321200001011234',
        phone: '13800000000',
        gender: 'MALE',
        birthDate: '2000-01-01',
      }),
      findVisitorByPhone: async () => null,
      updateVisitorByIdentity: async (input) => {
        calls.push(input);
        return {
          id: 9,
          visitorName: input.visitorName,
          idType: input.idType,
          idNumber: input.idNumber,
          phone: input.phone,
          gender: input.gender,
          birthDate: input.birthDate,
        };
      },
      updateVisitorByPhone: async () => null,
      insertVisitor: async () => {
        throw new Error('should not insert duplicate visitor');
      },
      findVisitorById: async () => null,
      listOrdersByVisitorId: async () => [],
    },
  });

  const result = await visitorService.registerVisitor({
    visitorName: '张三',
    idType: 'ID_CARD',
    idNumber: '450321200001011234',
    phone: '13900000000',
    gender: 'MALE',
    birthDate: '2000-01-01',
  });

  assert.deepEqual(result, {
    success: true,
    message: 'visitor registered',
    data: {
      id: 9,
      visitorName: '张三',
      idType: 'ID_CARD',
      idNumber: '450321200001011234',
      phone: '13900000000',
      gender: 'MALE',
      birthDate: '2000-01-01',
    },
  });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].visitorName, '张三');
});

test('getVisitorOrders groups order items by order', async () => {
  const visitorService = createVisitorService({
    visitorQuery: {
      findVisitorByIdentity: async () => null,
      findVisitorByPhone: async () => null,
      updateVisitorByIdentity: async () => null,
      updateVisitorByPhone: async () => null,
      insertVisitor: async () => null,
      findVisitorById: async () => ({
        id: 1,
        visitorName: '张三',
        idType: 'ID_CARD',
        idNumber: '450321200001011234',
        phone: '13800000000',
        gender: 'MALE',
        birthDate: '2000-01-01',
      }),
      listOrdersByVisitorId: async () => [
        {
          orderId: 101,
          orderNo: 'ORD202605010001',
          orderStatus: 'PAID',
          paymentStatus: 'PAID',
          orderSource: 'ONLINE',
          buyerName: '张三',
          buyerPhone: '13800000000',
          totalAmount: 198,
          discountAmount: 0,
          payableAmount: 198,
          paidAmount: 198,
          orderTime: '2026-05-01',
          paidAt: '2026-05-01',
          cancelTime: null,
          orderItemId: 201,
          itemNo: 'ORD202605010001-01',
          ticketCode: 'TCORD20260501000101',
          visitDate: '2026-05-01',
          originalPrice: 99,
          itemDiscountAmount: 0,
          finalPrice: 99,
          itemStatus: 'UNUSED',
          ticketTypeId: 11,
          ticketName: '成人票',
          productName: '双人筏-单程-妙灵洞码头→骥马码头',
          tripType: 'ONE_WAY',
          windowPhone: '19877396225',
        },
        {
          orderId: 101,
          orderNo: 'ORD202605010001',
          orderStatus: 'PAID',
          paymentStatus: 'PAID',
          orderSource: 'ONLINE',
          buyerName: '张三',
          buyerPhone: '13800000000',
          totalAmount: 198,
          discountAmount: 0,
          payableAmount: 198,
          paidAmount: 198,
          orderTime: '2026-05-01',
          paidAt: '2026-05-01',
          cancelTime: null,
          orderItemId: 202,
          itemNo: 'ORD202605010001-02',
          ticketCode: 'TCORD20260501000102',
          visitDate: '2026-05-01',
          originalPrice: 99,
          itemDiscountAmount: 0,
          finalPrice: 99,
          itemStatus: 'UNUSED',
          ticketTypeId: 11,
          ticketName: '成人票',
          productName: '双人筏-单程-妙灵洞码头→骥马码头',
          tripType: 'ONE_WAY',
          windowPhone: '19877396225',
        },
      ],
    },
  });

  const result = await visitorService.getVisitorOrders(1);

  assert.equal(result.success, true);
  assert.equal(result.data.visitor.id, 1);
  assert.equal(result.data.orders.length, 1);
  assert.equal(result.data.orders[0].items.length, 2);
  assert.equal(result.data.orders[0].items[0].ticketCode, 'TCORD20260501000101');
});

test('POST /api/visitors returns a registered visitor', async () => {
  const app = createApp({
    visitorService: {
      registerVisitor: async () => ({
        success: true,
        message: 'visitor registered',
        data: {
          id: 1,
          visitorName: '张三',
          idType: 'ID_CARD',
          idNumber: '450321200001011234',
          phone: '13800000000',
          gender: 'MALE',
          birthDate: '2000-01-01',
        },
      }),
      getVisitor: async () => ({
        success: true,
        message: 'visitor loaded',
        data: {
          id: 1,
          visitorName: '张三',
          idType: 'ID_CARD',
          idNumber: '450321200001011234',
          phone: '13800000000',
          gender: 'MALE',
          birthDate: '2000-01-01',
        },
      }),
      getVisitorOrders: async () => ({
        success: true,
        message: 'visitor orders loaded',
        data: {
          visitor: {
            id: 1,
            visitorName: '张三',
            idType: 'ID_CARD',
            idNumber: '450321200001011234',
            phone: '13800000000',
            gender: 'MALE',
            birthDate: '2000-01-01',
          },
          orders: [],
        },
      }),
    },
  });

  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/visitors`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        visitorName: '张三',
        idType: 'ID_CARD',
        idNumber: '450321200001011234',
      }),
    });
    const body = await response.json();

    assert.equal(response.status, 201);
    assert.equal(body.data.visitor.visitorName, '张三');
    assert.equal(body.data.user.role, 'VISITOR');
    assert.equal(typeof body.data.token, 'string');
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
