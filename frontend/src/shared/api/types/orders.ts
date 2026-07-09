export type OrderStatus = 'CREATED' | 'PAID' | 'CANCELLED' | 'COMPLETED' | 'REFUNDING' | (string & {})
export type OrderStatusFilter = 'CREATED' | 'PAID' | 'CANCELLED'
export type PaymentStatus = 'UNPAID' | 'PAID' | 'FAILED' | 'REFUNDED' | (string & {})
export type AdminOrderStatus = 'CREATED' | 'PAID' | 'CANCELLED' | 'COMPLETED' | 'REFUNDING' | 'REFUNDED' | (string & {})
export type AdminOrderStatusFilter = 'CREATED' | 'PAID' | 'CANCELLED' | 'COMPLETED' | 'REFUNDING' | 'REFUNDED'
export type AdminPaymentStatus = 'UNPAID' | 'PAID' | 'PARTIAL_REFUND' | 'REFUNDED' | 'FAILED' | (string & {})
export type AdminPaymentStatusFilter = 'UNPAID' | 'PAID' | 'PARTIAL_REFUND' | 'REFUNDED' | 'FAILED'
export type OrderItemStatus =
  | 'PENDING_PAYMENT'
  | 'UNUSED'
  | 'USED'
  | 'REFUNDING'
  | 'REFUNDED'
  | 'CANCELLED'
  | (string & {})

export type OrderCreateItemRequest = {
  productId: number
  timeSlotId: number
  visitDate: string
  quantity: number
  passengers: OrderPassengerRequest[]
}

export type OrderPassengerRequest = {
  passengerName: string
  idType: string
  idNumber: string
  phone: string
  templateId?: number
}

export type OrderCreateRequest = {
  buyerName: string
  buyerPhone: string
  items: OrderCreateItemRequest[]
}

export type OrderItemMe = {
  itemNo: string
  productId: number
  ticketTypeId: number
  productName: string
  ticketName: string
  timeSlotId: number
  visitDate: string
  slotStartTime: string
  slotEndTime: string
  originalPrice: string
  finalPrice: string
  itemStatus: OrderItemStatus
  ticketCode?: string
  passengerName: string
  passengerIdType: string
  passengerIdNumberMasked: string
  passengerPhoneMasked: string
  raftNo?: number | null
  raftSeatNo?: number | null
  raftAssignedAt?: string | null
}

export type OrderMe = {
  orderNo: string
  buyerName: string
  buyerPhone: string
  orderStatus: OrderStatus
  paymentStatus: PaymentStatus
  totalAmount: string
  payableAmount: string
  orderTime: string
  items: OrderItemMe[]
}

export type OrderSummary = OrderMe
export type MyOrderDetail = OrderMe

export type AdminOrderListParams = {
  status?: AdminOrderStatusFilter
  paymentStatus?: AdminPaymentStatusFilter
  orderNo?: string
  buyerPhone?: string
  page?: number
  pageSize?: number
}

export type AdminOrderSummary = {
  orderNo: string
  visitorId: number
  buyerName: string
  buyerPhoneMasked: string
  orderStatus: AdminOrderStatus
  paymentStatus: AdminPaymentStatus
  totalAmount: string
  payableAmount: string
  orderTime: string
  itemCount: number
}

export type AdminOrderList = {
  items: AdminOrderSummary[]
  total: number
  page: number
  pageSize: number
}

export type AdminOrderItem = {
  itemNo: string
  productId: number
  ticketTypeId: number
  productName: string
  ticketName: string
  timeSlotId: number
  visitDate: string
  slotStartTime: string
  slotEndTime: string
  originalPrice: string
  finalPrice: string
  itemStatus: OrderItemStatus
  ticketCode?: string | null
  passengerName: string
  passengerIdType: string
  passengerIdNumberMasked: string
  passengerPhoneMasked: string
  raftNo?: number | null
  raftSeatNo?: number | null
  raftAssignedAt?: string | null
}

export type AdminOrderDetail = {
  orderNo: string
  visitorId: number
  buyerName: string
  buyerPhoneMasked: string
  orderStatus: AdminOrderStatus
  paymentStatus: AdminPaymentStatus
  totalAmount: string
  payableAmount: string
  orderTime: string
  items: AdminOrderItem[]
}
