import { adminCheckInAuditLogExportsApi } from '../../shared/api/endpoints'
import type { AdminCheckInAuditLog, AdminCheckInAuditLogExportParams } from '../../shared/api/types'
import {
  adminCheckInLogsMode,
  listMockAdminCheckInAuditLogExportRows,
  normalizeAdminCheckInAuditLogExportParams,
} from './exportXlsx'

const adminCheckInLogCsvHeaders: Array<keyof AdminCheckInAuditLog> = [
  'orderNo',
  'itemNo',
  'ticketCode',
  'action',
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

export function neutralizeCheckInAuditCsvFormulaText(value: string | number | null) {
  const text = sanitizeCsvText(String(value ?? ''))
  const hasDangerousPrefix = /^[\t\r\n=+\-@]/.test(text) || /^ +[\t\r\n=+\-@]/.test(text)
  return hasDangerousPrefix ? `'${text}` : text
}

export function escapeCheckInAuditCsvCell(value: string | number | null) {
  const safeText = neutralizeCheckInAuditCsvFormulaText(value)
  const escapedText = safeText.replaceAll('"', '""')

  return /[",\t\r\n]/.test(safeText) ? `"${escapedText}"` : escapedText
}

export function buildAdminCheckInAuditCsvText(rows: AdminCheckInAuditLog[]) {
  const body = rows.map((row) => adminCheckInLogCsvHeaders.map((header) => escapeCheckInAuditCsvCell(row[header])).join(','))
  return `\ufeff${[adminCheckInLogCsvHeaders.join(','), ...body].join('\r\n')}`
}

function csvFileName(params: AdminCheckInAuditLogExportParams = {}) {
  const dateFrom = params.dateFrom?.trim().replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim().replaceAll('-', '') || 'end'
  return `admin-check-in-logs-${dateFrom}-${dateTo}.csv`
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

export async function downloadAdminCheckInAuditLogsCsv(params: AdminCheckInAuditLogExportParams = {}) {
  const normalizedParams = normalizeAdminCheckInAuditLogExportParams(params)
  const blob = adminCheckInLogsMode === 'api'
    ? await adminCheckInAuditLogExportsApi.csv(normalizedParams)
    : new Blob([buildAdminCheckInAuditCsvText(listMockAdminCheckInAuditLogExportRows(normalizedParams))], {
      type: 'text/csv;charset=utf-8',
    })

  downloadBlob(blob, csvFileName(normalizedParams))
}
