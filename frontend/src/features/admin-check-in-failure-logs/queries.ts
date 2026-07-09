import { useQuery } from '@tanstack/react-query'
import { adminCheckInFailureAuditLogsApi } from '../../shared/api/endpoints'
import type {
  AdminCheckInFailureAuditLogExportParams,
  AdminCheckInFailureAuditLogParams,
} from '../../shared/api/types'
import { listMockAdminCheckInFailureAuditLogSearch } from './mockData'

export type AdminCheckInFailureLogsMode = 'mock' | 'api'

export const adminCheckInFailureLogsMode: AdminCheckInFailureLogsMode =
  import.meta.env.VITE_ADMIN_CHECK_IN_FAILURE_LOGS_MODE === 'api' ? 'api' : 'mock'

export const adminCheckInFailureLogQueryKeys = {
  list: (
    params: AdminCheckInFailureAuditLogParams = {},
    mode: AdminCheckInFailureLogsMode = adminCheckInFailureLogsMode,
  ) => ['admin-check-in-failure-logs', mode, 'list', normalizeAdminCheckInFailureAuditLogParams(params)] as const,
}

function compactText(value?: string) {
  const trimmed = value?.trim()
  return trimmed || undefined
}

export function normalizeAdminCheckInFailureAuditLogParams(
  params: AdminCheckInFailureAuditLogParams = {},
): AdminCheckInFailureAuditLogParams {
  return {
    ...(compactText(params.ticketCode) ? { ticketCode: compactText(params.ticketCode) } : {}),
    ...(params.failureCode ? { failureCode: params.failureCode } : {}),
    ...(compactText(params.operatorUsername) ? { operatorUsername: compactText(params.operatorUsername) } : {}),
    ...(compactText(params.dateFrom) ? { dateFrom: compactText(params.dateFrom) } : {}),
    ...(compactText(params.dateTo) ? { dateTo: compactText(params.dateTo) } : {}),
    ...(params.page !== undefined ? { page: params.page } : {}),
    ...(params.pageSize !== undefined ? { pageSize: params.pageSize } : {}),
  }
}

export function normalizeAdminCheckInFailureAuditLogExportParams(
  params: AdminCheckInFailureAuditLogExportParams = {},
): AdminCheckInFailureAuditLogExportParams {
  return {
    ...(compactText(params.ticketCode) ? { ticketCode: compactText(params.ticketCode) } : {}),
    ...(params.failureCode ? { failureCode: params.failureCode } : {}),
    ...(compactText(params.operatorUsername) ? { operatorUsername: compactText(params.operatorUsername) } : {}),
    ...(compactText(params.dateFrom) ? { dateFrom: compactText(params.dateFrom) } : {}),
    ...(compactText(params.dateTo) ? { dateTo: compactText(params.dateTo) } : {}),
  }
}

export function useAdminCheckInFailureAuditLogSearchQuery(params: AdminCheckInFailureAuditLogParams = {}) {
  const normalizedParams = normalizeAdminCheckInFailureAuditLogParams(params)

  return useQuery({
    queryKey: adminCheckInFailureLogQueryKeys.list(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminCheckInFailureLogsMode === 'api') {
        return adminCheckInFailureAuditLogsApi.list(normalizedParams)
      }

      return listMockAdminCheckInFailureAuditLogSearch(normalizedParams)
    },
  })
}
