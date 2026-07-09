import { useQuery } from '@tanstack/react-query'
import { adminRefundAuditLogsApi } from '../../shared/api/endpoints'
import type { AdminRefundAuditLogParams } from '../../shared/api/types'
import { listMockAdminRefundAuditLogSearch } from './mockData'

export type AdminRefundLogsMode = 'mock' | 'api'

export const adminRefundLogsMode: AdminRefundLogsMode =
  import.meta.env.VITE_ADMIN_REFUND_LOGS_MODE === 'api' ? 'api' : 'mock'

export const adminRefundLogQueryKeys = {
  list: (params: AdminRefundAuditLogParams = {}, mode: AdminRefundLogsMode = adminRefundLogsMode) =>
    ['admin-refund-logs', mode, 'list', normalizeAdminRefundAuditLogParams(params)] as const,
}

export function normalizeAdminRefundAuditLogParams(
  params: AdminRefundAuditLogParams = {},
): AdminRefundAuditLogParams {
  const orderNo = params.orderNo?.trim()
  const operatorUsername = params.operatorUsername?.trim()
  const dateFrom = params.dateFrom?.trim()
  const dateTo = params.dateTo?.trim()

  return {
    ...(params.refundType ? { refundType: params.refundType } : {}),
    ...(orderNo ? { orderNo } : {}),
    ...(operatorUsername ? { operatorUsername } : {}),
    ...(dateFrom ? { dateFrom } : {}),
    ...(dateTo ? { dateTo } : {}),
    ...(params.page !== undefined ? { page: params.page } : {}),
    ...(params.pageSize !== undefined ? { pageSize: params.pageSize } : {}),
  }
}

export function useAdminRefundAuditLogSearchQuery(params: AdminRefundAuditLogParams = {}) {
  const normalizedParams = normalizeAdminRefundAuditLogParams(params)

  return useQuery({
    queryKey: adminRefundLogQueryKeys.list(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminRefundLogsMode === 'api') {
        return adminRefundAuditLogsApi.list(normalizedParams)
      }

      return listMockAdminRefundAuditLogSearch(normalizedParams)
    },
  })
}
