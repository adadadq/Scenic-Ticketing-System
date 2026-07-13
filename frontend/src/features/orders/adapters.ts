import type { MyOrderDetail, OrderSummary } from '../../shared/api/types'
import { scenicProductName, scenicTicketName } from '../../shared/display/scenicText'
import { formatSlotLabel, maskPhone, orderStatusMeta, parseOrderAmount } from './orderDisplay'
import type { OrderDetail, OrderListItem } from './types'

export function mapOrderSummary(order: OrderSummary): OrderListItem {
  const status = orderStatusMeta[order.orderStatus] ?? { label: order.orderStatus, tone: 'default' }
  const firstItem = order.items[0]

  return {
    orderNo: order.orderNo,
    orderStatus: order.orderStatus,
    orderStatusLabel: status.label,
    orderStatusTone: status.tone,
    paymentStatus: order.paymentStatus,
    productName: firstItem ? scenicProductName(firstItem.productName) : '订单详情中查看',
    ticketName: firstItem ? scenicTicketName(firstItem.ticketName) : '订单详情中查看',
    visitDate: firstItem?.visitDate ?? '',
    timeSlotLabel: formatSlotLabel(firstItem?.slotStartTime, firstItem?.slotEndTime),
    payableAmount: parseOrderAmount(order.payableAmount),
    itemCount: order.items.length,
    orderTime: order.orderTime,
  }
}

export function mapOrderDetail(order: MyOrderDetail): OrderDetail {
  return {
    ...mapOrderSummary(order),
    contactName: order.buyerName,
    contactPhoneMasked: maskPhone(order.buyerPhone),
    ticketCodes: order.items.flatMap((item) => (
      item.itemStatus !== 'REFUNDED' && item.ticketCode ? [item.ticketCode] : []
    )),
    canSelfRefund: order.canSelfRefund,
    refundDeadline: order.refundDeadline,
  }
}
