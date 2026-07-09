const crypto = require('node:crypto');
const { AppError } = require('../utils/app-error');
const { isNonEmptyString, parseDateString, parsePositiveInteger } = require('../utils/validators');
const { createOrderQuery } = require('../db/queries/order.query');

function parseMoney(value) {
  const amount = Number(value);

  if (!Number.isFinite(amount)) {
    throw new AppError(400, 'sale price must be a valid number');
  }

  return amount;
}

function roundMoney(value) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

function generateOrderNo() {
  const now = new Date();
  const timestamp = now.toISOString().replace(/[-:TZ.]/g, '');
  const randomSuffix = crypto.randomBytes(4).toString('hex').toUpperCase();

  return `ORD${timestamp}${randomSuffix}`;
}

function createOrderService(options = {}) {
  const orderQuery = options.orderQuery || createOrderQuery(options);

  function validateOrderPayload(payload = {}) {
    const buyerName = payload.buyerName;
    const buyerPhone = payload.buyerPhone;
    const orderSource = payload.orderSource;
    const items = payload.items;

    if (!isNonEmptyString(buyerName)) {
      throw new AppError(400, 'buyerName is required');
    }

    if (!isNonEmptyString(buyerPhone)) {
      throw new AppError(400, 'buyerPhone is required');
    }

    if (!isNonEmptyString(orderSource)) {
      throw new AppError(400, 'orderSource is required');
    }

    if (!Array.isArray(items) || items.length === 0) {
      throw new AppError(400, 'items must be a non-empty array');
    }

    return {
      buyerName: buyerName.trim(),
      buyerPhone: buyerPhone.trim(),
      orderSource: orderSource.trim(),
      items: items.map((item, index) => ({
        ticketTypeId: parsePositiveInteger(item?.ticketTypeId, `items[${index}].ticketTypeId`),
        visitorId: parsePositiveInteger(item?.visitorId, `items[${index}].visitorId`),
        timeSlotId: parsePositiveInteger(item?.timeSlotId, `items[${index}].timeSlotId`),
        visitDate: parseDateString(item?.visitDate, `items[${index}].visitDate`),
      })),
    };
  }

  function ensureOrderQueryFunction(name) {
    if (typeof orderQuery[name] !== 'function') {
      throw new AppError(503, 'database is unavailable');
    }
  }

  async function createOrder(payload = {}) {
    const normalized = validateOrderPayload(payload);

    ensureOrderQueryFunction('withTransaction');
    ensureOrderQueryFunction('findTicketTypeById');
    ensureOrderQueryFunction('lockTimeSlotQuota');
    ensureOrderQueryFunction('insertOrder');
    ensureOrderQueryFunction('insertOrderItem');
    ensureOrderQueryFunction('updateTimeSlotQuotaSold');

    return orderQuery.withTransaction(async (client) => {
      const resolvedItems = [];
      const reservedQuotaBySlot = new Map();
      let totalAmount = 0;
      let scenicSpotId = null;

      for (const item of normalized.items) {
        const ticketType = await orderQuery.findTicketTypeById(client, item.ticketTypeId);
        if (!ticketType) {
          throw new AppError(404, 'ticket type not found');
        }

        if (scenicSpotId === null) {
          scenicSpotId = ticketType.scenicSpotId;
        } else if (Number(ticketType.scenicSpotId) !== Number(scenicSpotId)) {
          throw new AppError(400, 'all items must belong to the same scenic spot');
        }

        const timeSlot = await orderQuery.lockTimeSlotQuota(client, item.timeSlotId, item.visitDate);
        if (!timeSlot) {
          throw new AppError(404, 'time slot not found');
        }

        if (Number(timeSlot.ticketTypeId) !== Number(ticketType.id)) {
          throw new AppError(400, 'time slot does not match ticket type');
        }

        const slotKey = `${item.timeSlotId}:${item.visitDate}`;
        const reservedCount = reservedQuotaBySlot.get(slotKey) || 0;
        const remainingQuota = timeSlot.quotaTotal - timeSlot.quotaSold - reservedCount;

        if (remainingQuota <= 0) {
          throw new AppError(409, 'time slot quota is not enough');
        }

        reservedQuotaBySlot.set(slotKey, reservedCount + 1);

        const originalPrice = parseMoney(ticketType.salePrice);
        totalAmount = roundMoney(totalAmount + originalPrice);

        resolvedItems.push({
          ...item,
          ticketType,
          timeSlot,
          originalPrice,
        });
      }

      const orderNo = generateOrderNo();
      const now = new Date().toISOString();
      const order = await orderQuery.insertOrder(client, {
        orderNo,
        scenicSpotId,
        buyerName: normalized.buyerName,
        buyerPhone: normalized.buyerPhone,
        orderSource: normalized.orderSource,
        orderStatus: 'PAID',
        paymentStatus: 'PAID',
        totalAmount,
        discountAmount: 0,
        payableAmount: totalAmount,
        paidAmount: totalAmount,
        paidAt: now,
        cancelTime: null,
        remark: null,
      });

      if (!order) {
        throw new AppError(500, 'failed to create order');
      }

      const createdItems = [];
      for (let index = 0; index < resolvedItems.length; index += 1) {
        const item = resolvedItems[index];
        const suffix = String(index + 1).padStart(2, '0');
        const itemNo = `${order.orderNo}-${suffix}`;
        const ticketCode = `TC${order.orderNo}${suffix}`;

        const orderItem = await orderQuery.insertOrderItem(client, {
          orderId: order.id,
          ticketTypeId: item.ticketTypeId,
          visitorId: item.visitorId,
          timeSlotId: item.timeSlotId,
          itemNo,
          visitDate: item.visitDate,
          originalPrice: item.originalPrice,
          discountAmount: 0,
          finalPrice: item.originalPrice,
          itemStatus: 'UNUSED',
          ticketCode,
        });

        if (!orderItem) {
          throw new AppError(500, 'failed to create order item');
        }

        const quotaUpdate = await orderQuery.updateTimeSlotQuotaSold(client, item.timeSlotId, 1);
        if (!quotaUpdate) {
          throw new AppError(500, 'failed to update time slot quota');
        }

        createdItems.push(orderItem);
      }

      return {
        success: true,
        message: 'order created',
        data: {
          orderId: order.id,
          orderNo: order.orderNo,
          totalAmount,
          itemCount: createdItems.length,
          items: createdItems.map((item, index) => {
            const resolvedItem = resolvedItems[index];
            return {
              orderItemId: item.id,
              itemNo: item.itemNo,
              ticketCode: item.ticketCode,
              ticketTypeId: resolvedItem.ticketType.ticketTypeId,
              productName: resolvedItem.ticketType.productName,
              tripType: resolvedItem.ticketType.tripType,
              raftCapacity: resolvedItem.ticketType.raftCapacity,
              windowPhone: resolvedItem.ticketType.windowPhone,
            };
          }),
        },
      };
    });
  }

  return {
    createOrder,
  };
}

module.exports = {
  createOrderService,
};
