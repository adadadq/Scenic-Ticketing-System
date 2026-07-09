const { AppError } = require('../utils/app-error');
const { isNonEmptyString, parseDateString, parsePositiveInteger } = require('../utils/validators');
const { createVisitorQuery } = require('../db/queries/visitor.query');

function normalizeOptionalText(value) {
  if (typeof value !== 'string') {
    return null;
  }

  const trimmed = value.trim();
  return trimmed === '' ? null : trimmed;
}

function createVisitorService(options = {}) {
  const visitorQuery = options.visitorQuery || createVisitorQuery(options);

  function ensureVisitorQueryFunction(name) {
    if (typeof visitorQuery[name] !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }
  }

  function validateVisitorPayload(payload = {}) {
    const visitorName = payload.visitorName;
    const idType = payload.idType;
    const idNumber = payload.idNumber;

    if (!isNonEmptyString(visitorName)) {
      throw new AppError(400, 'visitorName is required');
    }

    if (!isNonEmptyString(idType)) {
      throw new AppError(400, 'idType is required');
    }

    if (!isNonEmptyString(idNumber)) {
      throw new AppError(400, 'idNumber is required');
    }

    const birthDate = payload.birthDate ? parseDateString(payload.birthDate, 'birthDate') : null;

    return {
      visitorName: visitorName.trim(),
      idType: idType.trim(),
      idNumber: idNumber.trim(),
      phone: normalizeOptionalText(payload.phone),
      gender: normalizeOptionalText(payload.gender),
      birthDate,
    };
  }

  function normalizeVisitor(visitor) {
    if (!visitor) {
      return null;
    }

    return {
      id: Number(visitor.id),
      visitorName: visitor.visitorName,
      idType: visitor.idType,
      idNumber: visitor.idNumber,
      phone: visitor.phone,
      gender: visitor.gender,
      birthDate: visitor.birthDate,
    };
  }

  function groupVisitorOrders(rows) {
    const ordersById = new Map();

    for (const row of rows) {
      const orderId = Number(row.orderId);
      if (!ordersById.has(orderId)) {
        ordersById.set(orderId, {
          orderId,
          orderNo: row.orderNo,
          orderStatus: row.orderStatus,
          paymentStatus: row.paymentStatus,
          orderSource: row.orderSource,
          buyerName: row.buyerName,
          buyerPhone: row.buyerPhone,
          totalAmount: Number(row.totalAmount),
          discountAmount: Number(row.discountAmount),
          payableAmount: Number(row.payableAmount),
          paidAmount: Number(row.paidAmount),
          orderTime: row.orderTime,
          paidAt: row.paidAt,
          cancelTime: row.cancelTime,
          items: [],
        });
      }

      ordersById.get(orderId).items.push({
        orderItemId: Number(row.orderItemId),
        itemNo: row.itemNo,
        ticketCode: row.ticketCode,
        visitDate: row.visitDate,
        originalPrice: Number(row.originalPrice),
        itemDiscountAmount: Number(row.itemDiscountAmount),
        finalPrice: Number(row.finalPrice),
        itemStatus: row.itemStatus,
        ticketTypeId: Number(row.ticketTypeId),
        ticketName: row.ticketName,
        productName: row.productName,
        tripType: row.tripType,
        windowPhone: row.windowPhone,
      });
    }

    return Array.from(ordersById.values());
  }

  async function registerVisitor(payload = {}) {
    const normalized = validateVisitorPayload(payload);

    ensureVisitorQueryFunction('findVisitorByIdentity');
    ensureVisitorQueryFunction('findVisitorByPhone');
    ensureVisitorQueryFunction('insertVisitor');
    ensureVisitorQueryFunction('updateVisitorByIdentity');
    ensureVisitorQueryFunction('updateVisitorByPhone');

    const existingByPhone = await visitorQuery.findVisitorByPhone(normalized.phone);
    if (existingByPhone) {
      const updated = await visitorQuery.updateVisitorByPhone(normalized);
      return {
        success: true,
        message: 'visitor registered',
        data: normalizeVisitor(updated || existingByPhone),
      };
    }

    const existing = await visitorQuery.findVisitorByIdentity(normalized.idType, normalized.idNumber);
    if (existing) {
      const updated = await visitorQuery.updateVisitorByIdentity(normalized);
      return {
        success: true,
        message: 'visitor registered',
        data: normalizeVisitor(updated || existing),
      };
    }

    try {
      const created = await visitorQuery.insertVisitor(normalized);
      return {
        success: true,
        message: 'visitor registered',
        data: normalizeVisitor(created),
      };
    } catch (error) {
      if (error && error.code === '23505') {
        const latest = await visitorQuery.findVisitorByIdentity(normalized.idType, normalized.idNumber);
        if (latest) {
          return {
            success: true,
            message: 'visitor registered',
            data: normalizeVisitor(latest),
          };
        }
      }

      throw error;
    }
  }

  async function getVisitor(visitorId) {
    const normalizedVisitorId = parsePositiveInteger(visitorId, 'visitorId');
    ensureVisitorQueryFunction('findVisitorById');

    const visitor = await visitorQuery.findVisitorById(normalizedVisitorId);
    if (!visitor) {
      throw new AppError(404, 'visitor not found');
    }

    return {
      success: true,
      message: 'visitor loaded',
      data: normalizeVisitor(visitor),
    };
  }

  async function getVisitorOrders(visitorId) {
    const normalizedVisitorId = parsePositiveInteger(visitorId, 'visitorId');
    ensureVisitorQueryFunction('findVisitorById');
    ensureVisitorQueryFunction('listOrdersByVisitorId');

    const visitor = await visitorQuery.findVisitorById(normalizedVisitorId);
    if (!visitor) {
      throw new AppError(404, 'visitor not found');
    }

    const rows = await visitorQuery.listOrdersByVisitorId(normalizedVisitorId);

    return {
      success: true,
      message: 'visitor orders loaded',
      data: {
        visitor: normalizeVisitor(visitor),
        orders: groupVisitorOrders(rows),
      },
    };
  }

  return {
    getVisitor,
    getVisitorOrders,
    registerVisitor,
  };
}

module.exports = {
  createVisitorService,
};
