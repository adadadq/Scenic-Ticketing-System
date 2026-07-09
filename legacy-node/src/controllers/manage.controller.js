const { sendJson } = require('../utils/response');
const { createManageService } = require('../services/manage.service');
const { parsePositiveInteger } = require('../utils/validators');

function getRequestMeta(req) {
  return {
    operatorId: Number(req.body?.operatorId) || 1,
    requestIp: req.ip || req.socket?.remoteAddress || '127.0.0.1',
  };
}

function createManageController(options = {}) {
  const manageService = options.manageService || createManageService(options);

  async function getVisitors(req, res, next) {
    try {
      const data = await manageService.listVisitors(req.query);
      sendJson(res, 200, {
        success: true,
        message: 'visitors retrieved',
        data,
      });
    } catch (error) {
      next(error);
    }
  }

  async function getVisitorById(req, res, next) {
    try {
      const payload = await manageService.getVisitorById(req.params.visitorId);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function postVisitor(req, res, next) {
    try {
      const payload = await manageService.registerVisitor(req.body, getRequestMeta(req));
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getRoutes(req, res, next) {
    try {
      const data = await manageService.listRouteProducts(req.query);
      sendJson(res, 200, {
        success: true,
        message: 'routes retrieved',
        data,
      });
    } catch (error) {
      next(error);
    }
  }

  async function getPiers(_req, res, next) {
    try {
      const data = await manageService.listPiers();
      sendJson(res, 200, {
        success: true,
        message: 'piers retrieved',
        data,
      });
    } catch (error) {
      next(error);
    }
  }

  async function postPier(req, res, next) {
    try {
      const payload = await manageService.createPier(req.body, getRequestMeta(req));
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  async function putPier(req, res, next) {
    try {
      const id = parsePositiveInteger(req.params.id, 'id');
      const payload = await manageService.updatePier(id, req.body, getRequestMeta(req));
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function deletePier(req, res, next) {
    try {
      const id = parsePositiveInteger(req.params.id, 'id');
      const payload = await manageService.deletePier(id, getRequestMeta(req));
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getRouteProducts(req, res, next) {
    try {
      const data = await manageService.listRouteProducts(req.query);
      sendJson(res, 200, {
        success: true,
        message: 'route products retrieved',
        data,
      });
    } catch (error) {
      next(error);
    }
  }

  async function postRouteProduct(req, res, next) {
    try {
      const payload = await manageService.createRouteProduct(req.body, getRequestMeta(req));
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  async function putRouteProduct(req, res, next) {
    try {
      const id = parsePositiveInteger(req.params.id, 'id');
      const payload = await manageService.updateRouteProduct(id, req.body, getRequestMeta(req));
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function deleteRouteProduct(req, res, next) {
    try {
      const id = parsePositiveInteger(req.params.id, 'id');
      const payload = await manageService.deleteRouteProduct(id, getRequestMeta(req));
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getOfflineSaleNotices(req, res, next) {
    try {
      const data = await manageService.listOfflineSaleNotices(req.query);
      sendJson(res, 200, {
        success: true,
        message: 'sale notices retrieved',
        data,
      });
    } catch (error) {
      next(error);
    }
  }

  async function postOfflineSaleNotice(req, res, next) {
    try {
      const payload = await manageService.upsertOfflineSaleNotice(req.body, getRequestMeta(req));
      sendJson(res, 201, payload);
    } catch (error) {
      next(error);
    }
  }

  async function putOfflineSaleNotice(req, res, next) {
    try {
      const id = parsePositiveInteger(req.params.id, 'id');
      const payload = await manageService.updateOfflineSaleNotice(id, req.body, getRequestMeta(req));
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function deleteOfflineSaleNotice(req, res, next) {
    try {
      const id = parsePositiveInteger(req.params.id, 'id');
      const payload = await manageService.deleteOfflineSaleNotice(id, getRequestMeta(req));
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getOrdersByPhone(req, res, next) {
    try {
      const payload = await manageService.listOrdersByPhone(req.query.phone || req.query.buyerPhone);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getVisitorOrders(req, res, next) {
    try {
      const payload = await manageService.listOrdersByVisitorId(req.params.visitorId);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getInventory(req, res, next) {
    try {
      const payload = await manageService.listInventory(req.query);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  async function getOperationLogs(req, res, next) {
    try {
      const payload = await manageService.listOperationLogs(req.query.limit);
      sendJson(res, 200, payload);
    } catch (error) {
      next(error);
    }
  }

  return {
    getOfflineSaleNotices,
    getOperationLogs,
    getInventory,
    getOrdersByPhone,
    getVisitorById,
    getVisitorOrders,
    getPiers,
    getRouteProducts,
    getRoutes,
    getVisitors,
    deleteOfflineSaleNotice,
    deletePier,
    deleteRouteProduct,
    postOfflineSaleNotice,
    postPier,
    postRouteProduct,
    postVisitor,
    putOfflineSaleNotice,
    putPier,
    putRouteProduct,
  };
}

module.exports = {
  createManageController,
};
