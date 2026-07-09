import { adminRefundAuditLogExportsApi } from '../../shared/api/endpoints'
import type { AdminRefundAuditLog, AdminRefundAuditLogExportParams } from '../../shared/api/types'
import { listMockAdminRefundAuditLogExportRows } from './mockData'
import { adminRefundLogsMode } from './queries'

const adminRefundLogHeaders: Array<keyof AdminRefundAuditLog> = [
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
const adminRefundLogXlsxContentType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
const textEncoder = new TextEncoder()
let crc32Table: number[] | undefined

function compactText(value?: string) {
  const trimmed = value?.trim()
  return trimmed || undefined
}

export function normalizeAdminRefundAuditLogExportParams(
  params: AdminRefundAuditLogExportParams = {},
): AdminRefundAuditLogExportParams {
  return {
    ...(params.refundType ? { refundType: params.refundType } : {}),
    ...(compactText(params.orderNo) ? { orderNo: compactText(params.orderNo) } : {}),
    ...(compactText(params.operatorUsername) ? { operatorUsername: compactText(params.operatorUsername) } : {}),
    ...(compactText(params.dateFrom) ? { dateFrom: compactText(params.dateFrom) } : {}),
    ...(compactText(params.dateTo) ? { dateTo: compactText(params.dateTo) } : {}),
  }
}

export function neutralizeRefundAuditSpreadsheetText(value: string | number | null) {
  const text = String(value ?? '')
  const hasDangerousPrefix = /^[\t\r\n=+\-@]/.test(text) || /^ +[\t\r\n=+\-@]/.test(text)
  return hasDangerousPrefix ? `'${text}` : text
}

function sanitizeXmlText(value: string) {
  return Array.from(value)
    .filter((character) => {
      const codePoint = character.codePointAt(0)
      return codePoint === 0x9 ||
        codePoint === 0xA ||
        codePoint === 0xD ||
        (codePoint !== undefined && codePoint >= 0x20 && codePoint <= 0xD7FF) ||
        (codePoint !== undefined && codePoint >= 0xE000 && codePoint <= 0xFFFD) ||
        (codePoint !== undefined && codePoint >= 0x10000 && codePoint <= 0x10FFFF)
    })
    .join('')
}

function escapeXmlText(value: string | number | null) {
  return neutralizeRefundAuditSpreadsheetText(sanitizeXmlText(String(value ?? '')))
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

function columnName(index: number) {
  let name = ''
  let cursor = index + 1

  while (cursor > 0) {
    const remainder = (cursor - 1) % 26
    name = String.fromCharCode(65 + remainder) + name
    cursor = Math.floor((cursor - 1) / 26)
  }

  return name
}

function refundAuditCellValue(row: AdminRefundAuditLog, header: keyof AdminRefundAuditLog) {
  const value = row[header]
  return Array.isArray(value) ? value.join(';') : value
}

function buildWorksheetXml(rows: AdminRefundAuditLog[]) {
  const tableRows = [
    adminRefundLogHeaders,
    ...rows.map((row) => adminRefundLogHeaders.map((header) => refundAuditCellValue(row, header))),
  ]
  const xmlRows = tableRows.map((row, rowIndex) => {
    const cells = row.map((value, columnIndex) => {
      const cellRef = `${columnName(columnIndex)}${rowIndex + 1}`
      return `<c r="${cellRef}" t="inlineStr"><is><t>${escapeXmlText(value)}</t></is></c>`
    })

    return `<row r="${rowIndex + 1}">${cells.join('')}</row>`
  })

  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
    `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">` +
    `<sheetData>${xmlRows.join('')}</sheetData>` +
    `</worksheet>`
}

function makeCrc32Table() {
  return Array.from({ length: 256 }, (_, index) => {
    let value = index

    for (let bit = 0; bit < 8; bit += 1) {
      value = value & 1 ? 0xEDB88320 ^ (value >>> 1) : value >>> 1
    }

    return value >>> 0
  })
}

function crc32(bytes: Uint8Array) {
  crc32Table ??= makeCrc32Table()
  let crc = 0xFFFFFFFF

  for (const byte of bytes) {
    crc = (crc >>> 8) ^ crc32Table[(crc ^ byte) & 0xFF]
  }

  return (crc ^ 0xFFFFFFFF) >>> 0
}

function writeUint16(output: number[], value: number) {
  output.push(value & 0xFF, (value >>> 8) & 0xFF)
}

function writeUint32(output: number[], value: number) {
  output.push(value & 0xFF, (value >>> 8) & 0xFF, (value >>> 16) & 0xFF, (value >>> 24) & 0xFF)
}

function appendBytes(output: number[], bytes: Uint8Array) {
  for (const byte of bytes) {
    output.push(byte)
  }
}

function buildStoreZip(files: Array<{ name: string; content: string }>) {
  const output: number[] = []
  const centralDirectory: number[] = []

  for (const file of files) {
    const nameBytes = textEncoder.encode(file.name)
    const contentBytes = textEncoder.encode(file.content)
    const checksum = crc32(contentBytes)
    const localHeaderOffset = output.length

    writeUint32(output, 0x04034B50)
    writeUint16(output, 20)
    writeUint16(output, 0)
    writeUint16(output, 0)
    writeUint16(output, 0)
    writeUint16(output, 0)
    writeUint32(output, checksum)
    writeUint32(output, contentBytes.length)
    writeUint32(output, contentBytes.length)
    writeUint16(output, nameBytes.length)
    writeUint16(output, 0)
    appendBytes(output, nameBytes)
    appendBytes(output, contentBytes)

    writeUint32(centralDirectory, 0x02014B50)
    writeUint16(centralDirectory, 20)
    writeUint16(centralDirectory, 20)
    writeUint16(centralDirectory, 0)
    writeUint16(centralDirectory, 0)
    writeUint16(centralDirectory, 0)
    writeUint16(centralDirectory, 0)
    writeUint32(centralDirectory, checksum)
    writeUint32(centralDirectory, contentBytes.length)
    writeUint32(centralDirectory, contentBytes.length)
    writeUint16(centralDirectory, nameBytes.length)
    writeUint16(centralDirectory, 0)
    writeUint16(centralDirectory, 0)
    writeUint16(centralDirectory, 0)
    writeUint16(centralDirectory, 0)
    writeUint32(centralDirectory, 0)
    writeUint32(centralDirectory, localHeaderOffset)
    appendBytes(centralDirectory, nameBytes)
  }

  const centralDirectoryOffset = output.length
  output.push(...centralDirectory)
  writeUint32(output, 0x06054B50)
  writeUint16(output, 0)
  writeUint16(output, 0)
  writeUint16(output, files.length)
  writeUint16(output, files.length)
  writeUint32(output, centralDirectory.length)
  writeUint32(output, centralDirectoryOffset)
  writeUint16(output, 0)

  return new Uint8Array(output)
}

export function buildAdminRefundAuditLogsXlsxBlob(rows: AdminRefundAuditLog[]) {
  const files = [
    {
      name: '[Content_Types].xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
        `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">` +
        `<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>` +
        `<Default Extension="xml" ContentType="application/xml"/>` +
        `<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>` +
        `<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>` +
        `</Types>`,
    },
    {
      name: '_rels/.rels',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
        `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` +
        `<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>` +
        `</Relationships>`,
    },
    {
      name: 'xl/workbook.xml',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
        `<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ` +
        `xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">` +
        `<sheets><sheet name="RefundLogs" sheetId="1" r:id="rId1"/></sheets>` +
        `</workbook>`,
    },
    {
      name: 'xl/_rels/workbook.xml.rels',
      content: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
        `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">` +
        `<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>` +
        `</Relationships>`,
    },
    {
      name: 'xl/worksheets/sheet1.xml',
      content: buildWorksheetXml(rows),
    },
  ]

  return new Blob([buildStoreZip(files)], { type: adminRefundLogXlsxContentType })
}

function xlsxFileName(params: AdminRefundAuditLogExportParams = {}) {
  const dateFrom = params.dateFrom?.trim().replaceAll('-', '') || 'start'
  const dateTo = params.dateTo?.trim().replaceAll('-', '') || 'end'
  return `admin-refund-logs-${dateFrom}-${dateTo}.xlsx`
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

export async function downloadAdminRefundAuditLogsXlsx(params: AdminRefundAuditLogExportParams = {}) {
  const normalizedParams = normalizeAdminRefundAuditLogExportParams(params)
  const blob = adminRefundLogsMode === 'api'
    ? await adminRefundAuditLogExportsApi.xlsx(normalizedParams)
    : buildAdminRefundAuditLogsXlsxBlob(listMockAdminRefundAuditLogExportRows(normalizedParams))

  downloadBlob(blob, xlsxFileName(normalizedParams))
}
