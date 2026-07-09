const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');

const { createApp } = require('../src/app');
const { AppError } = require('../src/utils/app-error');
const { createAuthService, verifyAdminPassword } = require('../src/services/auth.service');

test('verifyAdminPassword accepts legacy demo placeholders without bcrypt dependency', () => {
  const demoHash = '$2b$12$example_hash_value_for_demo_only';

  assert.equal(verifyAdminPassword('LEGACY_DEMO_PASSWORD_A_DO_NOT_USE', demoHash), true);
  assert.equal(verifyAdminPassword('LEGACY_DEMO_PASSWORD_B_DO_NOT_USE', demoHash), true);
  assert.equal(verifyAdminPassword('LEGACY_DEMO_PASSWORD_C_DO_NOT_USE', demoHash), true);
  assert.equal(verifyAdminPassword('wrong-password', demoHash), false);
});

test('loginAdmin returns an admin token for enabled admin users', async () => {
  const authService = createAuthService({
    authQuery: {
      findAdminByUsername: async (username) => ({
        id: 1,
        username,
        displayName: '系统管理员',
        phone: '13800000000',
        passwordHash: '$2b$12$example_hash_value_for_demo_only',
        status: 'ENABLED',
      }),
    },
    visitorQuery: {},
  });

  const result = await authService.loginAdmin({
    username: 'admin',
    password: 'LEGACY_DEMO_PASSWORD_A_DO_NOT_USE',
  });

  assert.equal(result.success, true);
  assert.equal(result.data.user.role, 'ADMIN');
  assert.equal(result.data.user.username, 'admin');
  assert.equal(typeof result.data.token, 'string');
});

test('loginVisitorTemp creates a temporary visitor when phone is unknown', async () => {
  const insertedVisitors = [];
  const authService = createAuthService({
    authQuery: {},
    visitorQuery: {
      findVisitorByPhone: async () => null,
      insertVisitor: async (input) => {
        insertedVisitors.push(input);
        return {
          id: 7,
          visitorName: input.visitorName,
          idType: input.idType,
          idNumber: input.idNumber,
          phone: input.phone,
          gender: null,
          birthDate: null,
        };
      },
    },
  });

  const result = await authService.loginVisitorTemp({ phone: '13911112222' });

  assert.equal(result.success, true);
  assert.equal(result.data.user.role, 'VISITOR');
  assert.equal(result.data.user.scope, 'TEMP');
  assert.equal(result.data.user.phone, '13911112222');
  assert.equal(insertedVisitors.length, 1);
  assert.equal(insertedVisitors[0].idType, 'TEMP_PHONE');
});

test('requireRegisteredVisitor rejects temporary visitor sessions', async () => {
  const authService = createAuthService({
    authQuery: {},
    visitorQuery: {
      findVisitorByPhone: async () => ({
        id: 8,
        visitorName: '临时游客2222',
        idType: 'TEMP_PHONE',
        idNumber: '13911112222',
        phone: '13911112222',
      }),
    },
  });
  const login = await authService.loginVisitorTemp({ phone: '13911112222' });
  const middleware = authService.requireRegisteredVisitor();
  const req = { headers: { authorization: `Bearer ${login.data.token}` } };

  await new Promise((resolve) => {
    middleware(req, {}, (error) => {
      assert.ok(error instanceof AppError);
      assert.equal(error.statusCode, 403);
      resolve();
    });
  });
});

test('authRequired routes reject anonymous requests and accept visitor token for browsing', async () => {
  const authService = createAuthService({
    authQuery: {},
    visitorQuery: {
      findVisitorByPhone: async () => ({
        id: 12,
        visitorName: '临时游客2222',
        idType: 'TEMP_PHONE',
        idNumber: '13911112222',
        phone: '13911112222',
      }),
    },
  });
  const app = createApp({
    authRequired: true,
    authService,
    ticketService: {
      getTicketTypes: async () => ({ success: true, message: 'ok', data: [] }),
      getTimeSlots: async () => ({ success: true, message: 'ok', data: [] }),
      getRouteProducts: async () => ({ success: true, message: 'ok', data: [] }),
    },
  });
  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const anonymous = await fetch(`http://127.0.0.1:${port}/api/ticket-types`);
    assert.equal(anonymous.status, 401);

    const login = await fetch(`http://127.0.0.1:${port}/api/auth/visitor/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: '13911112222' }),
    });
    const loginBody = await login.json();

    const browsed = await fetch(`http://127.0.0.1:${port}/api/ticket-types`, {
      headers: { Authorization: `Bearer ${loginBody.data.token}` },
    });
    assert.equal(browsed.status, 200);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('temporary visitor cannot read my orders route', async () => {
  const authService = createAuthService({
    authQuery: {},
    visitorQuery: {
      findVisitorByPhone: async () => ({
        id: 15,
        visitorName: '临时游客3333',
        idType: 'TEMP_PHONE',
        idNumber: '13911113333',
        phone: '13911113333',
      }),
    },
  });
  const app = createApp({
    authRequired: true,
    authService,
    visitorService: {
      getVisitor: async () => ({ success: true, message: 'visitor loaded', data: {} }),
      getVisitorOrders: async () => {
        throw new Error('temporary visitor should not reach visitor order service');
      },
      registerVisitor: async () => ({ success: true, message: 'visitor registered', data: {} }),
    },
  });
  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const login = await fetch(`http://127.0.0.1:${port}/api/auth/visitor/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone: '13911113333' }),
    });
    const loginBody = await login.json();
    const orders = await fetch(`http://127.0.0.1:${port}/api/visitors/15/orders`, {
      headers: { Authorization: `Bearer ${loginBody.data.token}` },
    });
    const body = await orders.json();

    assert.equal(orders.status, 403);
    assert.equal(body.message, 'registered visitor account required');
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
