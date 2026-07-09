const { sendJson } = require('../utils/response');
const { AppError } = require('../utils/app-error');
const { createVisitorService } = require('../services/visitor.service');
const { createAuthService } = require('../services/auth.service');

function createVisitorController(options = {}) {
  const visitorService = options.visitorService || createVisitorService(options);
  const authService = options.authService || createAuthService(options);

  async function postVisitor(req, res, next) {
    try {
      const visitorPayload = await visitorService.registerVisitor(req.body);
      const loginPayload = await authService.loginRegisteredVisitor(visitorPayload.data);
      sendJson(res, 201, {
        success: true,
        message: visitorPayload.message,
        data: {
          ...loginPayload.data,
          visitor: visitorPayload.data,
        },
      });
    } catch (error) {
      next(error);
    }
  }

  async function getVisitor(req, res, next) {
    try {
      const currentUser = req.auth || authService.getSessionUserFromRequest(req);
      const requestedVisitorId = Number(req.params.visitorId);

      if (!currentUser) {
        throw new AppError(401, 'unauthorized');
      }

      if (currentUser.role === 'VISITOR' && Number(currentUser.visitorId) !== requestedVisitorId) {
        throw new AppError(403, 'forbidden');
      }

      const payload = await visitorService.getVisitor(req.params.visitorId);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getVisitorOrders(req, res, next) {
    try {
      const currentUser = req.auth || authService.getSessionUserFromRequest(req);
      const requestedVisitorId = Number(req.params.visitorId);

      if (!currentUser) {
        throw new AppError(401, 'unauthorized');
      }

      if (currentUser.role === 'VISITOR' && Number(currentUser.visitorId) !== requestedVisitorId) {
        throw new AppError(403, 'forbidden');
      }

      if (currentUser.role === 'VISITOR' && currentUser.scope !== 'REGISTERED') {
        throw new AppError(403, 'registered visitor account required');
      }

      const payload = await visitorService.getVisitorOrders(req.params.visitorId);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    getVisitor,
    getVisitorOrders,
    postVisitor,
  };
}

module.exports = {
  createVisitorController,
};
