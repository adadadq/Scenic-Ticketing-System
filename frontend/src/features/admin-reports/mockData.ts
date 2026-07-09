import { ApiError } from '../../shared/api/errors'
import type {
  AdminDailyTrend,
  AdminHourlyTrend,
  AdminMonthlyTrend,
  AdminPaymentReconciliation,
  AdminProductBreakdown,
  AdminReportParams,
  AdminReportSummary,
  AdminTrendReportParams,
} from '../../shared/api/types'

const mockDailyTrend: AdminDailyTrend[] = [
  {
    reportDate: '2026-06-26',
    orderCount: 38,
    paidOrderCount: 31,
    completedOrderCount: 18,
    refundedOrderCount: 2,
    cancelledOrderCount: 5,
    netPaidAmount: '8420.00',
    ticketCount: 72,
    soldTicketCount: 61,
    checkedInTicketCount: 34,
    refundedTicketCount: 3,
  },
  {
    reportDate: '2026-06-27',
    orderCount: 44,
    paidOrderCount: 36,
    completedOrderCount: 21,
    refundedOrderCount: 3,
    cancelledOrderCount: 4,
    netPaidAmount: '9860.00',
    ticketCount: 85,
    soldTicketCount: 70,
    checkedInTicketCount: 41,
    refundedTicketCount: 5,
  },
  {
    reportDate: '2026-06-28',
    orderCount: 52,
    paidOrderCount: 43,
    completedOrderCount: 24,
    refundedOrderCount: 4,
    cancelledOrderCount: 5,
    netPaidAmount: '11940.00',
    ticketCount: 98,
    soldTicketCount: 84,
    checkedInTicketCount: 48,
    refundedTicketCount: 6,
  },
]

const mockHourlyTrend: AdminHourlyTrend[] = [
  {
    reportHour: '2026-06-26T09:00:00',
    orderCount: 18,
    paidOrderCount: 15,
    completedOrderCount: 8,
    refundedOrderCount: 1,
    cancelledOrderCount: 2,
    netPaidAmount: '3820.00',
    ticketCount: 34,
    soldTicketCount: 29,
    checkedInTicketCount: 16,
    refundedTicketCount: 1,
  },
  {
    reportHour: '2026-06-26T15:00:00',
    orderCount: 20,
    paidOrderCount: 16,
    completedOrderCount: 10,
    refundedOrderCount: 1,
    cancelledOrderCount: 3,
    netPaidAmount: '4600.00',
    ticketCount: 38,
    soldTicketCount: 32,
    checkedInTicketCount: 18,
    refundedTicketCount: 2,
  },
  {
    reportHour: '2026-06-27T10:00:00',
    orderCount: 21,
    paidOrderCount: 17,
    completedOrderCount: 10,
    refundedOrderCount: 1,
    cancelledOrderCount: 2,
    netPaidAmount: '4660.00',
    ticketCount: 41,
    soldTicketCount: 34,
    checkedInTicketCount: 20,
    refundedTicketCount: 2,
  },
  {
    reportHour: '2026-06-27T16:00:00',
    orderCount: 23,
    paidOrderCount: 19,
    completedOrderCount: 11,
    refundedOrderCount: 2,
    cancelledOrderCount: 2,
    netPaidAmount: '5200.00',
    ticketCount: 44,
    soldTicketCount: 36,
    checkedInTicketCount: 21,
    refundedTicketCount: 3,
  },
  {
    reportHour: '2026-06-28T09:00:00',
    orderCount: 25,
    paidOrderCount: 21,
    completedOrderCount: 11,
    refundedOrderCount: 2,
    cancelledOrderCount: 2,
    netPaidAmount: '5600.00',
    ticketCount: 47,
    soldTicketCount: 40,
    checkedInTicketCount: 23,
    refundedTicketCount: 3,
  },
  {
    reportHour: '2026-06-28T14:00:00',
    orderCount: 27,
    paidOrderCount: 22,
    completedOrderCount: 13,
    refundedOrderCount: 2,
    cancelledOrderCount: 3,
    netPaidAmount: '6340.00',
    ticketCount: 51,
    soldTicketCount: 44,
    checkedInTicketCount: 25,
    refundedTicketCount: 3,
  },
]

const mockProductBreakdown: AdminProductBreakdown[] = [
  {
    productId: 1,
    ticketTypeId: 10,
    productName: '遇龙河竹筏漂流',
    ticketName: '成人票',
    orderCount: 86,
    ticketCount: 151,
    soldTicketCount: 124,
    checkedInTicketCount: 76,
    refundedTicketCount: 8,
    netPaidAmount: '21120.00',
  },
  {
    productId: 2,
    ticketTypeId: 20,
    productName: '遇龙河亲子体验',
    ticketName: '儿童票',
    orderCount: 32,
    ticketCount: 62,
    soldTicketCount: 54,
    checkedInTicketCount: 29,
    refundedTicketCount: 4,
    netPaidAmount: '3672.00',
  },
  {
    productId: 3,
    ticketTypeId: 30,
    productName: '金龙桥日落漂流',
    ticketName: '双人套票',
    orderCount: 16,
    ticketCount: 42,
    soldTicketCount: 37,
    checkedInTicketCount: 18,
    refundedTicketCount: 2,
    netPaidAmount: '5428.00',
  },
]

function inRange(date: string, params: AdminReportParams = {}) {
  const dateFrom = params.dateFrom?.trim()
  const dateTo = params.dateTo?.trim()

  if (dateFrom && date < dateFrom) {
    return false
  }

  if (dateTo && date > dateTo) {
    return false
  }

  return true
}

function dayCountInclusive(dateFrom: string, dateTo: string) {
  const millisecondsPerDay = 24 * 60 * 60 * 1000
  return Math.floor((parseDate(dateTo).getTime() - parseDate(dateFrom).getTime()) / millisecondsPerDay) + 1
}

function monthCountInclusive(dateFrom: string, dateTo: string) {
  const [startYear, startMonth] = dateFrom.split('-').map(Number)
  const [endYear, endMonth] = dateTo.split('-').map(Number)
  return (endYear - startYear) * 12 + endMonth - startMonth + 1
}

function assertValidTrendParams(
  params: AdminTrendReportParams = {},
  maxEmptyBucketRange?: { count: (dateFrom: string, dateTo: string) => number; limit: number },
) {
  const dateFrom = params.dateFrom?.trim()
  const dateTo = params.dateTo?.trim()

  if (dateFrom && dateTo && dateFrom > dateTo) {
    throw new ApiError({
      success: false,
      code: 'ADMIN_REPORT_DATE_RANGE_INVALID',
      message: '报表日期范围无效',
      request_id: 'mock-admin-report-trend',
    })
  }

  if (params.includeEmpty && (!dateFrom || !dateTo)) {
    throw new ApiError({
      success: false,
      code: 'ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED',
      message: '补齐空趋势桶需要同时提供开始和结束日期',
      request_id: 'mock-admin-report-trend',
    })
  }

  if (
    params.includeEmpty &&
    dateFrom &&
    dateTo &&
    maxEmptyBucketRange &&
    maxEmptyBucketRange.count(dateFrom, dateTo) > maxEmptyBucketRange.limit
  ) {
    throw new ApiError({
      success: false,
      code: 'ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE',
      message: '趋势补零范围过大',
      request_id: 'mock-admin-report-trend',
    })
  }
}

function sumAmount(rows: Array<{ netPaidAmount: string }>) {
  return rows.reduce((total, row) => total + Number(row.netPaidAmount), 0).toFixed(2)
}

function sumNumber<T>(rows: T[], selector: (row: T) => number) {
  return rows.reduce((total, row) => total + selector(row), 0)
}

function amount(value: number) {
  return value.toFixed(2)
}

function zeroMetrics() {
  return {
    orderCount: 0,
    paidOrderCount: 0,
    completedOrderCount: 0,
    refundedOrderCount: 0,
    cancelledOrderCount: 0,
    netPaidAmount: '0.00',
    ticketCount: 0,
    soldTicketCount: 0,
    checkedInTicketCount: 0,
    refundedTicketCount: 0,
  }
}

function parseDate(date: string) {
  const [year, month, day] = date.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day))
}

function formatDate(date: Date) {
  return date.toISOString().slice(0, 10)
}

function listDates(dateFrom: string, dateTo: string) {
  const dates: string[] = []
  const current = parseDate(dateFrom)
  const end = parseDate(dateTo)

  while (current <= end) {
    dates.push(formatDate(current))
    current.setUTCDate(current.getUTCDate() + 1)
  }

  return dates
}

function listMonths(dateFrom: string, dateTo: string) {
  const months: string[] = []
  const [startYear, startMonth] = dateFrom.split('-').map(Number)
  const [endYear, endMonth] = dateTo.split('-').map(Number)
  let year = startYear
  let month = startMonth

  while (year < endYear || (year === endYear && month <= endMonth)) {
    months.push(`${year}-${String(month).padStart(2, '0')}`)
    month += 1

    if (month > 12) {
      month = 1
      year += 1
    }
  }

  return months
}

export function getMockAdminReportSummary(params: AdminReportParams = {}): AdminReportSummary {
  const rows = mockDailyTrend.filter((row) => inRange(row.reportDate, params))

  return {
    dateFrom: params.dateFrom?.trim() || mockDailyTrend[0].reportDate,
    dateTo: params.dateTo?.trim() || mockDailyTrend.at(-1)?.reportDate || mockDailyTrend[0].reportDate,
    orderCount: sumNumber(rows, (row) => row.orderCount),
    paidOrderCount: sumNumber(rows, (row) => row.paidOrderCount),
    completedOrderCount: sumNumber(rows, (row) => row.completedOrderCount),
    refundedOrderCount: sumNumber(rows, (row) => row.refundedOrderCount),
    cancelledOrderCount: sumNumber(rows, (row) => row.cancelledOrderCount),
    netPaidAmount: sumAmount(rows),
    ticketCount: sumNumber(rows, (row) => row.ticketCount),
    soldTicketCount: sumNumber(rows, (row) => row.soldTicketCount),
    checkedInTicketCount: sumNumber(rows, (row) => row.checkedInTicketCount),
    refundedTicketCount: sumNumber(rows, (row) => row.refundedTicketCount),
  }
}

export function getMockAdminPaymentReconciliation(params: AdminReportParams = {}): AdminPaymentReconciliation {
  const rows = mockDailyTrend.filter((row) => inRange(row.reportDate, params))
  const orderNetPaidAmount = Number(sumAmount(rows))
  const refundAuditAmount = sumNumber(rows, (row) => row.refundedTicketCount) * 88
  const unreconciledAmount = rows.some((row) => row.reportDate === '2026-06-28') ? 16 : 0
  const expectedNetAmount = orderNetPaidAmount - unreconciledAmount
  const capturedPaymentAmount = expectedNetAmount + refundAuditAmount

  return {
    dateFrom: params.dateFrom?.trim() || mockDailyTrend[0].reportDate,
    dateTo: params.dateTo?.trim() || mockDailyTrend.at(-1)?.reportDate || mockDailyTrend[0].reportDate,
    orderNetPaidAmount: amount(orderNetPaidAmount),
    capturedPaymentAmount: amount(capturedPaymentAmount),
    refundAuditAmount: amount(refundAuditAmount),
    expectedNetAmount: amount(expectedNetAmount),
    unreconciledAmount: amount(unreconciledAmount),
    capturedPaymentCount: sumNumber(rows, (row) => row.paidOrderCount),
    refundAuditLogCount: sumNumber(rows, (row) => row.refundedOrderCount),
    reconciled: unreconciledAmount === 0,
  }
}

export function listMockAdminProductBreakdown(params: AdminReportParams = {}) {
  const hasRowsInRange = mockDailyTrend.some((row) => inRange(row.reportDate, params))
  return hasRowsInRange ? mockProductBreakdown : []
}

export function listMockAdminDailyTrend(params: AdminTrendReportParams = {}) {
  assertValidTrendParams(params, { count: dayCountInclusive, limit: 366 })
  const rows = mockDailyTrend.filter((row) => inRange(row.reportDate, params))

  if (!params.includeEmpty) {
    return rows
  }

  const rowsByDate = new Map(rows.map((row) => [row.reportDate, row]))

  return listDates(params.dateFrom?.trim() ?? '', params.dateTo?.trim() ?? '').map((reportDate): AdminDailyTrend => {
    return rowsByDate.get(reportDate) ?? {
      reportDate,
      ...zeroMetrics(),
    }
  })
}

export function listMockAdminHourlyTrend(params: AdminTrendReportParams = {}) {
  assertValidTrendParams(params, { count: dayCountInclusive, limit: 31 })
  const rows = mockHourlyTrend.filter((row) => inRange(row.reportHour.slice(0, 10), params))

  if (!params.includeEmpty) {
    return rows
  }

  const rowsByHour = new Map(rows.map((row) => [row.reportHour, row]))

  return listDates(params.dateFrom?.trim() ?? '', params.dateTo?.trim() ?? '').flatMap((date) => {
    return Array.from({ length: 24 }, (_, hour): AdminHourlyTrend => {
      const reportHour = `${date}T${String(hour).padStart(2, '0')}:00:00`

      return rowsByHour.get(reportHour) ?? {
        reportHour,
        ...zeroMetrics(),
      }
    })
  })
}

export function listMockAdminMonthlyTrend(params: AdminTrendReportParams = {}) {
  assertValidTrendParams(params, { count: monthCountInclusive, limit: 60 })
  const rowsByMonth = new Map<string, AdminDailyTrend[]>()
  const dailyRows = listMockAdminDailyTrend({
    ...(params.dateFrom?.trim() ? { dateFrom: params.dateFrom.trim() } : {}),
    ...(params.dateTo?.trim() ? { dateTo: params.dateTo.trim() } : {}),
  })

  for (const row of dailyRows) {
    const reportMonth = row.reportDate.slice(0, 7)
    rowsByMonth.set(reportMonth, [...(rowsByMonth.get(reportMonth) ?? []), row])
  }

  const rows = [...rowsByMonth.entries()].map(([reportMonth, rows]): AdminMonthlyTrend => {
    return {
      reportMonth,
      orderCount: sumNumber(rows, (row) => row.orderCount),
      paidOrderCount: sumNumber(rows, (row) => row.paidOrderCount),
      completedOrderCount: sumNumber(rows, (row) => row.completedOrderCount),
      refundedOrderCount: sumNumber(rows, (row) => row.refundedOrderCount),
      cancelledOrderCount: sumNumber(rows, (row) => row.cancelledOrderCount),
      netPaidAmount: sumAmount(rows),
      ticketCount: sumNumber(rows, (row) => row.ticketCount),
      soldTicketCount: sumNumber(rows, (row) => row.soldTicketCount),
      checkedInTicketCount: sumNumber(rows, (row) => row.checkedInTicketCount),
      refundedTicketCount: sumNumber(rows, (row) => row.refundedTicketCount),
    }
  })

  if (!params.includeEmpty) {
    return rows
  }

  const rowsByMonthValue = new Map(rows.map((row) => [row.reportMonth, row]))

  return listMonths(params.dateFrom?.trim() ?? '', params.dateTo?.trim() ?? '').map((reportMonth): AdminMonthlyTrend => {
    return rowsByMonthValue.get(reportMonth) ?? {
      reportMonth,
      ...zeroMetrics(),
    }
  })
}
