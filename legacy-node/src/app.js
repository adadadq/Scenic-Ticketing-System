const fs = require('node:fs');
const express = require('express');
const path = require('node:path');

const { createHealthRouter } = require('./routes/health.routes');
const { createAuthRouter } = require('./routes/auth.routes');
const { createTicketRouter } = require('./routes/ticket.routes');
const { createVisitorRouter } = require('./routes/visitor.routes');
const { createOrderRouter } = require('./routes/order.routes');
const { createCheckinRouter } = require('./routes/checkin.routes');
const { createRefundRouter } = require('./routes/refund.routes');
const { createReportRouter } = require('./routes/report.routes');
const { notFoundMiddleware } = require('./middlewares/not-found.middleware');
const { errorMiddleware } = require('./middlewares/error.middleware');
const { createHealthService } = require('./services/health.service');
const { createAuthService } = require('./services/auth.service');
const { createTicketService } = require('./services/ticket.service');
const { createVisitorService } = require('./services/visitor.service');
const { createOrderService } = require('./services/order.service');
const { createCheckinService } = require('./services/checkin.service');
const { createRefundService } = require('./services/refund.service');
const { createReportService } = require('./services/report.service');

function createApp(options = {}) {
  const app = express();
  const publicDir = path.resolve(__dirname, '../public');
  const indexHtmlPath = path.join(publicDir, 'index.html');
  const stylesPath = path.join(publicDir, 'styles.css');
  const frontendScriptPath = path.join(publicDir, 'app.js');
  const authRequired = options.authRequired === true;
  const healthService = options.healthService || createHealthService({
    pingDatabase: options.pingDatabase,
  });
  const authService = options.authService || createAuthService({
    dbPool: options.dbPool,
    authQuery: options.authQuery,
    visitorQuery: options.visitorQuery,
  });
  const authMiddleware = authRequired ? {
    requireAdmin: authService.requireAdmin(),
    requireRegisteredVisitor: authService.requireRegisteredVisitor(),
    requireSession: authService.requireSession(),
    requireVisitorOrAdmin: authService.requireVisitorOrAdmin(),
  } : {};
  const ticketService = options.ticketService || createTicketService({
    dbPool: options.dbPool,
    ticketQuery: options.ticketQuery,
  });
  const visitorService = options.visitorService || createVisitorService({
    dbPool: options.dbPool,
    visitorQuery: options.visitorQuery,
  });
  const orderService = options.orderService || createOrderService({
    dbPool: options.dbPool,
    orderQuery: options.orderQuery,
  });
  const checkinService = options.checkinService || createCheckinService({
    dbPool: options.dbPool,
    checkinQuery: options.checkinQuery,
  });
  const refundService = options.refundService || createRefundService({
    dbPool: options.dbPool,
    refundQuery: options.refundQuery,
  });
  const reportService = options.reportService || createReportService({
    dbPool: options.dbPool,
    reportQuery: options.reportQuery,
  });

  app.use(express.json());
  app.get('/', (_req, res) => {
    res.type('html').send(fs.readFileSync(indexHtmlPath, 'utf8'));
  });
  app.get('/styles.css', (_req, res) => {
    res.type('text/css').send(fs.readFileSync(stylesPath, 'utf8'));
  });
  app.get('/app.js', (_req, res) => {
    res.type('application/javascript').send(fs.readFileSync(frontendScriptPath, 'utf8'));
  });
  app.use('/api', createAuthRouter({ authService }));
  app.use('/api', createHealthRouter({ healthService }));
  app.use('/api', createTicketRouter({ ticketService, authMiddleware }));
  app.use('/api', createVisitorRouter({ visitorService, authService, authMiddleware }));
  app.use('/api', createOrderRouter({ orderService, authMiddleware }));
  app.use('/api', createCheckinRouter({ checkinService, authMiddleware }));
  app.use('/api', createRefundRouter({ refundService, authMiddleware }));
  app.use('/api', createReportRouter({ reportService, authMiddleware }));
  app.use(notFoundMiddleware);
  app.use(errorMiddleware);

  return app;
}

module.exports = {
  createApp,
};
