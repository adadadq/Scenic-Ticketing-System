import { ApiError } from '../../shared/api/errors'
import type {
  AdminBatchCheckIn,
  AdminBatchCheckInRequest,
  AdminBatchUndoCheckIn,
  AdminBatchUndoCheckInRequest,
  AdminCheckIn,
  AdminOrderDetail,
  AdminOrderList,
  AdminOrderListParams,
  AdminOrderSummary,
  AdminPartialRefund,
  AdminPartialRefundRequest,
  AdminRefund,
  AdminRefundAuditLog,
  AdminRefundRequest,
  AdminUndoCheckIn,
} from '../../shared/api/types'
import { addMockAdminCheckInAuditLog } from '../admin-check-in-logs/exportXlsx'
import { addMockAdminRefundAuditLog } from '../admin-refund-logs/mockData'
import { mockAdminOrderDetails, mockRefundAuditLogsByOrderNo } from './mockOrderSeeds'

function summaryFromDetail(order: AdminOrderDetail): AdminOrderSummary {
  return {
    orderNo: order.orderNo,
    visitorId: order.visitorId,
    buyerName: order.buyerName,
    buyerPhoneMasked: order.buyerPhoneMasked,
    orderStatus: order.orderStatus,
    paymentStatus: order.paymentStatus,
    totalAmount: order.totalAmount,
    payableAmount: order.payableAmount,
    orderTime: order.orderTime,
    itemCount: order.items.length,
  }
}

function textIncludes(value: string, query?: string) {
  const trimmed = query?.trim()
  return trimmed ? value.toLowerCase().includes(trimmed.toLowerCase()) : true
}

function phoneMatches(maskedPhone: string, query?: string) {
  const trimmed = query?.trim()

  if (!trimmed) {
    return true
  }

  if (/^\d{4}$/.test(trimmed)) {
    return maskedPhone.endsWith(trimmed)
  }

  return maskedPhone.includes(trimmed)
}

export function listMockAdminOrders(params: AdminOrderListParams = {}): AdminOrderList {
  const page = Math.max(1, params.page ?? 1)
  const pageSize = Math.min(100, Math.max(1, params.pageSize ?? 20))
  const filtered = mockAdminOrderDetails
    .filter((order) => !params.status || order.orderStatus === params.status)
    .filter((order) => !params.paymentStatus || order.paymentStatus === params.paymentStatus)
    .filter((order) => textIncludes(order.orderNo, params.orderNo))
    .filter((order) => phoneMatches(order.buyerPhoneMasked, params.buyerPhone))
    .map(summaryFromDetail)
  const start = (page - 1) * pageSize

  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  }
}

export function getMockAdminOrderDetail(orderNo: string) {
  return mockAdminOrderDetails.find((order) => order.orderNo === orderNo) ?? null
}

export function listMockAdminRefundAuditLogs(orderNo: string) {
  return mockRefundAuditLogsByOrderNo[orderNo] ?? []
}

function appendMockRefundAuditLog(orderNo: string, log: AdminRefundAuditLog) {
  const logs = mockRefundAuditLogsByOrderNo[orderNo] ?? []
  logs.unshift(log)
  mockRefundAuditLogsByOrderNo[orderNo] = logs
  addMockAdminRefundAuditLog(log)
}

function amountSum(items: AdminOrderDetail['items']) {
  return items.reduce((sum, item) => sum + Number(item.finalPrice), 0).toFixed(2)
}

function normalizeRefundItemNos(itemNos: string[]) {
  return itemNos.map((itemNo) => itemNo.trim())
}

function throwPartialRefundValidationError(message: string): never {
  throw new ApiError({
    success: false,
    code: 'VALIDATION_ERROR',
    message,
    request_id: 'mock-admin-partial-refund',
  })
}

function hasRemainingCheckableTicket(items: AdminOrderDetail['items']) {
  return items.some((item) => item.itemStatus === 'UNUSED' && Boolean(item.ticketCode))
}

function isCheckInBusinessError(error: unknown): error is ApiError {
  return error instanceof ApiError &&
    ['TICKET_NOT_FOUND', 'TICKET_ALREADY_USED', 'TICKET_NOT_CHECKABLE'].includes(error.code)
}

function isUndoCheckInBusinessError(error: unknown): error is ApiError {
  return error instanceof ApiError &&
    ['TICKET_NOT_FOUND', 'TICKET_NOT_CHECKED_IN', 'TICKET_UNDO_NOT_ALLOWED'].includes(error.code)
}

export function checkInMockAdminTicket(ticketCode: string): AdminCheckIn {
  const normalizedTicketCode = ticketCode.trim()
  const order = mockAdminOrderDetails.find((candidate) =>
    candidate.items.some((item) => item.ticketCode === normalizedTicketCode),
  )
  const item = order?.items.find((candidate) => candidate.ticketCode === normalizedTicketCode)

  if (!order || !item) {
    throw new ApiError({
      success: false,
      code: 'TICKET_NOT_FOUND',
      message: '票码不存在',
      request_id: 'mock-admin-check-in',
    })
  }

  if (item.itemStatus === 'USED') {
    throw new ApiError({
      success: false,
      code: 'TICKET_ALREADY_USED',
      message: '票码已核销',
      request_id: 'mock-admin-check-in',
    })
  }

  if (
    order.orderStatus !== 'PAID' ||
    (order.paymentStatus !== 'PAID' && order.paymentStatus !== 'PARTIAL_REFUND') ||
    item.itemStatus !== 'UNUSED'
  ) {
    throw new ApiError({
      success: false,
      code: 'TICKET_NOT_CHECKABLE',
      message: '当前票码不可核销',
      request_id: 'mock-admin-check-in',
    })
  }

  item.itemStatus = 'USED'

  if (!hasRemainingCheckableTicket(order.items)) {
    order.orderStatus = 'COMPLETED'
  }

  const checkIn: AdminCheckIn = {
    orderNo: order.orderNo,
    itemNo: item.itemNo,
    ticketCode: normalizedTicketCode,
    orderStatus: order.orderStatus,
    itemStatus: item.itemStatus,
    checkedInAt: '2026-06-28T15:32:00+08:00',
  }

  addMockAdminCheckInAuditLog({
    orderNo: checkIn.orderNo,
    itemNo: checkIn.itemNo,
    ticketCode: checkIn.ticketCode,
    action: 'CHECK_IN',
    reason: null,
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'mock-check-in-request-260628-admin',
    createdAt: checkIn.checkedInAt,
  })

  return checkIn
}

function throwBatchCheckInValidationError(message: string): never {
  throw new ApiError({
    success: false,
    code: 'VALIDATION_ERROR',
    message,
    request_id: 'mock-admin-batch-check-in',
  })
}

function throwBatchUndoCheckInValidationError(message: string): never {
  throw new ApiError({
    success: false,
    code: 'VALIDATION_ERROR',
    message,
    request_id: 'mock-admin-batch-undo-check-in',
  })
}

function normalizeUndoCheckInReason(reason?: string) {
  if (reason === undefined) {
    return null
  }

  const trimmed = reason.trim()

  if (!trimmed || trimmed.length > 100) {
    throwBatchUndoCheckInValidationError('撤销核验原因需为 1-100 字')
  }

  return trimmed
}

export function checkInMockAdminTickets(body: AdminBatchCheckInRequest): AdminBatchCheckIn {
  const ticketCodes = body.ticketCodes.map((ticketCode) => ticketCode.trim())
  const uniqueTicketCodes = new Set(ticketCodes)

  if (ticketCodes.length === 0 || ticketCodes.length > 50 || ticketCodes.some((ticketCode) => !ticketCode)) {
    throwBatchCheckInValidationError('核验票码不合法')
  }

  if (uniqueTicketCodes.size !== ticketCodes.length) {
    throwBatchCheckInValidationError('核验票码不能重复')
  }

  const results: AdminBatchCheckIn['results'] = ticketCodes.map((ticketCode) => {
    try {
      return {
        ticketCode,
        success: true as const,
        checkIn: checkInMockAdminTicket(ticketCode),
      }
    } catch (error) {
      if (!isCheckInBusinessError(error)) {
        throw error
      }

      return {
        ticketCode,
        success: false as const,
        code: error.code,
        message: error.message,
      }
    }
  })
  const successCount = results.filter((result) => result.success).length

  return {
    totalCount: results.length,
    successCount,
    failureCount: results.length - successCount,
    results,
  }
}

export function undoCheckInMockAdminTicket(ticketCode: string, reason?: string): AdminUndoCheckIn {
  const normalizedTicketCode = ticketCode.trim()
  const normalizedReason = normalizeUndoCheckInReason(reason)
  const order = mockAdminOrderDetails.find((candidate) =>
    candidate.items.some((item) => item.ticketCode === normalizedTicketCode),
  )
  const item = order?.items.find((candidate) => candidate.ticketCode === normalizedTicketCode)

  if (!order || !item) {
    throw new ApiError({
      success: false,
      code: 'TICKET_NOT_FOUND',
      message: '票码不存在',
      request_id: 'mock-admin-undo-check-in',
    })
  }

  if (item.itemStatus !== 'USED') {
    throw new ApiError({
      success: false,
      code: 'TICKET_NOT_CHECKED_IN',
      message: '票码未核销',
      request_id: 'mock-admin-undo-check-in',
    })
  }

  if (
    (order.orderStatus !== 'PAID' && order.orderStatus !== 'COMPLETED') ||
    (order.paymentStatus !== 'PAID' && order.paymentStatus !== 'PARTIAL_REFUND')
  ) {
    throw new ApiError({
      success: false,
      code: 'TICKET_UNDO_NOT_ALLOWED',
      message: '当前票码不可撤销核销',
      request_id: 'mock-admin-undo-check-in',
    })
  }

  item.itemStatus = 'UNUSED'

  if (order.orderStatus === 'COMPLETED') {
    order.orderStatus = 'PAID'
  }

  const undoCheckIn: AdminUndoCheckIn = {
    orderNo: order.orderNo,
    itemNo: item.itemNo,
    ticketCode: normalizedTicketCode,
    orderStatus: order.orderStatus,
    itemStatus: item.itemStatus,
    undoneAt: '2026-06-28T15:52:00+08:00',
  }

  addMockAdminCheckInAuditLog({
    orderNo: undoCheckIn.orderNo,
    itemNo: undoCheckIn.itemNo,
    ticketCode: undoCheckIn.ticketCode,
    action: 'UNDO_CHECK_IN',
    reason: normalizedReason,
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'mock-undo-check-in-request-260628-admin',
    createdAt: undoCheckIn.undoneAt,
  })

  return undoCheckIn
}

export function undoCheckInMockAdminTickets(body: AdminBatchUndoCheckInRequest): AdminBatchUndoCheckIn {
  const ticketCodes = body.ticketCodes.map((ticketCode) => ticketCode.trim())
  const uniqueTicketCodes = new Set(ticketCodes)
  const normalizedReason = normalizeUndoCheckInReason(body.reason)

  if (ticketCodes.length === 0 || ticketCodes.length > 50 || ticketCodes.some((ticketCode) => !ticketCode)) {
    throwBatchUndoCheckInValidationError('撤销核验票码不合法')
  }

  if (uniqueTicketCodes.size !== ticketCodes.length) {
    throwBatchUndoCheckInValidationError('撤销核验票码不能重复')
  }

  const results: AdminBatchUndoCheckIn['results'] = ticketCodes.map((ticketCode) => {
    try {
      return {
        ticketCode,
        success: true as const,
        undoCheckIn: undoCheckInMockAdminTicket(ticketCode, normalizedReason ?? undefined),
      }
    } catch (error) {
      if (!isUndoCheckInBusinessError(error)) {
        throw error
      }

      return {
        ticketCode,
        success: false as const,
        code: error.code,
        message: error.message,
      }
    }
  })
  const successCount = results.filter((result) => result.success).length

  return {
    totalCount: results.length,
    successCount,
    failureCount: results.length - successCount,
    results,
  }
}

export function refundMockAdminOrder(orderNo: string, body: AdminRefundRequest = {}): AdminRefund {
  const order = mockAdminOrderDetails.find((candidate) => candidate.orderNo === orderNo)

  if (!order) {
    throw new ApiError({
      success: false,
      code: 'ADMIN_ORDER_NOT_FOUND',
      message: '订单不存在',
      request_id: 'mock-admin-refund',
    })
  }

  if (order.orderStatus === 'REFUNDED' || order.paymentStatus === 'REFUNDED') {
    throw new ApiError({
      success: false,
      code: 'ORDER_ALREADY_REFUNDED',
      message: '订单已退款',
      request_id: 'mock-admin-refund',
    })
  }

  if (
    order.orderStatus !== 'PAID' ||
    order.paymentStatus !== 'PAID' ||
    order.items.some((item) => item.itemStatus !== 'UNUSED')
  ) {
    throw new ApiError({
      success: false,
      code: 'ORDER_NOT_REFUNDABLE',
      message: '当前订单不可退款',
      request_id: 'mock-admin-refund',
    })
  }

  const refundedAmount = order.payableAmount
  const refundedItemNos = order.items.map((item) => item.itemNo)
  const refundedAt = '2026-06-28T16:45:00+08:00'

  order.orderStatus = 'REFUNDED'
  order.paymentStatus = 'REFUNDED'
  order.payableAmount = '0.00'
  order.items.forEach((item) => {
    item.itemStatus = 'REFUNDED'
  })

  appendMockRefundAuditLog(order.orderNo, {
    orderNo: order.orderNo,
    refundType: 'FULL',
    refundedAmount,
    refundedItemCount: order.items.length,
    refundedItemNos,
    reason: body.reason?.trim() || null,
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'mock-refund-request-260628-005',
    createdAt: refundedAt,
  })

  return {
    orderNo: order.orderNo,
    orderStatus: order.orderStatus,
    paymentStatus: order.paymentStatus,
    refundedAmount,
    refundedItemCount: order.items.length,
    refundedAt,
  }
}

export function partialRefundMockAdminOrder(
  orderNo: string,
  body: AdminPartialRefundRequest,
): AdminPartialRefund {
  const order = mockAdminOrderDetails.find((candidate) => candidate.orderNo === orderNo)
  const itemNos = normalizeRefundItemNos(body.itemNos)
  const uniqueItemNos = new Set(itemNos)

  if (itemNos.length === 0 || itemNos.length > 20 || itemNos.some((itemNo) => !itemNo)) {
    throwPartialRefundValidationError('退款票项不合法')
  }

  if (uniqueItemNos.size !== itemNos.length) {
    throwPartialRefundValidationError('退款票项不能重复')
  }

  if ((body.reason?.trim().length ?? 0) > 100) {
    throwPartialRefundValidationError('退款原因最多 100 字符')
  }

  if (!order) {
    throw new ApiError({
      success: false,
      code: 'ADMIN_ORDER_NOT_FOUND',
      message: '订单不存在',
      request_id: 'mock-admin-partial-refund',
    })
  }

  if (order.orderStatus === 'REFUNDED' || order.paymentStatus === 'REFUNDED') {
    throw new ApiError({
      success: false,
      code: 'ORDER_ALREADY_REFUNDED',
      message: '订单已退款',
      request_id: 'mock-admin-partial-refund',
    })
  }

  const isPartiallyRefundableState =
    order.orderStatus === 'PAID' &&
    (order.paymentStatus === 'PAID' || order.paymentStatus === 'PARTIAL_REFUND') &&
    order.items.every((item) => item.itemStatus === 'UNUSED' || item.itemStatus === 'REFUNDED')

  if (!isPartiallyRefundableState) {
    throw new ApiError({
      success: false,
      code: 'ORDER_NOT_PARTIALLY_REFUNDABLE',
      message: '当前订单不可部分退款',
      request_id: 'mock-admin-partial-refund',
    })
  }

  const selectedItems = itemNos.map((itemNo) => order.items.find((item) => item.itemNo === itemNo))

  if (selectedItems.some((item) => !item)) {
    throw new ApiError({
      success: false,
      code: 'ORDER_REFUND_ITEMS_INVALID',
      message: '退款票项不属于该订单',
      request_id: 'mock-admin-partial-refund',
    })
  }

  if (selectedItems.some((item) => item?.itemStatus !== 'UNUSED')) {
    throw new ApiError({
      success: false,
      code: 'ORDER_NOT_PARTIALLY_REFUNDABLE',
      message: '选中票项不可部分退款',
      request_id: 'mock-admin-partial-refund',
    })
  }

  const refundableItems = selectedItems.filter((item): item is AdminOrderDetail['items'][number] => Boolean(item))
  const refundedAmount = amountSum(refundableItems)
  const refundedAt = '2026-06-28T17:12:00+08:00'

  refundableItems.forEach((item) => {
    item.itemStatus = 'REFUNDED'
  })

  const remainingItems = order.items.filter((item) => item.itemStatus !== 'REFUNDED')

  order.payableAmount = amountSum(remainingItems)
  order.paymentStatus = remainingItems.length === 0 ? 'REFUNDED' : 'PARTIAL_REFUND'
  order.orderStatus = remainingItems.length === 0 ? 'REFUNDED' : 'PAID'

  appendMockRefundAuditLog(order.orderNo, {
    orderNo: order.orderNo,
    refundType: 'PARTIAL',
    refundedAmount,
    refundedItemCount: refundableItems.length,
    refundedItemNos: itemNos,
    reason: body.reason?.trim() || null,
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'mock-partial-refund-request-260628-006',
    createdAt: refundedAt,
  })

  return {
    orderNo: order.orderNo,
    orderStatus: order.orderStatus,
    paymentStatus: order.paymentStatus,
    refundedAmount,
    refundedItemCount: refundableItems.length,
    refundedItemNos: itemNos,
    refundedAt,
  }
}
