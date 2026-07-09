import { ApiError } from '../../shared/api/errors'
import type {
  AdminCheckInFailureAuditLog,
  AdminCheckInFailureAuditLogList,
  AdminCheckInFailureAuditLogParams,
  AdminCheckInFailureCode,
} from '../../shared/api/types'

const allowedFailureCodes: AdminCheckInFailureCode[] = [
  'TICKET_NOT_FOUND',
  'TICKET_ALREADY_USED',
  'TICKET_NOT_CHECKABLE',
  'TICKET_NOT_CHECKED_IN',
  'TICKET_UNDO_NOT_ALLOWED',
]

const mockAdminCheckInFailureAuditLogs: AdminCheckInFailureAuditLog[] = [
  {
    ticketCode: 'TK-MISSING-260701',
    action: 'CHECK_IN',
    failureCode: 'TICKET_NOT_FOUND',
    failureMessage: '票码不存在',
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'mock-check-in-failure-260701-001',
    createdAt: '2026-07-01T10:12:00+08:00',
  },
  {
    ticketCode: 'TK2606280001A',
    action: 'CHECK_IN',
    failureCode: 'TICKET_ALREADY_USED',
    failureMessage: '票码已核销',
    operatorUsername: 'shift-a',
    operatorDisplayName: '早班核验员',
    requestId: 'mock-check-in-failure-260701-002',
    createdAt: '2026-07-01T10:08:00+08:00',
  },
  {
    ticketCode: 'TK2606290007C',
    action: 'CHECK_IN',
    failureCode: 'TICKET_NOT_CHECKABLE',
    failureMessage: '当前票码状态不可核验',
    operatorUsername: 'ops_lina',
    operatorDisplayName: '运营李娜',
    requestId: 'mock-check-in-failure-260630-003',
    createdAt: '2026-06-30T17:35:00+08:00',
  },
  {
    ticketCode: 'TK2606280009U',
    action: 'UNDO_CHECK_IN',
    failureCode: 'TICKET_NOT_CHECKED_IN',
    failureMessage: '票码未核销',
    operatorUsername: 'shift-b',
    operatorDisplayName: '晚班核验员',
    requestId: 'mock-check-in-failure-260701-004',
    createdAt: '2026-07-01T10:04:00+08:00',
  },
  {
    ticketCode: 'TK2606280010U',
    action: 'UNDO_CHECK_IN',
    failureCode: 'TICKET_UNDO_NOT_ALLOWED',
    failureMessage: '当前票码不可撤销核销',
    operatorUsername: 'ops_lina',
    operatorDisplayName: '运营李娜',
    requestId: 'mock-check-in-failure-260630-005',
    createdAt: '2026-06-30T17:28:00+08:00',
  },
]

function textIncludes(value: string, query?: string) {
  const trimmed = query?.trim()
  return trimmed ? value.toLowerCase().includes(trimmed.toLowerCase()) : true
}

function datePart(value: string) {
  return value.slice(0, 10)
}

function assertValidFilters(params: AdminCheckInFailureAuditLogParams = {}) {
  const dateFrom = params.dateFrom?.trim()
  const dateTo = params.dateTo?.trim()

  if (params.failureCode && !allowedFailureCodes.includes(params.failureCode)) {
    throw new ApiError({
      success: false,
      code: 'ADMIN_CHECK_IN_FAILURE_CODE_INVALID',
      message: '核验失败码无效',
      request_id: 'mock-check-in-failure-log-search',
    })
  }

  if (dateFrom && dateTo && dateFrom > dateTo) {
    throw new ApiError({
      success: false,
      code: 'ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID',
      message: '核验失败审计日期范围无效',
      request_id: 'mock-check-in-failure-log-search',
    })
  }
}

function inDateRange(log: AdminCheckInFailureAuditLog, params: AdminCheckInFailureAuditLogParams = {}) {
  const current = datePart(log.createdAt)
  const dateFrom = params.dateFrom?.trim()
  const dateTo = params.dateTo?.trim()

  if (dateFrom && current < dateFrom) {
    return false
  }

  if (dateTo && current > dateTo) {
    return false
  }

  return true
}

export function listMockAdminCheckInFailureAuditLogRows(params: AdminCheckInFailureAuditLogParams = {}) {
  assertValidFilters(params)

  return mockAdminCheckInFailureAuditLogs
    .filter((log) => textIncludes(log.ticketCode, params.ticketCode))
    .filter((log) => !params.failureCode || log.failureCode === params.failureCode)
    .filter((log) => textIncludes(log.operatorUsername, params.operatorUsername))
    .filter((log) => inDateRange(log, params))
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
}

export function listMockAdminCheckInFailureAuditLogSearch(
  params: AdminCheckInFailureAuditLogParams = {},
): AdminCheckInFailureAuditLogList {
  const page = Math.max(1, params.page ?? 1)
  const pageSize = Math.min(100, Math.max(1, params.pageSize ?? 20))
  const filtered = listMockAdminCheckInFailureAuditLogRows(params)
  const start = (page - 1) * pageSize

  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  }
}
