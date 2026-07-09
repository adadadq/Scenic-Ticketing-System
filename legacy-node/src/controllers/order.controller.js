const { sendJson } = require('../utils/response');
const { AppError } = require('../utils/app-error');
const { createOrderService } = require('../services/order.service');

function createOrderController(options = {}) {
  const orderService = options.orderService || createOrderService(options);

  async function createOrder(req, res, next) {
    try {
      const currentUser = req.auth;

      if (!currentUser) {
        throw new AppError(401, 'unauthorized');
      }

      if (currentUser.role !== 'VISITOR' || currentUser.scope !== 'REGISTERED') {
        throw new AppError(403, 'registered visitor account required');
      }

      const body = {
        ...req.body,
        items: Array.isArray(req.body?.items)
          ? req.body.items.map((item) => ({
            ...item,
            visitorId: currentUser.visitorId,
          }))
          : req.body?.items,
      };

      const payload = await orderService.createOrder(body);
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    createOrder,
  };
}

module.exports = {
  createOrderController,
};
