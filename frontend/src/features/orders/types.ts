import type { OrderStatus, OrderStatusFilter, PaymentStatus } from '../../shared/api/types'

export type OrderStatusFilterValue = 'ALL' | OrderStatusFilter

export type OrderStatusTone = 'processing' | 'success' | 'warning' | 'default'

export type OrderListItem = {
  orderNo: string
  orderStatus: OrderStatus
  orderStatusLabel: string
  orderStatusTone: OrderStatusTone
  paymentStatus: PaymentStatus
  productName: string
  ticketName: string
  visitDate: string
  timeSlotLabel: string
  payableAmount: number
  itemCount: number
  orderTime: string
}

export type OrderDetail = OrderListItem & {
  productName: string
  ticketName: string
  contactName: string
  contactPhoneMasked: string
  ticketCodes: string[]
}
