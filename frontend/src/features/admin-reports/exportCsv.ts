import { adminReportExportsApi, adminReportsApi } from '../../shared/api/endpoints'
import type { AdminDailyTrend, AdminHourlyTrend, AdminMonthlyTrend, AdminPaymentReconciliation, AdminProductBreakdown, AdminReportParams, AdminTrendReportParams } from '../../shared/api/types'
import { scenicProductName, scenicTicketName } from '../../shared/display/scenicText'
import { listMockAdminOrders } from '../admin-orders/mockData'
import { adminReportsMode, normalizeAdminReportParams, normalizeAdminTrendReportParams } from './queries'
import {
  getMockAdminPaymentReconciliation,
  listMockAdminProductBreakdown,
  listMockAdminDailyTrend,
  listMockAdminHourlyTrend,
  listMockAdminMonthlyTrend,
} from './mockData'
import { buildWorkbookBlob, neutralizeSpreadsheetFormulaText } from './xlsxWorkbook'

export { neutralizeSpreadsheetFormulaText } from './xlsxWorkbook'

type AdminOrderCsvRow = {
  orderNo: string
  buyerName: string
  buyerPhoneMasked: string
  orderStatus: string
  paymentStatus: string
  totalAmount: string
  payableAmount: string
  orderTime: string
  itemCount: number
}

export type AdminTrendCsvKind = 'daily' | 'hourly' | 'monthly'

type AdminTrendCsvRow = {
  period: string
  orderCount: number
  paidOrderCount: number
  completedOrderCount: number
  refundedOrderCount: number
  cancelledOrderCount: number
  netPaidAmount: string
  ticketCount: number
  soldTicketCount: number
  checkedInTicketCount: number
  refundedTicketCount: number
}

const adminPaymentReconciliationCsvHeaders: Array<keyof AdminPaymentReconciliation> = [
  'dateFrom',
  'dateTo',
  'orderNetPaidAmount',
  'capturedPaymentAmount',
  'refundAuditAmount',
  'expectedNetAmount',
  'unreconciledAmount',
  'capturedPaymentCount',
  'refundAuditLogCount',
  'reconciled',
]

const adminProductBreakdownCsvHeaders: Array<keyof AdminProductBreakdown> = [
  'productId',
  'ticketTypeId',
  'productName',
  'ticketName',
  'orderCount',
  'ticketCount',
  'soldTicketCount',
  'checkedInTicketCount',
  'refundedTicketCount',
  'netPaidAmount',
]

const adminOrderCsvHeaders: Array<keyof AdminOrderCsvRow> = [
  'orderNo',
  'buyerName',
  'buyerPhoneMasked',
  'orderStatus',
  'paymentStatus',
  'totalAmount',
  'payableAmount',
  'orderTime',
  'itemCount',
]
const adminTrendMetricCsvHeaders: Array<Exclude<keyof AdminTrendCsvRow, 'period'>> = [
  'orderCount',
  'paidOrderCount',
  'completedOrderCount',
  'refundedOrderCount',
  'cancelledOrderCount',
  'netPaidAmount',
  'ticketCount',
  'soldTicketCount',
  'checkedInTicketCount',
  'refundedTicketCount',
]

function isInReportRange(orderTime: string, params: AdminReportParams = {}) {
  const reportDate = orderTime.slice(0, 10)
  const dateFrom = params.dateFrom?.trim()
  const dateTo = params.dateTo?.trim()

  if (dateFrom && reportDate < dateFrom) {
    return false
  }

  if (dateTo && reportDate > dateTo) {
    return false
  }

  return true
}

export function escapeCsvCell(value: string | number | boolean) {
  const safeText = neutralizeSpreadsheetFormulaText(value)
  const escapedText = safeText.replaceAll('"', '""')

  return /[",\t\r\n]/.test(safeText) ? `"${escapedText}"` : escapedText
}

export function listMockAdminOrderCsvRows(params: AdminReportParams = {}): AdminOrderCsvRow[] {
  return listMockAdminOrders({ page: 1, pageSize: 100 }).items
    .filter((order) => isInReportRange(order.orderTime, params))
    .map((order) => ({
      orderNo: order.orderNo,
      buyerName: order.buyerName,
      buyerPhoneMasked: order.buyerPhoneMasked,
      orderStatus: order.orderStatus,
      paymentStatus: order.paymentStatus,
      totalAmount: order.totalAmount,
      payableAmount: order.payableAmount,
      orderTime: order.orderTime,
      itemCount: order.itemCount,
    }))
}

export function buildAdminOrdersCsvText(rows: AdminOrderCsvRow[]) {
  const body = rows.map((row) => adminOrderCsvHeaders.map((header) => escapeCsvCell(row[header])).join(','))
  return `\ufeff${[adminOrderCsvHeaders.join(','), ...body].join('\r\n')}`
}

function mapDailyTrendRow(row: AdminDailyTrend): AdminTrendCsvRow {
  return {
    period: row.reportDate,
    orderCount: row.orderCount,
    paidOrderCount: row.paidOrderCount,
    completedOrderCount: row.completedOrderCount,
    refundedOrderCount: row.refundedOrderCount,
    cancelledOrderCount: row.cancelledOrderCount,
    netPaidAmount: row.netPaidAmount,
    ticketCount: row.ticketCount,
    soldTicketCount: row.soldTicketCount,
    checkedInTicketCount: row.checkedInTicketCount,
    refundedTicketCount: row.refundedTicketCount,
  }
}

function mapHourlyTrendRow(row: AdminHourlyTrend): AdminTrendCsvRow {
  return {
    period: row.reportHour,
    orderCount: row.orderCount,
    paidOrderCount: row.paidOrderCount,
    completedOrderCount: row.completedOrderCount,
    refundedOrderCount: row.refundedOrderCount,
    cancelledOrderCount: row.cancelledOrderCount,
    netPaidAmount: row.netPaidAmount,
    ticketCount: row.ticketCount,
    soldTicketCount: row.soldTicketCount,
    checkedInTicketCount: row.checkedInTicketCount,
    refundedTicketCount: row.refundedTicketCount,
  }
}

function mapMonthlyTrendRow(row: AdminMonthlyTrend): AdminTrendCsvRow {
  return {
    period: row.reportMonth,
    orderCount: row.orderCount,
    paidOrderCount: row.paidOrderCount,
    completedOrderCount: row.completedOrderCount,
    refundedOrderCount: row.refundedOrderCount,
    cancelledOrderCount: row.cancelledOrderCount,
    netPaidAmount: row.netPaidAmount,
    ticketCount: row.ticketCount,
    soldTicketCount: row.soldTicketCount,
    checkedInTicketCount: row.checkedInTicketCount,
    refundedTicketCount: row.refundedTicketCount,
  }
}

export function listMockAdminTrendCsvRows(kind: AdminTrendCsvKind, params: AdminTrendReportParams = {}): AdminTrendCsvRow[] {
  switch (kind) {
    case 'daily':
      return listMockAdminDailyTrend(params).map(mapDailyTrendRow)
    case 'hourly':
      return listMockAdminHourlyTrend(params).map(mapHourlyTrendRow)
    case 'monthly':
      return listMockAdminMonthlyTrend(params).map(mapMonthlyTrendRow)
  }
}

export function buildAdminTrendCsvText(kind: AdminTrendCsvKind, rows: AdminTrendCsvRow[]) {
  const periodHeader = {
    daily: 'reportDate',
    hourly: 'reportHour',
    monthly: 'reportMonth',
  }[kind]
  const body = rows.map((row) => [
    escapeCsvCell(row.period),
    ...adminTrendMetricCsvHeaders.map((header) => escapeCsvCell(row[header])),
  ].join(','))

  return `\ufeff${[[periodHeader, ...adminTrendMetricCsvHeaders].join(','), ...body].join('\r\n')}`
}

function csvFileName(params: AdminReportParams = {}) {
  const dateFrom = params.dateFrom?.trim() || 'all'
  const dateTo = params.dateTo?.trim() || 'all'
  return `admin-orders-${dateFrom}-${dateTo}.csv`
}

function xlsxFileName(params: AdminReportParams = {}) {
  const dateFrom = params.dateFrom?.trim() || 'all'
  const dateTo = params.dateTo?.trim() || 'all'
  return `admin-orders-${dateFrom}-${dateTo}.xlsx`
}

function trendCsvFileName(kind: AdminTrendCsvKind, params: AdminTrendReportParams = {}) {
  const dateFrom = params.dateFrom?.trim()?.replaceAll('-', '') || 'all'
  const dateTo = params.dateTo?.trim()?.replaceAll('-', '') || 'all'
  return `admin-${kind}-trend-${dateFrom}-${dateTo}.csv`
}

function trendXlsxFileName(kind: AdminTrendCsvKind, params: AdminTrendReportParams = {}) {
  const dateFrom = params.dateFrom?.trim()?.replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim()?.replaceAll('-', '') || 'end'
  return `admin-${kind}-trend-${dateFrom}-${dateTo}.xlsx`
}

function paymentReconciliationCsvFileName(params: AdminReportParams = {}) {
  const dateFrom = params.dateFrom?.trim()?.replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim()?.replaceAll('-', '') || 'end'
  return `admin-payment-reconciliation-${dateFrom}-${dateTo}.csv`
}

function paymentReconciliationXlsxFileName(params: AdminReportParams = {}) {
  const dateFrom = params.dateFrom?.trim()?.replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim()?.replaceAll('-', '') || 'end'
  return `admin-payment-reconciliation-${dateFrom}-${dateTo}.xlsx`
}

function productBreakdownCsvFileName(params: AdminReportParams = {}) {
  const dateFrom = params.dateFrom?.trim()?.replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim()?.replaceAll('-', '') || 'end'
  return `admin-product-breakdown-${dateFrom}-${dateTo}.csv`
}

function productBreakdownXlsxFileName(params: AdminReportParams = {}) {
  const dateFrom = params.dateFrom?.trim()?.replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim()?.replaceAll('-', '') || 'end'
  return `admin-product-breakdown-${dateFrom}-${dateTo}.xlsx`
}

function downloadBlob(blob: Blob, fileName: string) {
  const objectUrl = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = objectUrl
  link.download = fileName
  link.rel = 'noopener'
  document.body.append(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(objectUrl)
}

export function buildAdminOrdersXlsxBlob(rows: AdminOrderCsvRow[]) {
  return buildWorkbookBlob('Orders', [
    adminOrderCsvHeaders,
    ...rows.map((row) => adminOrderCsvHeaders.map((header) => row[header])),
  ])
}

export function buildAdminPaymentReconciliationCsvText(row: AdminPaymentReconciliation) {
  const body = adminPaymentReconciliationCsvHeaders.map((header) => escapeCsvCell(String(row[header]))).join(',')
  return `\ufeff${[adminPaymentReconciliationCsvHeaders.join(','), body].join('\r\n')}`
}

function productBreakdownExportValue(row: AdminProductBreakdown, header: keyof AdminProductBreakdown) {
  if (header === 'productName') {
    return scenicProductName(row.productName)
  }

  if (header === 'ticketName') {
    return scenicTicketName(row.ticketName)
  }

  return row[header]
}

export function buildAdminProductBreakdownCsvText(rows: AdminProductBreakdown[]) {
  const body = rows.map((row) => adminProductBreakdownCsvHeaders.map((header) => escapeCsvCell(productBreakdownExportValue(row, header))).join(','))
  return `\ufeff${[adminProductBreakdownCsvHeaders.join(','), ...body].join('\r\n')}`
}

export function buildAdminPaymentReconciliationXlsxBlob(row: AdminPaymentReconciliation) {
  return buildWorkbookBlob('Payment Reconciliation', [
    adminPaymentReconciliationCsvHeaders,
    adminPaymentReconciliationCsvHeaders.map((header) => row[header]),
  ])
}

export function buildAdminProductBreakdownXlsxBlob(rows: AdminProductBreakdown[]) {
  return buildWorkbookBlob('Product Breakdown', [
    adminProductBreakdownCsvHeaders,
    ...rows.map((row) => adminProductBreakdownCsvHeaders.map((header) => productBreakdownExportValue(row, header))),
  ])
}

export function buildAdminTrendXlsxBlob(kind: AdminTrendCsvKind, rows: AdminTrendCsvRow[]) {
  const periodHeader = {
    daily: 'reportDate',
    hourly: 'reportHour',
    monthly: 'reportMonth',
  }[kind]
  const sheetName = {
    daily: 'Daily Trend',
    hourly: 'Hourly Trend',
    monthly: 'Monthly Trend',
  }[kind]

  return buildWorkbookBlob(sheetName, [
    [periodHeader, ...adminTrendMetricCsvHeaders],
    ...rows.map((row) => [
      row.period,
      ...adminTrendMetricCsvHeaders.map((header) => row[header]),
    ]),
  ])
}

export async function downloadAdminOrdersCsv(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)
  const blob = adminReportsMode === 'api'
    ? await adminReportExportsApi.ordersCsv(normalizedParams)
    : new Blob([buildAdminOrdersCsvText(listMockAdminOrderCsvRows(normalizedParams))], {
      type: 'text/csv;charset=utf-8',
    })

  downloadBlob(blob, csvFileName(normalizedParams))
}

export async function downloadAdminPaymentReconciliationCsv(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)
  const blob = adminReportsMode === 'api'
    ? await adminReportExportsApi.paymentReconciliationCsv(normalizedParams)
    : new Blob([buildAdminPaymentReconciliationCsvText(getMockAdminPaymentReconciliation(normalizedParams))], {
      type: 'text/csv;charset=utf-8',
    })

  downloadBlob(blob, paymentReconciliationCsvFileName(normalizedParams))
}

export async function downloadAdminProductBreakdownCsv(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)
  const rows = adminReportsMode === 'api'
    ? await adminReportsApi.productBreakdown(normalizedParams)
    : listMockAdminProductBreakdown(normalizedParams)
  const blob = new Blob([buildAdminProductBreakdownCsvText(rows)], {
      type: 'text/csv;charset=utf-8',
    })

  downloadBlob(blob, productBreakdownCsvFileName(normalizedParams))
}

export async function downloadAdminPaymentReconciliationXlsx(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)
  const blob = adminReportsMode === 'api'
    ? await adminReportExportsApi.paymentReconciliationXlsx(normalizedParams)
    : buildAdminPaymentReconciliationXlsxBlob(getMockAdminPaymentReconciliation(normalizedParams))

  downloadBlob(blob, paymentReconciliationXlsxFileName(normalizedParams))
}

export async function downloadAdminProductBreakdownXlsx(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)
  const rows = adminReportsMode === 'api'
    ? await adminReportsApi.productBreakdown(normalizedParams)
    : listMockAdminProductBreakdown(normalizedParams)
  const blob = buildAdminProductBreakdownXlsxBlob(rows)

  downloadBlob(blob, productBreakdownXlsxFileName(normalizedParams))
}

export async function downloadAdminOrdersXlsx(params: AdminReportParams = {}) {
  const normalizedParams = normalizeAdminReportParams(params)
  const blob = adminReportsMode === 'api'
    ? await adminReportExportsApi.ordersXlsx(normalizedParams)
    : buildAdminOrdersXlsxBlob(listMockAdminOrderCsvRows(normalizedParams))

  downloadBlob(blob, xlsxFileName(normalizedParams))
}

export async function downloadAdminTrendCsv(kind: AdminTrendCsvKind, params: AdminTrendReportParams = {}) {
  const normalizedParams = normalizeAdminTrendReportParams(params)
  const blob = adminReportsMode === 'api'
    ? await {
      daily: adminReportExportsApi.dailyTrendCsv,
      hourly: adminReportExportsApi.hourlyTrendCsv,
      monthly: adminReportExportsApi.monthlyTrendCsv,
    }[kind](normalizedParams)
    : new Blob([buildAdminTrendCsvText(kind, listMockAdminTrendCsvRows(kind, normalizedParams))], {
      type: 'text/csv;charset=utf-8',
    })

  downloadBlob(blob, trendCsvFileName(kind, normalizedParams))
}

export async function downloadAdminTrendXlsx(kind: AdminTrendCsvKind, params: AdminTrendReportParams = {}) {
  const normalizedParams = normalizeAdminTrendReportParams(params)
  const blob = adminReportsMode === 'api'
    ? await {
      daily: adminReportExportsApi.dailyTrendXlsx,
      hourly: adminReportExportsApi.hourlyTrendXlsx,
      monthly: adminReportExportsApi.monthlyTrendXlsx,
    }[kind](normalizedParams)
    : buildAdminTrendXlsxBlob(kind, listMockAdminTrendCsvRows(kind, normalizedParams))

  downloadBlob(blob, trendXlsxFileName(kind, normalizedParams))
}
