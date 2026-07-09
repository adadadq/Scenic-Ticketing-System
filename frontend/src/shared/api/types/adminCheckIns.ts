import type { AdminOrderStatus, OrderItemStatus } from './orders'

export type AdminCheckInRequest = {
  ticketCode: string
}

export type AdminBatchCheckInRequest = {
  ticketCodes: string[]
}

export type AdminBatchUndoCheckInRequest = {
  ticketCodes: string[]
  reason?: string
}

export type AdminCheckIn = {
  orderNo: string
  itemNo: string
  ticketCode: string
  orderStatus: AdminOrderStatus
  itemStatus: OrderItemStatus
  checkedInAt: string
  raftNo?: number | null
  raftSeatNo?: number | null
}

export type AdminUndoCheckIn = {
  orderNo: string
  itemNo: string
  ticketCode: string
  orderStatus: AdminOrderStatus
  itemStatus: OrderItemStatus
  undoneAt: string
}

export type AdminBatchCheckInSuccessResult = {
  ticketCode: string
  success: true
  checkIn: AdminCheckIn
}

export type AdminBatchCheckInFailureResult = {
  ticketCode: string
  success: false
  code: string
  message: string
}

export type AdminBatchCheckInResult = AdminBatchCheckInSuccessResult | AdminBatchCheckInFailureResult

export type AdminBatchCheckIn = {
  totalCount: number
  successCount: number
  failureCount: number
  results: AdminBatchCheckInResult[]
}

export type AdminBatchUndoCheckInSuccessResult = {
  ticketCode: string
  success: true
  undoCheckIn: AdminUndoCheckIn
}

export type AdminBatchUndoCheckInFailureResult = {
  ticketCode: string
  success: false
  code: string
  message: string
}

export type AdminBatchUndoCheckInResult =
  | AdminBatchUndoCheckInSuccessResult
  | AdminBatchUndoCheckInFailureResult

export type AdminBatchUndoCheckIn = {
  totalCount: number
  successCount: number
  failureCount: number
  results: AdminBatchUndoCheckInResult[]
}

export type AdminCheckInAuditLogAction = 'CHECK_IN' | 'UNDO_CHECK_IN'

export type AdminCheckInAuditLog = {
  orderNo: string
  itemNo: string
  ticketCode: string
  action: AdminCheckInAuditLogAction
  reason: string | null
  operatorUsername: string
  operatorDisplayName: string
  requestId: string | null
  createdAt: string
}

export type AdminCheckInAuditLogExportParams = {
  ticketCode?: string
  orderNo?: string
  operatorUsername?: string
  reason?: string
  dateFrom?: string
  dateTo?: string
}

export type AdminCheckInFailureCode =
  | 'TICKET_NOT_FOUND'
  | 'TICKET_ALREADY_USED'
  | 'TICKET_NOT_CHECKABLE'
  | 'TICKET_NOT_CHECKED_IN'
  | 'TICKET_UNDO_NOT_ALLOWED'

export type AdminCheckInFailureAuditLog = {
  ticketCode: string
  action: 'CHECK_IN' | 'UNDO_CHECK_IN'
  failureCode: AdminCheckInFailureCode
  failureMessage: string
  operatorUsername: string
  operatorDisplayName: string
  requestId: string | null
  createdAt: string
}

export type AdminCheckInFailureAuditLogParams = {
  ticketCode?: string
  failureCode?: AdminCheckInFailureCode
  operatorUsername?: string
  dateFrom?: string
  dateTo?: string
  page?: number
  pageSize?: number
}

export type AdminCheckInFailureAuditLogExportParams = {
  ticketCode?: string
  failureCode?: AdminCheckInFailureCode
  operatorUsername?: string
  dateFrom?: string
  dateTo?: string
}

export type AdminCheckInFailureAuditLogList = {
  items: AdminCheckInFailureAuditLog[]
  total: number
  page: number
  pageSize: number
}
