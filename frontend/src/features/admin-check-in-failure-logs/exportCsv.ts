import { adminCheckInFailureAuditLogExportsApi } from '../../shared/api/endpoints'
import type {
  AdminCheckInFailureAuditLog,
  AdminCheckInFailureAuditLogExportParams,
} from '../../shared/api/types'
import { listMockAdminCheckInFailureAuditLogRows } from './mockData'
import {
  adminCheckInFailureLogsMode,
  normalizeAdminCheckInFailureAuditLogExportParams,
} from './queries'

const adminCheckInFailureLogCsvHeaders: Array<keyof AdminCheckInFailureAuditLog> = [
  'ticketCode',
  'action',
  'failureCode',
  'failureMessage',
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

export function neutralizeCheckInFailureAuditCsvFormulaText(value: string | number | null) {
  const text = sanitizeCsvText(String(value ?? ''))
  const hasDangerousPrefix = /^[\t\r\n=+\-@]/.test(text) || /^ +[\t\r\n=+\-@]/.test(text)
  return hasDangerousPrefix ? `'${text}` : text
}

export function escapeCheckInFailureAuditCsvCell(value: string | number | null) {
  const safeText = neutralizeCheckInFailureAuditCsvFormulaText(value)
  const escapedText = safeText.replaceAll('"', '""')

  return /[",\t\r\n]/.test(safeText) ? `"${escapedText}"` : escapedText
}

export function buildAdminCheckInFailureAuditCsvText(rows: AdminCheckInFailureAuditLog[]) {
  const body = rows.map((row) =>
    adminCheckInFailureLogCsvHeaders.map((header) => escapeCheckInFailureAuditCsvCell(row[header])).join(','),
  )
  return `\ufeff${[adminCheckInFailureLogCsvHeaders.join(','), ...body].join('\r\n')}`
}

function csvFileName(params: AdminCheckInFailureAuditLogExportParams = {}) {
  const dateFrom = params.dateFrom?.trim().replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim().replaceAll('-', '') || 'end'
  return `admin-check-in-failure-logs-${dateFrom}-${dateTo}.csv`
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

export async function downloadAdminCheckInFailureAuditLogsCsv(
  params: AdminCheckInFailureAuditLogExportParams = {},
) {
  const normalizedParams = normalizeAdminCheckInFailureAuditLogExportParams(params)
  const blob = adminCheckInFailureLogsMode === 'api'
    ? await adminCheckInFailureAuditLogExportsApi.csv(normalizedParams)
    : new Blob([buildAdminCheckInFailureAuditCsvText(listMockAdminCheckInFailureAuditLogRows(normalizedParams))], {
      type: 'text/csv;charset=utf-8',
    })

  downloadBlob(blob, csvFileName(normalizedParams))
}
