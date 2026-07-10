import { useQuery } from '@tanstack/react-query'
import { adminReportsApi } from '../../shared/api/endpoints'
import type { AdminReportParams, AdminTrendReportParams } from '../../shared/api/types'
import {
  getMockAdminPaymentReconciliation,
  getMockAdminReportSummary,
  listMockAdminDailyTrend,
  listMockAdminHourlyTrend,
  listMockAdminMonthlyTrend,
  listMockAdminProductBreakdown,
} from './mockData'

export type AdminReportsMode = 'mock' | 'api'

export const adminReportsMode: AdminReportsMode = import.meta.env.VITE_ADMIN_REPORTS_MODE === 'mock' ? 'mock' : 'api'

export const adminReportQueryKeys = {
  dailyTrend: (params: AdminTrendReportParams = {}, mode: AdminReportsMode = adminReportsMode) =>
    ['admin-reports', mode, 'daily-trend', normalizeAdminTrendReportParams(params)] as const,
  hourlyTrend: (params: AdminTrendReportParams = {}, mode: AdminReportsMode = adminReportsMode) =>
    ['admin-reports', mode, 'hourly-trend', normalizeAdminTrendReportParams(params)] as const,
  monthlyTrend: (params: AdminTrendReportParams = {}, mode: AdminReportsMode = adminReportsMode) =>
    ['admin-reports', mode, 'monthly-trend', normalizeAdminTrendReportParams(params)] as const,
  paymentReconciliation: (params: AdminReportParams = {}, mode: AdminReportsMode = adminReportsMode) =>
    ['admin-reports', mode, 'payment-reconciliation', normalizeAdminReportParams(params)] as const,
  productBreakdown: (params: AdminReportParams = {}, mode: AdminReportsMode = adminReportsMode) =>
    ['admin-reports', mode, 'product-breakdown', normalizeAdminReportParams(params)] as const,
  summary: (params: AdminReportParams = {}, mode: AdminReportsMode = adminReportsMode) =>
    ['admin-reports', mode, 'summary', normalizeAdminReportParams(params)] as const,
}

export function normalizeAdminReportParams(params: AdminReportParams = {}): AdminReportParams {
  const dateFrom = params.dateFrom?.trim()
  const dateTo = params.dateTo?.trim()

  return {
    ...(dateFrom ? { dateFrom } : {}),
    ...(dateTo ? { dateTo } : {}),
  }
}

export function normalizeAdminTrendReportParams(params: AdminTrendReportParams = {}): AdminTrendReportParams {
  return {
    ...normalizeAdminReportParams(params),
    ...(params.includeEmpty ? { includeEmpty: true } : {}),
  }
}

export function useAdminReportSummaryQuery(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)

  return useQuery({
    queryKey: adminReportQueryKeys.summary(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminReportsMode === 'api') {
        return adminReportsApi.summary(normalizedParams)
      }

      return getMockAdminReportSummary(normalizedParams)
    },
  })
}

export function useAdminProductBreakdownQuery(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)

  return useQuery({
    queryKey: adminReportQueryKeys.productBreakdown(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminReportsMode === 'api') {
        return adminReportsApi.productBreakdown(normalizedParams)
      }

      return listMockAdminProductBreakdown(normalizedParams)
    },
  })
}

export function useAdminPaymentReconciliationQuery(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)

  return useQuery({
    queryKey: adminReportQueryKeys.paymentReconciliation(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminReportsMode === 'api') {
        return adminReportsApi.paymentReconciliation(normalizedParams)
      }

      return getMockAdminPaymentReconciliation(normalizedParams)
    },
  })
}

export function useAdminDailyTrendQuery(params: AdminTrendReportParams = {}) {
  const normalizedParams = normalizeAdminTrendReportParams(params)

  return useQuery({
    queryKey: adminReportQueryKeys.dailyTrend(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminReportsMode === 'api') {
        return adminReportsApi.dailyTrend(normalizedParams)
      }

      return listMockAdminDailyTrend(normalizedParams)
    },
  })
}

export function useAdminHourlyTrendQuery(params: AdminTrendReportParams = {}) {
  const normalizedParams = normalizeAdminTrendReportParams(params)

  return useQuery({
    queryKey: adminReportQueryKeys.hourlyTrend(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminReportsMode === 'api') {
        return adminReportsApi.hourlyTrend(normalizedParams)
      }

      return listMockAdminHourlyTrend(normalizedParams)
    },
  })
}

export function useAdminMonthlyTrendQuery(params: AdminTrendReportParams = {}) {
  const normalizedParams = normalizeAdminTrendReportParams(params)

  return useQuery({
    queryKey: adminReportQueryKeys.monthlyTrend(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminReportsMode === 'api') {
        return adminReportsApi.monthlyTrend(normalizedParams)
      }

      return listMockAdminMonthlyTrend(normalizedParams)
    },
  })
}
