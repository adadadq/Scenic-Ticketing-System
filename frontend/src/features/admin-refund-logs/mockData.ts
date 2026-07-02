import { ApiError } from '../../shared/api/errors'
import type {
  AdminRefundAuditLog,
  AdminRefundAuditLogExportParams,
  AdminRefundAuditLogList,
  AdminRefundAuditLogParams,
} from '../../shared/api/types'

const mockRefundAuditLogs: AdminRefundAuditLog[] = [
  {
    orderNo: 'YT2606280004',
    refundType: 'FULL',
    refundedAmount: '256.00',
    refundedItemCount: 2,
    refundedItemNos: ['ITEM-260628-004-A', 'ITEM-260628-004-B'],
    reason: '暴雨停航',
    operatorUsername: 'ops_lina',
    operatorDisplayName: '运营李娜',
    requestId: 'mock-refund-request-260628-004',
    createdAt: '2026-06-28T16:20:00+08:00',
  },
  {
    orderNo: 'YT2606280003',
    refundType: 'PARTIAL',
    refundedAmount: '68.00',
    refundedItemCount: 1,
    refundedItemNos: ['ITEM-260628-003-A'],
    reason: '儿童票临时取消',
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'mock-refund-request-260628-003',
    createdAt: '2026-06-28T15:47:00+08:00',
  },
]

export function addMockAdminRefundAuditLog(log: AdminRefundAuditLog) {
  mockRefundAuditLogs.unshift(log)
}

function textIncludes(value: string, query?: string) {
  const trimmed = query?.trim()
  return trimmed ? value.toLowerCase().includes(trimmed.toLowerCase()) : true
}

function datePart(value: string) {
  return value.slice(0, 10)
}

function inDateRange(log: AdminRefundAuditLog, params: AdminRefundAuditLogExportParams = {}) {
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

function assertValidRefundAuditExportFilters(params: AdminRefundAuditLogExportParams = {}) {
  const dateFrom = params.dateFrom?.trim()
  const dateTo = params.dateTo?.trim()

  if (dateFrom && dateTo && dateFrom > dateTo) {
    throw new ApiError({
      success: false,
      code: 'ADMIN_REFUND_LOG_DATE_RANGE_INVALID',
      message: '退款审计日志日期范围无效',
      request_id: 'mock-admin-refund-log-search',
    })
  }
}

export function listMockAdminRefundAuditLogExportRows(params: AdminRefundAuditLogExportParams = {}) {
  assertValidRefundAuditExportFilters(params)

  return mockRefundAuditLogs
    .filter((log) => !params.refundType || log.refundType === params.refundType)
    .filter((log) => textIncludes(log.orderNo, params.orderNo))
    .filter((log) => textIncludes(log.operatorUsername, params.operatorUsername))
    .filter((log) => inDateRange(log, params))
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt))
}

export function listMockAdminRefundAuditLogSearch(params: AdminRefundAuditLogParams = {}): AdminRefundAuditLogList {
  assertValidRefundAuditExportFilters(params)

  const page = Math.max(1, params.page ?? 1)
  const pageSize = Math.min(100, Math.max(1, params.pageSize ?? 20))
  const filtered = listMockAdminRefundAuditLogExportRows(params)
  const start = (page - 1) * pageSize

  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  }
}
