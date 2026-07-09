const { sendJson } = require('../utils/response');
const { createTicketService } = require('../services/ticket.service');

function createTicketController(options = {}) {
  const ticketService = options.ticketService || createTicketService(options);

  async function getTicketTypes(_req, res, next) {
    try {
      const payload = await ticketService.getTicketTypes();
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getTimeSlots(req, res, next) {
    try {
      const payload = await ticketService.getTimeSlots(req.query);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getRouteProducts(_req, res, next) {
    try {
      const payload = await ticketService.getRouteProducts();
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getPiers(_req, res, next) {
    try {
      const payload = await ticketService.getPiers();
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getAdminRouteProducts(_req, res, next) {
    try {
      const payload = await ticketService.getAdminRouteProducts();
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getAdminTimeSlots(req, res, next) {
    try {
      const payload = await ticketService.getAdminTimeSlots(req.query);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function postRouteProduct(req, res, next) {
    try {
      const payload = await ticketService.createRouteProduct(req.body);
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  async function postAdminTimeSlot(req, res, next) {
    try {
      const payload = await ticketService.saveAdminTimeSlot(req.body);
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  async function deleteRouteProduct(req, res, next) {
    try {
      const payload = await ticketService.disableRouteProduct(req.params.routeProductId);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function restoreRouteProduct(req, res, next) {
    try {
      const payload = await ticketService.restoreRouteProduct(req.params.routeProductId);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    deleteRouteProduct,
    getAdminTimeSlots,
    getAdminRouteProducts,
    getPiers,
    getTicketTypes,
    getTimeSlots,
    getRouteProducts,
    postRouteProduct,
    postAdminTimeSlot,
    restoreRouteProduct,
  };
}

module.exports = {
  createTicketController,
};
