import type {
  AdminCheckInAuditLogExportParams,
  AdminCheckInFailureAuditLogExportParams,
  AdminCheckInFailureAuditLogParams,
  AdminExportJobListParams,
  AdminOrderListParams,
  AdminRefundAuditLogExportParams,
  AdminRefundAuditLogParams,
  AdminReportParams,
  AdminTrendReportParams,
} from './types'

export function compactText(value?: string) {
  const trimmed = value?.trim()
  return trimmed || undefined
}

function buildSearch(search: URLSearchParams) {
  const query = search.toString()
  return query ? `?${query}` : ''
}

export function buildAdminOrderListSearch(params: AdminOrderListParams = {}) {
  const search = new URLSearchParams()
  const orderNo = compactText(params.orderNo)
  const buyerPhone = compactText(params.buyerPhone)

  if (params.status) {
    search.set('status', params.status)
  }

  if (params.paymentStatus) {
    search.set('paymentStatus', params.paymentStatus)
  }

  if (orderNo) {
    search.set('orderNo', orderNo)
  }

  if (buyerPhone) {
    search.set('buyerPhone', buyerPhone)
  }

  if (params.page !== undefined) {
    search.set('page', String(params.page))
  }

  if (params.pageSize !== undefined) {
    search.set('pageSize', String(params.pageSize))
  }

  return buildSearch(search)
}

export function buildAdminReportSearch(params: AdminReportParams = {}) {
  const search = new URLSearchParams()
  const dateFrom = compactText(params.dateFrom)
  const dateTo = compactText(params.dateTo)

  if (dateFrom) {
    search.set('dateFrom', dateFrom)
  }

  if (dateTo) {
    search.set('dateTo', dateTo)
  }

  return buildSearch(search)
}

export function buildAdminTrendReportSearch(params: AdminTrendReportParams = {}) {
  const search = new URLSearchParams()
  const dateFrom = compactText(params.dateFrom)
  const dateTo = compactText(params.dateTo)

  if (dateFrom) {
    search.set('dateFrom', dateFrom)
  }

  if (dateTo) {
    search.set('dateTo', dateTo)
  }

  if (params.includeEmpty) {
    search.set('includeEmpty', 'true')
  }

  return buildSearch(search)
}

export function buildAdminRefundAuditLogSearch(params: AdminRefundAuditLogParams = {}) {
  const search = new URLSearchParams()
  const orderNo = compactText(params.orderNo)
  const operatorUsername = compactText(params.operatorUsername)
  const dateFrom = compactText(params.dateFrom)
  const dateTo = compactText(params.dateTo)

  if (params.refundType) {
    search.set('refundType', params.refundType)
  }

  if (orderNo) {
    search.set('orderNo', orderNo)
  }

  if (operatorUsername) {
    search.set('operatorUsername', operatorUsername)
  }

  if (dateFrom) {
    search.set('dateFrom', dateFrom)
  }

  if (dateTo) {
    search.set('dateTo', dateTo)
  }

  if (params.page !== undefined) {
    search.set('page', String(params.page))
  }

  if (params.pageSize !== undefined) {
    search.set('pageSize', String(params.pageSize))
  }

  return buildSearch(search)
}

export function buildAdminRefundAuditLogExportSearch(params: AdminRefundAuditLogExportParams = {}) {
  const search = new URLSearchParams()
  const orderNo = compactText(params.orderNo)
  const operatorUsername = compactText(params.operatorUsername)
  const dateFrom = compactText(params.dateFrom)
  const dateTo = compactText(params.dateTo)

  if (params.refundType) {
    search.set('refundType', params.refundType)
  }

  if (orderNo) {
    search.set('orderNo', orderNo)
  }

  if (operatorUsername) {
    search.set('operatorUsername', operatorUsername)
  }

  if (dateFrom) {
    search.set('dateFrom', dateFrom)
  }

  if (dateTo) {
    search.set('dateTo', dateTo)
  }

  return buildSearch(search)
}

export function buildAdminCheckInAuditLogExportSearch(params: AdminCheckInAuditLogExportParams = {}) {
  const search = new URLSearchParams()
  const ticketCode = compactText(params.ticketCode)
  const orderNo = compactText(params.orderNo)
  const operatorUsername = compactText(params.operatorUsername)
  const reason = compactText(params.reason)
  const dateFrom = compactText(params.dateFrom)
  const dateTo = compactText(params.dateTo)

  if (ticketCode) {
    search.set('ticketCode', ticketCode)
  }

  if (orderNo) {
    search.set('orderNo', orderNo)
  }

  if (operatorUsername) {
    search.set('operatorUsername', operatorUsername)
  }

  if (reason) {
    search.set('reason', reason)
  }

  if (dateFrom) {
    search.set('dateFrom', dateFrom)
  }

  if (dateTo) {
    search.set('dateTo', dateTo)
  }

  return buildSearch(search)
}

export function buildAdminCheckInFailureAuditLogSearch(params: AdminCheckInFailureAuditLogParams = {}) {
  const search = new URLSearchParams()
  const ticketCode = compactText(params.ticketCode)
  const operatorUsername = compactText(params.operatorUsername)
  const dateFrom = compactText(params.dateFrom)
  const dateTo = compactText(params.dateTo)

  if (ticketCode) {
    search.set('ticketCode', ticketCode)
  }

  if (params.failureCode) {
    search.set('failureCode', params.failureCode)
  }

  if (operatorUsername) {
    search.set('operatorUsername', operatorUsername)
  }

  if (dateFrom) {
    search.set('dateFrom', dateFrom)
  }

  if (dateTo) {
    search.set('dateTo', dateTo)
  }

  if (params.page !== undefined) {
    search.set('page', String(params.page))
  }

  if (params.pageSize !== undefined) {
    search.set('pageSize', String(params.pageSize))
  }

  return buildSearch(search)
}

export function buildAdminExportJobListSearch(params: AdminExportJobListParams = {}) {
  const search = new URLSearchParams()

  if (params.exportType) {
    search.set('exportType', params.exportType)
  }

  if (params.fileFormat) {
    search.set('fileFormat', params.fileFormat)
  }

  if (params.status) {
    search.set('status', params.status)
  }

  if (params.page !== undefined) {
    search.set('page', String(params.page))
  }

  if (params.pageSize !== undefined) {
    search.set('pageSize', String(params.pageSize))
  }

  return buildSearch(search)
}

export function buildAdminCheckInFailureAuditLogExportSearch(params: AdminCheckInFailureAuditLogExportParams = {}) {
  const search = new URLSearchParams()
  const ticketCode = compactText(params.ticketCode)
  const operatorUsername = compactText(params.operatorUsername)
  const dateFrom = compactText(params.dateFrom)
  const dateTo = compactText(params.dateTo)

  if (ticketCode) {
    search.set('ticketCode', ticketCode)
  }

  if (params.failureCode) {
    search.set('failureCode', params.failureCode)
  }

  if (operatorUsername) {
    search.set('operatorUsername', operatorUsername)
  }

  if (dateFrom) {
    search.set('dateFrom', dateFrom)
  }

  if (dateTo) {
    search.set('dateTo', dateTo)
  }

  return buildSearch(search)
}
