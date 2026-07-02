import type { MyOrderDetail, OrderSummary } from '../../shared/api/types'
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
    visitDate: firstItem?.visitDate ?? '',
    timeSlotLabel: formatSlotLabel(firstItem?.slotStartTime, firstItem?.slotEndTime),
    payableAmount: parseOrderAmount(order.payableAmount),
    itemCount: order.items.length,
    orderTime: order.orderTime,
  }
}

export function mapOrderDetail(order: MyOrderDetail): OrderDetail {
  const firstItem = order.items[0]

  return {
    ...mapOrderSummary(order),
    productName: firstItem?.productName ?? '订单详情中查看',
    ticketName: firstItem?.ticketName ?? '订单详情中查看',
    contactName: order.buyerName,
    contactPhoneMasked: maskPhone(order.buyerPhone),
    ticketCodes: order.items.flatMap((item) => (item.ticketCode ? [item.ticketCode] : [])),
  }
}
