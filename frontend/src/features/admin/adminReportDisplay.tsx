import type { AdminDailyTrend, AdminHourlyTrend, AdminMonthlyTrend, AdminReportParams } from '../../shared/api/types'

export const defaultReportParams: AdminReportParams = {
  dateFrom: '2026-06-26',
  dateTo: '2026-06-28',
}

export function amountLabel(amount: string) {
  return `¥ ${amount}`
}

export function metricLabel(value?: number) {
  return value?.toLocaleString('zh-CN') ?? '0'
}

export type AdminTrendMetricRow = AdminDailyTrend | AdminHourlyTrend | AdminMonthlyTrend

export function maxTrendAmount(trendRows: AdminTrendMetricRow[]) {
  return Math.max(...trendRows.map((row) => Number(row.netPaidAmount)), 1)
}

export function trendPeriodLabel(row: AdminTrendMetricRow) {
  if ('reportHour' in row) {
    return row.reportHour.replace('T', ' ').slice(0, 16)
  }

  return 'reportMonth' in row ? row.reportMonth : row.reportDate
}
