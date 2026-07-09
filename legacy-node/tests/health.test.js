const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');

const { createApp } = require('../src/app');
const { createHealthService } = require('../src/services/health.service');

test('GET /api/health returns ok', async () => {
  const app = createApp();
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/health`);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.deepEqual(body, { success: true, message: 'service is running' });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('GET / returns static console page', async () => {
  const app = createApp();
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/`);
    const body = await response.text();

    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type') || '', /text\/html/);
    assert.match(body, /遇龙河景区/);
    assert.match(body, /码头窗口售票/);
    assert.match(body, /创建订单/);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('createHealthService maps successful ping to database health', async () => {
  const healthService = createHealthService({
    pingDatabase: async () => true,
  });

  const body = await healthService.getDatabaseHealth();

  assert.deepEqual(body, { success: true, message: 'database is running' });
});

test('createHealthService maps ping failure to AppError 503', async () => {
  const healthService = createHealthService({
    pingDatabase: async () => {
      throw new Error('db down');
    },
  });

  await assert.rejects(
    healthService.getDatabaseHealth(),
    (error) => error.name === 'AppError' && error.statusCode === 503 && error.message === 'database is unavailable',
  );
});

test('GET /api/db/health returns ok when db is healthy', async () => {
  const app = createApp({
    healthService: {
      getServiceHealth: async () => ({
        success: true,
        message: 'service is running',
      }),
      getDatabaseHealth: async () => ({
        success: true,
        message: 'database is running',
      }),
    },
  });
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/db/health`);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.deepEqual(body, { success: true, message: 'database is running' });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('GET /api/db/health returns 503 when db is unavailable', async () => {
  const app = createApp({
    healthService: {
      getServiceHealth: async () => ({
        success: true,
        message: 'service is running',
      }),
      getDatabaseHealth: async () => {
        const error = new Error('database is unavailable');
        error.statusCode = 503;
        throw error;
      },
    },
  });
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/db/health`);
    const body = await response.json();

    assert.equal(response.status, 503);
    assert.deepEqual(body, { success: false, message: 'database is unavailable' });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test('unknown route returns 404', async () => {
  const app = createApp();
  const server = http.createServer(app);

  await new Promise((resolve) => server.listen(0, resolve));
  const { port } = server.address();

  try {
    const response = await fetch(`http://127.0.0.1:${port}/api/unknown`);
    const body = await response.json();

    assert.equal(response.status, 404);
    assert.deepEqual(body, { success: false, message: 'Not Found' });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
