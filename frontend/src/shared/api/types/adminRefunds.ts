import type { AdminOrderStatus, AdminPaymentStatus } from './orders'

export type AdminRefundRequest = {
  reason?: string
}

export type AdminRefund = {
  orderNo: string
  orderStatus: AdminOrderStatus
  paymentStatus: AdminPaymentStatus
  refundedAmount: string
  refundedItemCount: number
  refundedAt: string
}

export type AdminPartialRefundRequest = {
  itemNos: string[]
  reason?: string
}

export type AdminPartialRefund = {
  orderNo: string
  orderStatus: AdminOrderStatus
  paymentStatus: AdminPaymentStatus
  refundedAmount: string
  refundedItemCount: number
  refundedItemNos: string[]
  refundedAt: string
}

export type AdminRefundType = 'FULL' | 'PARTIAL'

export type AdminRefundAuditLog = {
  orderNo: string
  refundType: AdminRefundType
  refundedAmount: string
  refundedItemCount: number
  refundedItemNos: string[]
  reason: string | null
  operatorUsername: string
  operatorDisplayName: string
  requestId: string | null
  createdAt: string
}

export type AdminRefundAuditLogParams = {
  refundType?: AdminRefundType
  orderNo?: string
  operatorUsername?: string
  dateFrom?: string
  dateTo?: string
  page?: number
  pageSize?: number
}

export type AdminRefundAuditLogExportParams = {
  refundType?: AdminRefundType
  orderNo?: string
  operatorUsername?: string
  dateFrom?: string
  dateTo?: string
}

export type AdminRefundAuditLogList = {
  items: AdminRefundAuditLog[]
  total: number
  page: number
  pageSize: number
}
