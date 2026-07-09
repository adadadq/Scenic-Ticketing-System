const express = require('express');

const { createTicketController } = require('../controllers/ticket.controller');

function createTicketRouter(options = {}) {
  const ticketController = options.ticketController
    || createTicketController({ ticketService: options.ticketService });
  const authMiddleware = options.authMiddleware || {};
  const requireSession = authMiddleware.requireSession || ((_req, _res, next) => next());
  const requireAdmin = authMiddleware.requireAdmin || ((_req, _res, next) => next());

  const ticketRouter = express.Router();
  ticketRouter.get('/ticket-types', requireSession, ticketController.getTicketTypes);
  ticketRouter.get('/time-slots', requireSession, ticketController.getTimeSlots);
  ticketRouter.get('/route-products', requireSession, ticketController.getRouteProducts);
  ticketRouter.get('/piers', requireAdmin, ticketController.getPiers);
  ticketRouter.get('/admin/route-products', requireAdmin, ticketController.getAdminRouteProducts);
  ticketRouter.get('/admin/time-slots', requireAdmin, ticketController.getAdminTimeSlots);
  ticketRouter.post('/admin/route-products', requireAdmin, ticketController.postRouteProduct);
  ticketRouter.post('/admin/time-slots', requireAdmin, ticketController.postAdminTimeSlot);
  ticketRouter.patch('/admin/route-products/:routeProductId/restore', requireAdmin, ticketController.restoreRouteProduct);
  ticketRouter.delete('/admin/route-products/:routeProductId', requireAdmin, ticketController.deleteRouteProduct);

  return ticketRouter;
}

module.exports = {
  createTicketRouter,
};
