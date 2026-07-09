const { AppError } = require('../utils/app-error');
const { formatDateInAsiaShanghai } = require('../utils/date');
const { parseDateString, parsePositiveInteger } = require('../utils/validators');
const { createTicketQuery } = require('../db/queries/ticket.query');

const DEFAULT_SCENIC_SPOT_ID = 1;

function parseMoney(value, fieldName) {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    throw new AppError(400, `${fieldName} must be a valid number`);
  }

  return amount;
}

function parseNonNegativeInteger(value, fieldName) {
  const parsed = Number(value);

  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new AppError(400, `${fieldName} must be a non-negative integer`);
  }

  return parsed;
}

function normalizeBoolean(value, fallback = true) {
  if (value === undefined || value === null || value === '') {
    return fallback;
  }

  if (typeof value === 'boolean') {
    return value;
  }

  const normalized = String(value).trim().toLowerCase();
  if (['true', '1', 'yes', 'on'].includes(normalized)) {
    return true;
  }

  if (['false', '0', 'no', 'off'].includes(normalized)) {
    return false;
  }

  return fallback;
}

function normalizeTimeOfDay(value, fieldName) {
  const text = String(value || '').trim();
  if (!text) {
    throw new AppError(400, `${fieldName} is required`);
  }

  const match = text.match(/^([01]\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?$/);
  if (!match) {
    throw new AppError(400, `${fieldName} must be in HH:MM format`);
  }

  return `${match[1]}:${match[2]}:${match[3] || '00'}`;
}

function normalizeTimeSlot(timeSlot) {
  const quotaTotal = Number(timeSlot.quotaTotal);
  const quotaSold = Number(timeSlot.quotaSold);

  return {
    ...timeSlot,
    visitDate: formatDateInAsiaShanghai(timeSlot.visitDate),
    quotaTotal,
    quotaSold,
    quotaCheckedIn: Number(timeSlot.quotaCheckedIn),
    remainingQuota: Number.isFinite(quotaTotal) && Number.isFinite(quotaSold)
      ? quotaTotal - quotaSold
      : timeSlot.remainingQuota,
  };
}

function normalizeRouteProduct(routeProduct) {
  return {
    id: Number(routeProduct.id),
    ticketTypeId: Number(routeProduct.ticketTypeId),
    productName: routeProduct.productName,
    tripType: routeProduct.tripType,
    raftCapacity: Number(routeProduct.raftCapacity),
    windowPhone: routeProduct.windowPhone,
    saleStatus: routeProduct.saleStatus,
  };
}

function normalizePier(pier) {
  return {
    id: Number(pier.id),
    scenicSpotId: Number(pier.scenicSpotId),
    pierName: pier.pierName,
    pierType: pier.pierType,
    contactPhone: pier.contactPhone,
    status: pier.status,
    sortNo: Number(pier.sortNo),
  };
}

function normalizeAdminRouteProduct(routeProduct) {
  return {
    id: Number(routeProduct.id),
    scenicSpotId: Number(routeProduct.scenicSpotId),
    ticketTypeId: Number(routeProduct.ticketTypeId),
    productName: routeProduct.productName,
    ticketName: routeProduct.ticketName,
    ticketCategory: routeProduct.ticketCategory,
    originalPrice: routeProduct.originalPrice,
    salePrice: routeProduct.salePrice,
    raftCapacity: Number(routeProduct.raftCapacity),
    tripType: routeProduct.tripType,
    startPierId: Number(routeProduct.startPierId),
    startPierName: routeProduct.startPierName,
    endPierId: Number(routeProduct.endPierId),
    endPierName: routeProduct.endPierName,
    windowPhone: routeProduct.windowPhone,
    routeStatus: routeProduct.routeStatus,
    ticketStatus: routeProduct.ticketStatus,
    saleStatus: routeProduct.saleStatus,
  };
}

function normalizeAdminTimeSlot(timeSlot) {
  return normalizeTimeSlot(timeSlot);
}

function createTicketService(options = {}) {
  const ticketQuery = options.ticketQuery || createTicketQuery(options);

  async function getTicketTypes() {
    if (typeof ticketQuery.findTicketTypes !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const data = await ticketQuery.findTicketTypes();
    return {
      success: true,
      message: 'ticket types retrieved',
      data,
    };
  }

  async function getTimeSlots(params = {}) {
    const ticketTypeId = parsePositiveInteger(params.ticketTypeId, 'ticketTypeId');
    const visitDate = parseDateString(params.visitDate, 'visitDate');

    if (typeof ticketQuery.findTimeSlotsByTicketTypeAndDate !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const data = (await ticketQuery.findTimeSlotsByTicketTypeAndDate(ticketTypeId, visitDate))
      .map(normalizeTimeSlot);
    return {
      success: true,
      message: 'time slots retrieved',
      data,
    };
  }

  async function getRouteProducts() {
    if (typeof ticketQuery.findRouteProducts !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const data = (await ticketQuery.findRouteProducts()).map(normalizeRouteProduct);

    return {
      success: true,
      message: 'route products loaded',
      data,
    };
  }

  async function getPiers() {
    if (typeof ticketQuery.findPiers !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const data = (await ticketQuery.findPiers()).map(normalizePier);

    return {
      success: true,
      message: 'piers retrieved',
      data,
    };
  }

  async function getAdminRouteProducts() {
    if (typeof ticketQuery.findAdminRouteProducts !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const data = (await ticketQuery.findAdminRouteProducts()).map(normalizeAdminRouteProduct);

    return {
      success: true,
      message: 'admin route products retrieved',
      data,
    };
  }

  async function getAdminTimeSlots(params = {}) {
    const routeProductId = parsePositiveInteger(params.routeProductId, 'routeProductId');
    const visitDate = parseDateString(params.visitDate, 'visitDate');

    if (typeof ticketQuery.findAdminRouteProductById !== 'function'
      || typeof ticketQuery.findAdminTimeSlotsByTicketTypeAndDate !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const routeProduct = await ticketQuery.findAdminRouteProductById(routeProductId);
    if (!routeProduct) {
      throw new AppError(404, 'route product not found');
    }

    const data = (await ticketQuery.findAdminTimeSlotsByTicketTypeAndDate(
      routeProduct.ticketTypeId,
      visitDate,
    )).map(normalizeAdminTimeSlot);

    return {
      success: true,
      message: 'admin time slots retrieved',
      data,
    };
  }

  function validateAdminRouteProductPayload(payload = {}) {
    const productName = payload.productName;
    const ticketName = payload.ticketName;
    const tripType = payload.tripType;
    const startPierId = parsePositiveInteger(payload.startPierId, 'startPierId');
    const endPierId = parsePositiveInteger(payload.endPierId, 'endPierId');
    const raftCapacity = parsePositiveInteger(payload.raftCapacity, 'raftCapacity');
    const originalPrice = parseMoney(payload.originalPrice, 'originalPrice');
    const salePrice = parseMoney(payload.salePrice, 'salePrice');

    if (!productName || !String(productName).trim()) {
      throw new AppError(400, 'productName is required');
    }

    if (!ticketName || !String(ticketName).trim()) {
      throw new AppError(400, 'ticketName is required');
    }

    if (!tripType || !String(tripType).trim()) {
      throw new AppError(400, 'tripType is required');
    }

    if (startPierId === endPierId) {
      throw new AppError(400, 'start and end pier must be different');
    }

    if (salePrice > originalPrice) {
      throw new AppError(400, 'sale price must not exceed original price');
    }

    return {
      scenicSpotId: DEFAULT_SCENIC_SPOT_ID,
      productName: String(productName).trim(),
      ticketName: String(ticketName).trim(),
      ticketCategory: String(payload.ticketCategory || 'RAFT').trim() || 'RAFT',
      tripType: String(tripType).trim(),
      startPierId,
      endPierId,
      raftCapacity,
      originalPrice,
      salePrice,
      windowPhone: payload.windowPhone ? String(payload.windowPhone).trim() : null,
      description: payload.description ? String(payload.description).trim() : null,
      refundRule: payload.refundRule ? String(payload.refundRule).trim() : null,
      isRealNameRequired: normalizeBoolean(payload.isRealNameRequired, true),
      routeStatus: String(payload.routeStatus || 'ENABLED').trim() || 'ENABLED',
      ticketStatus: String(payload.ticketStatus || 'ENABLED').trim() || 'ENABLED',
    };
  }

  function validateAdminTimeSlotPayload(payload = {}) {
    const routeProductId = parsePositiveInteger(payload.routeProductId, 'routeProductId');
    const visitDate = parseDateString(payload.visitDate, 'visitDate');
    const slotStartTime = normalizeTimeOfDay(payload.slotStartTime, 'slotStartTime');
    const slotEndTime = normalizeTimeOfDay(payload.slotEndTime, 'slotEndTime');
    const quotaTotal = parseNonNegativeInteger(payload.quotaTotal, 'quotaTotal');
    const status = String(payload.status || 'ENABLED').trim() || 'ENABLED';

    if (slotEndTime <= slotStartTime) {
      throw new AppError(400, 'slot end time must be after start time');
    }

    if (!['ENABLED', 'DISABLED'].includes(status)) {
      throw new AppError(400, 'status must be ENABLED or DISABLED');
    }

    return {
      routeProductId,
      visitDate,
      slotStartTime,
      slotEndTime,
      quotaTotal,
      status,
    };
  }

  async function createRouteProduct(payload = {}) {
    const normalized = validateAdminRouteProductPayload(payload);

    if (typeof ticketQuery.withTransaction !== 'function'
      || typeof ticketQuery.insertTicketType !== 'function'
      || typeof ticketQuery.insertRouteProduct !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    return ticketQuery.withTransaction(async (client) => {
      const ticketType = await ticketQuery.insertTicketType(client, {
        scenicSpotId: normalized.scenicSpotId,
        ticketName: normalized.ticketName,
        ticketCategory: normalized.ticketCategory,
        originalPrice: normalized.originalPrice,
        salePrice: normalized.salePrice,
        description: normalized.description,
        refundRule: normalized.refundRule,
        isRealNameRequired: normalized.isRealNameRequired,
        status: normalized.ticketStatus,
      });

      if (!ticketType) {
        throw new AppError(500, 'failed to create ticket type');
      }

      const routeProduct = await ticketQuery.insertRouteProduct(client, {
        scenicSpotId: normalized.scenicSpotId,
        ticketTypeId: ticketType.id,
        productName: normalized.productName,
        raftCapacity: normalized.raftCapacity,
        tripType: normalized.tripType,
        startPierId: normalized.startPierId,
        endPierId: normalized.endPierId,
        windowPhone: normalized.windowPhone,
        salePrice: normalized.salePrice,
        status: normalized.routeStatus,
      });

      if (!routeProduct) {
        throw new AppError(500, 'failed to create route product');
      }

      return {
        success: true,
        message: 'route product created',
        data: {
          ticketType: {
            id: ticketType.id,
            ticketName: ticketType.ticketName,
          },
          routeProduct: {
            id: routeProduct.id,
            productName: routeProduct.productName,
            ticketTypeId: routeProduct.ticketTypeId,
            startPierId: routeProduct.startPierId,
            endPierId: routeProduct.endPierId,
            status: routeProduct.status,
          },
        },
      };
    });
  }

  async function saveAdminTimeSlot(payload = {}) {
    const normalized = validateAdminTimeSlotPayload(payload);

    if (typeof ticketQuery.findAdminRouteProductById !== 'function'
      || typeof ticketQuery.withTransaction !== 'function'
      || typeof ticketQuery.findTimeSlotQuotaByKey !== 'function'
      || typeof ticketQuery.insertTimeSlotQuota !== 'function'
      || typeof ticketQuery.updateTimeSlotQuota !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    const routeProduct = await ticketQuery.findAdminRouteProductById(normalized.routeProductId);
    if (!routeProduct) {
      throw new AppError(404, 'route product not found');
    }

    return ticketQuery.withTransaction(async (client) => {
      const slotInput = {
        ticketTypeId: routeProduct.ticketTypeId,
        visitDate: normalized.visitDate,
        slotStartTime: normalized.slotStartTime,
        slotEndTime: normalized.slotEndTime,
        quotaTotal: normalized.quotaTotal,
        status: normalized.status,
      };
      const existing = await ticketQuery.findTimeSlotQuotaByKey(client, slotInput);

      if (existing && existing.quotaSold > normalized.quotaTotal) {
        throw new AppError(400, 'quotaTotal must not be less than sold quota');
      }

      const timeSlot = existing
        ? await ticketQuery.updateTimeSlotQuota(client, existing.id, slotInput)
        : await ticketQuery.insertTimeSlotQuota(client, slotInput);

      if (!timeSlot) {
        throw new AppError(500, 'failed to save time slot');
      }

      return {
        success: true,
        message: existing ? 'time slot updated' : 'time slot created',
        data: {
          routeProduct: {
            id: routeProduct.id,
            productName: routeProduct.productName,
            ticketTypeId: routeProduct.ticketTypeId,
          },
          timeSlot: normalizeAdminTimeSlot(timeSlot),
        },
      };
    });
  }

  async function disableRouteProduct(routeProductId) {
    const normalizedRouteProductId = parsePositiveInteger(routeProductId, 'routeProductId');

    if (typeof ticketQuery.withTransaction !== 'function'
      || typeof ticketQuery.updateRouteProductStatus !== 'function'
      || typeof ticketQuery.updateTicketTypeStatus !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    return ticketQuery.withTransaction(async (client) => {
      const routeProduct = await ticketQuery.updateRouteProductStatus(client, normalizedRouteProductId, 'DISABLED');
      if (!routeProduct) {
        throw new AppError(404, 'route product not found');
      }

      await ticketQuery.updateTicketTypeStatus(client, routeProduct.ticketTypeId, 'DISABLED');

      return {
        success: true,
        message: 'route product disabled',
        data: {
          routeProductId: routeProduct.id,
          ticketTypeId: routeProduct.ticketTypeId,
          status: routeProduct.status,
        },
      };
    });
  }

  async function restoreRouteProduct(routeProductId) {
    const normalizedRouteProductId = parsePositiveInteger(routeProductId, 'routeProductId');

    if (typeof ticketQuery.withTransaction !== 'function'
      || typeof ticketQuery.updateRouteProductStatus !== 'function'
      || typeof ticketQuery.updateTicketTypeStatus !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }

    return ticketQuery.withTransaction(async (client) => {
      const routeProduct = await ticketQuery.updateRouteProductStatus(client, normalizedRouteProductId, 'ENABLED');
      if (!routeProduct) {
        throw new AppError(404, 'route product not found');
      }

      await ticketQuery.updateTicketTypeStatus(client, routeProduct.ticketTypeId, 'ENABLED');

      return {
        success: true,
        message: 'route product restored',
        data: {
          routeProductId: routeProduct.id,
          ticketTypeId: routeProduct.ticketTypeId,
          status: routeProduct.status,
        },
      };
    });
  }

  return {
    createRouteProduct,
    disableRouteProduct,
    getAdminRouteProducts,
    getAdminTimeSlots,
    getPiers,
    getTicketTypes,
    getTimeSlots,
    getRouteProducts,
    restoreRouteProduct,
    saveAdminTimeSlot,
  };
}

module.exports = {
  createTicketService,
};
