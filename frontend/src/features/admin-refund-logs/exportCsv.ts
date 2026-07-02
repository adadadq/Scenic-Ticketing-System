import { adminRefundAuditLogExportsApi } from '../../shared/api/endpoints'
import type { AdminRefundAuditLog, AdminRefundAuditLogExportParams } from '../../shared/api/types'
import { listMockAdminRefundAuditLogExportRows } from './mockData'
import { adminRefundLogsMode } from './queries'
import { normalizeAdminRefundAuditLogExportParams } from './exportXlsx'

type AdminRefundAuditCsvRow = Omit<AdminRefundAuditLog, 'refundedItemNos'> & {
  refundedItemNos: string
}

const adminRefundLogCsvHeaders: Array<keyof AdminRefundAuditCsvRow> = [
  'orderNo',
  'refundType',
  'refundedAmount',
  'refundedItemCount',
  'refundedItemNos',
  'reason',
  'operatorUsername',
  'operatorDisplayName',
  'requestId',
  'createdAt',
]

function sanitizeCsvText(value: string) {
  return Array.from(value)
    .filter((character) => {
      const codePoint = character.codePointAt(0)
      return codePoint === 0x9 ||
        codePoint === 0xA ||
        codePoint === 0xD ||
        (codePoint !== undefined && codePoint >= 0x20 && codePoint !== 0x7F)
    })
    .join('')
}

export function neutralizeRefundAuditCsvFormulaText(value: string | number | null) {
  const text = sanitizeCsvText(String(value ?? ''))
  const hasDangerousPrefix = /^[\t\r\n=+\-@]/.test(text) || /^ +[\t\r\n=+\-@]/.test(text)
  return hasDangerousPrefix ? `'${text}` : text
}

export function escapeRefundAuditCsvCell(value: string | number | null) {
  const safeText = neutralizeRefundAuditCsvFormulaText(value)
  const escapedText = safeText.replaceAll('"', '""')

  return /[",\t\r\n]/.test(safeText) ? `"${escapedText}"` : escapedText
}

export function listMockAdminRefundAuditCsvRows(params: AdminRefundAuditLogExportParams = {}): AdminRefundAuditCsvRow[] {
  return listMockAdminRefundAuditLogExportRows(params).map((log) => ({
    ...log,
    refundedItemNos: log.refundedItemNos.join(';'),
  }))
}

export function buildAdminRefundAuditCsvText(rows: AdminRefundAuditCsvRow[]) {
  const body = rows.map((row) => adminRefundLogCsvHeaders.map((header) => escapeRefundAuditCsvCell(row[header])).join(','))
  return `\ufeff${[adminRefundLogCsvHeaders.join(','), ...body].join('\r\n')}`
}

function csvFileName(params: AdminRefundAuditLogExportParams = {}) {
  const dateFrom = params.dateFrom?.trim().replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim().replaceAll('-', '') || 'end'
  return `admin-refund-logs-${dateFrom}-${dateTo}.csv`
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

export async function downloadAdminRefundAuditLogsCsv(params: AdminRefundAuditLogExportParams = {}) {
  const normalizedParams = normalizeAdminRefundAuditLogExportParams(params)
  const blob = adminRefundLogsMode === 'api'
    ? await adminRefundAuditLogExportsApi.csv(normalizedParams)
    : new Blob([buildAdminRefundAuditCsvText(listMockAdminRefundAuditCsvRows(normalizedParams))], {
      type: 'text/csv;charset=utf-8',
    })

  downloadBlob(blob, csvFileName(normalizedParams))
}
