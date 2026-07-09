const { AppError } = require('../utils/app-error');
const { isNonEmptyString, parseDateString, parsePositiveInteger } = require('../utils/validators');
const { createManageQuery } = require('../db/queries/manage.query');

function parseMaybePositiveInteger(value, fieldName) {
  if (value === undefined || value === null || value === '') {
    return null;
  }

  return parsePositiveInteger(value, fieldName);
}

function parseMoney(value, fieldName) {
  const amount = Number(value);

  if (!Number.isFinite(amount) || amount < 0) {
    throw new AppError(400, `${fieldName} must be a valid non-negative number`);
  }

  return Math.round((amount + Number.EPSILON) * 100) / 100;
}

function parseNonNegativeInteger(value, fieldName) {
  const parsed = Number(value);

  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new AppError(400, `${fieldName} must be a non-negative integer`);
  }

  return parsed;
}

function normalizeNullableString(value) {
  if (value === undefined || value === null) {
    return null;
  }

  const text = String(value).trim();
  return text === '' ? null : text;
}

function createManageService(options = {}) {
  const manageQuery = options.manageQuery || createManageQuery(options);

  function ensureManageQueryFunction(name) {
    if (typeof manageQuery[name] !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }
  }

  function validateVisitorPayload(payload = {}) {
    if (!isNonEmptyString(payload.visitorName)) {
      throw new AppError(400, 'visitorName is required');
    }

    if (!isNonEmptyString(payload.idType)) {
      throw new AppError(400, 'idType is required');
    }

    if (!isNonEmptyString(payload.idNumber)) {
      throw new AppError(400, 'idNumber is required');
    }

    return {
      visitorName: payload.visitorName.trim(),
      idType: payload.idType.trim(),
      idNumber: payload.idNumber.trim(),
      phone: normalizeNullableString(payload.phone),
      gender: normalizeNullableString(payload.gender),
      birthDate: payload.birthDate ? parseDateString(payload.birthDate, 'birthDate') : null,
    };
  }

  function validatePierPayload(payload = {}) {
    if (!isNonEmptyString(payload.pierName)) {
      throw new AppError(400, 'pierName is required');
    }

    if (!isNonEmptyString(payload.pierType)) {
      throw new AppError(400, 'pierType is required');
    }

    return {
      scenicSpotId: parsePositiveInteger(payload.scenicSpotId, 'scenicSpotId'),
      pierName: payload.pierName.trim(),
      pierType: payload.pierType.trim(),
      contactPhone: normalizeNullableString(payload.contactPhone),
      status: normalizeNullableString(payload.status) || 'ENABLED',
      sortNo: parseNonNegativeInteger(payload.sortNo ?? 0, 'sortNo'),
    };
  }

  function validateRouteProductPayload(payload = {}) {
    if (!isNonEmptyString(payload.productName)) {
      throw new AppError(400, 'productName is required');
    }

    if (!isNonEmptyString(payload.tripType)) {
      throw new AppError(400, 'tripType is required');
    }

    if (!isNonEmptyString(payload.windowPhone)) {
      throw new AppError(400, 'windowPhone is required');
    }

    return {
      scenicSpotId: parsePositiveInteger(payload.scenicSpotId, 'scenicSpotId'),
      ticketTypeId: parsePositiveInteger(payload.ticketTypeId, 'ticketTypeId'),
      productName: payload.productName.trim(),
      raftCapacity: parsePositiveInteger(payload.raftCapacity, 'raftCapacity'),
      tripType: payload.tripType.trim(),
      startPierId: parsePositiveInteger(payload.startPierId, 'startPierId'),
      endPierId: parsePositiveInteger(payload.endPierId, 'endPierId'),
      windowPhone: payload.windowPhone.trim(),
      salePrice: parseMoney(payload.salePrice, 'salePrice'),
      status: normalizeNullableString(payload.status) || 'ENABLED',
    };
  }

  function validateNoticePayload(payload = {}) {
    if (!isNonEmptyString(payload.saleStatus)) {
      throw new AppError(400, 'saleStatus is required');
    }

    return {
      routeProductId: parsePositiveInteger(payload.routeProductId, 'routeProductId'),
      businessDate: parseDateString(payload.businessDate, 'businessDate'),
      saleStatus: payload.saleStatus.trim(),
      remark: normalizeNullableString(payload.remark),
    };
  }

  function validateOrderSearchPhone(phone) {
    if (!isNonEmptyString(phone)) {
      throw new AppError(400, 'buyerPhone is required');
    }

    return phone.trim();
  }

  async function listVisitors(filters = {}) {
    ensureManageQueryFunction('listVisitors');
    return manageQuery.listVisitors(filters);
  }

  async function getVisitorById(visitorId) {
    const normalizedVisitorId = parsePositiveInteger(visitorId, 'visitorId');
    ensureManageQueryFunction('findVisitorById');

    const visitor = await manageQuery.findVisitorById(normalizedVisitorId);
    if (!visitor) {
      throw new AppError(404, 'visitor not found');
    }

    return {
      success: true,
      message: 'visitor retrieved',
      data: visitor,
    };
  }

  async function registerVisitor(payload = {}, meta = {}) {
    const normalized = validateVisitorPayload(payload);
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('findVisitorByIdentity');
    ensureManageQueryFunction('insertVisitor');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const existing = await manageQuery.findVisitorByIdentity(normalized.idType, normalized.idNumber);
      if (existing) {
        return {
          success: true,
          message: 'visitor already exists',
          data: existing,
        };
      }

      const visitor = await manageQuery.insertVisitor(client, normalized);
      if (!visitor) {
        throw new AppError(500, 'failed to create visitor');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'VISITOR',
        operationType: 'CREATE',
        targetTable: 'visitor',
        targetId: visitor.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(visitor),
      });

      return {
        success: true,
        message: 'visitor created',
        data: visitor,
      };
    });
  }

  async function listPiers() {
    ensureManageQueryFunction('listPiers');
    return manageQuery.listPiers();
  }

  async function createPier(payload = {}, meta = {}) {
    const normalized = validatePierPayload(payload);
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('insertPier');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const pier = await manageQuery.insertPier(client, normalized);
      if (!pier) {
        throw new AppError(500, 'failed to create pier');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'PIER',
        operationType: 'CREATE',
        targetTable: 'pier',
        targetId: pier.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(pier),
      });

      return {
        success: true,
        message: 'pier created',
        data: pier,
      };
    });
  }

  async function updatePier(id, payload = {}, meta = {}) {
    const normalized = validatePierPayload(payload);
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('updatePier');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const pier = await manageQuery.updatePier(client, id, normalized);
      if (!pier) {
        throw new AppError(404, 'pier not found');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'PIER',
        operationType: 'UPDATE',
        targetTable: 'pier',
        targetId: pier.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(pier),
      });

      return {
        success: true,
        message: 'pier updated',
        data: pier,
      };
    });
  }

  async function deletePier(id, meta = {}) {
    const normalizedId = parsePositiveInteger(id, 'id');
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('disablePier');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const pier = await manageQuery.disablePier(client, normalizedId);
      if (!pier) {
        throw new AppError(404, 'pier not found');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'PIER',
        operationType: 'DELETE',
        targetTable: 'pier',
        targetId: pier.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(pier),
      });

      return {
        success: true,
        message: 'pier disabled',
        data: pier,
      };
    });
  }

  async function listRouteProducts(filters = {}) {
    ensureManageQueryFunction('listRouteProducts');
    return manageQuery.listRouteProducts(filters);
  }

  async function createRouteProduct(payload = {}, meta = {}) {
    const normalized = validateRouteProductPayload(payload);
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('insertRouteProduct');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const routeProduct = await manageQuery.insertRouteProduct(client, normalized);
      if (!routeProduct) {
        throw new AppError(500, 'failed to create route product');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'ROUTE_PRODUCT',
        operationType: 'CREATE',
        targetTable: 'route_product',
        targetId: routeProduct.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(routeProduct),
      });

      return {
        success: true,
        message: 'route product created',
        data: routeProduct,
      };
    });
  }

  async function updateRouteProduct(id, payload = {}, meta = {}) {
    const normalized = validateRouteProductPayload(payload);
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('updateRouteProduct');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const routeProduct = await manageQuery.updateRouteProduct(client, id, normalized);
      if (!routeProduct) {
        throw new AppError(404, 'route product not found');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'ROUTE_PRODUCT',
        operationType: 'UPDATE',
        targetTable: 'route_product',
        targetId: routeProduct.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(routeProduct),
      });

      return {
        success: true,
        message: 'route product updated',
        data: routeProduct,
      };
    });
  }

  async function deleteRouteProduct(id, meta = {}) {
    const normalizedId = parsePositiveInteger(id, 'id');
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('disableRouteProduct');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const routeProduct = await manageQuery.disableRouteProduct(client, normalizedId);
      if (!routeProduct) {
        throw new AppError(404, 'route product not found');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'ROUTE_PRODUCT',
        operationType: 'DELETE',
        targetTable: 'route_product',
        targetId: routeProduct.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(routeProduct),
      });

      return {
        success: true,
        message: 'route product disabled',
        data: routeProduct,
      };
    });
  }

  async function listOfflineSaleNotices(filters = {}) {
    ensureManageQueryFunction('listOfflineSaleNotices');
    return manageQuery.listOfflineSaleNotices(filters);
  }

  async function upsertOfflineSaleNotice(payload = {}, meta = {}) {
    const normalized = validateNoticePayload(payload);
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('findOfflineSaleNoticeByRouteDate');
    ensureManageQueryFunction('insertOfflineSaleNotice');
    ensureManageQueryFunction('updateOfflineSaleNotice');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const existing = await manageQuery.findOfflineSaleNoticeByRouteDate(
        client,
        normalized.routeProductId,
        normalized.businessDate,
      );

      const notice = existing
        ? await manageQuery.updateOfflineSaleNotice(client, existing.id, normalized)
        : await manageQuery.insertOfflineSaleNotice(client, normalized);

      if (!notice) {
        throw new AppError(500, 'failed to save sale notice');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'OFFLINE_SALE_NOTICE',
        operationType: existing ? 'UPDATE' : 'CREATE',
        targetTable: 'offline_sale_notice',
        targetId: notice.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(notice),
      });

      return {
        success: true,
        message: existing ? 'sale notice updated' : 'sale notice created',
        data: notice,
      };
    });
  }

  async function updateOfflineSaleNotice(id, payload = {}, meta = {}) {
    const normalizedId = parsePositiveInteger(id, 'id');
    const normalized = validateNoticePayload(payload);
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('updateOfflineSaleNotice');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const notice = await manageQuery.updateOfflineSaleNotice(client, normalizedId, normalized);
      if (!notice) {
        throw new AppError(404, 'sale notice not found');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'OFFLINE_SALE_NOTICE',
        operationType: 'UPDATE',
        targetTable: 'offline_sale_notice',
        targetId: notice.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(notice),
      });

      return {
        success: true,
        message: 'sale notice updated',
        data: notice,
      };
    });
  }

  async function deleteOfflineSaleNotice(id, meta = {}) {
    const normalizedId = parsePositiveInteger(id, 'id');
    ensureManageQueryFunction('withTransaction');
    ensureManageQueryFunction('closeOfflineSaleNotice');
    ensureManageQueryFunction('insertOperationLog');

    return manageQuery.withTransaction(async (client) => {
      const notice = await manageQuery.closeOfflineSaleNotice(client, normalizedId);
      if (!notice) {
        throw new AppError(404, 'sale notice not found');
      }

      await manageQuery.insertOperationLog(client, {
        operatorId: meta.operatorId || 1,
        moduleName: 'OFFLINE_SALE_NOTICE',
        operationType: 'DELETE',
        targetTable: 'offline_sale_notice',
        targetId: notice.id,
        operationResult: 'SUCCESS',
        requestIp: meta.requestIp || '127.0.0.1',
        detailJson: JSON.stringify(notice),
      });

      return {
        success: true,
        message: 'sale notice closed',
        data: notice,
      };
    });
  }

  async function searchOrdersByPhone(buyerPhone) {
    const normalizedPhone = validateOrderSearchPhone(buyerPhone);
    ensureManageQueryFunction('listOrdersByPhone');
    return {
      success: true,
      message: 'orders retrieved',
      data: await manageQuery.listOrdersByPhone(normalizedPhone),
    };
  }

  async function listOrdersByVisitorId(visitorId) {
    const normalizedVisitorId = parsePositiveInteger(visitorId, 'visitorId');
    ensureManageQueryFunction('listOrdersByVisitorId');
    return {
      success: true,
      message: 'visitor orders retrieved',
      data: await manageQuery.listOrdersByVisitorId(normalizedVisitorId),
    };
  }

  async function listInventory(filters = {}) {
    ensureManageQueryFunction('listInventory');
    const normalized = {
      ticketTypeId: filters.ticketTypeId ? parsePositiveInteger(filters.ticketTypeId, 'ticketTypeId') : null,
      visitDate: filters.visitDate ? parseDateString(filters.visitDate, 'visitDate') : null,
    };

    return {
      success: true,
      message: 'inventory retrieved',
      data: await manageQuery.listInventory(normalized),
    };
  }

  async function listOperationLogs(limit) {
    ensureManageQueryFunction('listOperationLogs');
    const normalizedLimit = limit ? parsePositiveInteger(limit, 'limit') : 50;
    return {
      success: true,
      message: 'operation logs retrieved',
      data: await manageQuery.listOperationLogs(Math.min(normalizedLimit, 200)),
    };
  }

  return {
    createPier,
    createRouteProduct,
    deleteOfflineSaleNotice,
    deletePier,
    deleteRouteProduct,
    getVisitorById,
    listOfflineSaleNotices,
    listOperationLogs,
    listInventory,
    listOrdersByPhone: searchOrdersByPhone,
    listOrdersByVisitorId,
    listPiers,
    listRouteProducts,
    listVisitors,
    registerVisitor,
    updateOfflineSaleNotice,
    updatePier,
    updateRouteProduct,
    upsertOfflineSaleNotice,
  };
}

module.exports = {
  createManageService,
};
