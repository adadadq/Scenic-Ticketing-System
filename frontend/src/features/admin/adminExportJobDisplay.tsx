import { Tag } from 'antd'
import type {
  AdminCheckInFailureCode,
  AdminExportFileFormat,
  AdminExportJobFilters,
  AdminExportJobStatus,
  AdminExportType,
  AdminRefundType,
} from '../../shared/api/types'

export type ExportTypeOption = {
  label: string
  value: AdminExportType
}

export type AdminExportJobFilterDraft = {
  dateFrom: string
  dateTo: string
  exportType: AdminExportType
  failureCode: AdminCheckInFailureCode | ''
  includeEmpty: boolean
  operatorUsername: string
  orderNo: string
  refundType: AdminRefundType | ''
  ticketCode: string
}

export const exportTypeOptions: ExportTypeOption[] = [
  { label: '订单明细', value: 'ORDER_DETAIL' },
  { label: '核验审计', value: 'CHECK_IN_AUDIT' },
  { label: '核验失败审计', value: 'CHECK_IN_FAILURE_AUDIT' },
  { label: '退款审计', value: 'REFUND_AUDIT' },
  { label: '支付对账', value: 'PAYMENT_RECONCILIATION' },
  { label: '产品维度', value: 'PRODUCT_BREAKDOWN' },
  { label: '日报趋势', value: 'DAILY_TREND' },
  { label: '小时趋势', value: 'HOURLY_TREND' },
  { label: '月度趋势', value: 'MONTHLY_TREND' },
]

export const statusOptions: Array<{ label: string; value: AdminExportJobStatus }> = [
  { label: '待处理', value: 'PENDING' },
  { label: '处理中', value: 'RUNNING' },
  { label: '已完成', value: 'SUCCEEDED' },
  { label: '失败', value: 'FAILED' },
]

export const fileFormatOptions: Array<{ label: string; value: AdminExportFileFormat }> = [
  { label: 'CSV', value: 'CSV' },
  { label: 'XLSX', value: 'XLSX' },
]

export const failureCodeOptions: Array<{ label: string; value: AdminCheckInFailureCode }> = [
  { label: '票码不存在', value: 'TICKET_NOT_FOUND' },
  { label: '票码已核验', value: 'TICKET_ALREADY_USED' },
  { label: '票码不可核验', value: 'TICKET_NOT_CHECKABLE' },
  { label: '票码未核验', value: 'TICKET_NOT_CHECKED_IN' },
  { label: '不可撤销核验', value: 'TICKET_UNDO_NOT_ALLOWED' },
]

export const refundTypeOptions: Array<{ label: string; value: AdminRefundType }> = [
  { label: '整单退款', value: 'FULL' },
  { label: '部分退款', value: 'PARTIAL' },
]

export function exportTypeLabel(value: AdminExportType) {
  return exportTypeOptions.find((option) => option.value === value)?.label ?? value
}

export function statusTag(status: AdminExportJobStatus) {
  const colorMap: Record<AdminExportJobStatus, string> = {
    FAILED: 'red',
    PENDING: 'gold',
    RUNNING: 'blue',
    SUCCEEDED: 'green',
  }

  return <Tag color={colorMap[status]}>{statusOptions.find((option) => option.value === status)?.label ?? status}</Tag>
}

export function formatTime(value?: string | null) {
  return value ? value.replace('T', ' ').slice(0, 19) : '未开始'
}

export function filterEntries(filters: AdminExportJobFilters) {
  return Object.entries(filters).filter(([, value]) => value !== '' && value !== false)
}

export function filterTagLabel(key: string, value: string | boolean) {
  return `${key}: ${value === true ? 'true' : value}`
}

export function supportsTicketCode(exportType: AdminExportType) {
  return exportType === 'CHECK_IN_AUDIT' || exportType === 'CHECK_IN_FAILURE_AUDIT'
}

export function supportsOrderNo(exportType: AdminExportType) {
  return exportType === 'CHECK_IN_AUDIT' || exportType === 'REFUND_AUDIT'
}

export function supportsOperator(exportType: AdminExportType) {
  return exportType === 'CHECK_IN_AUDIT' || exportType === 'CHECK_IN_FAILURE_AUDIT' || exportType === 'REFUND_AUDIT'
}

export function supportsTrendEmpty(exportType: AdminExportType) {
  return exportType === 'DAILY_TREND' || exportType === 'HOURLY_TREND' || exportType === 'MONTHLY_TREND'
}

export function buildAdminExportJobFilters({
  dateFrom,
  dateTo,
  exportType,
  failureCode,
  includeEmpty,
  operatorUsername,
  orderNo,
  refundType,
  ticketCode,
}: AdminExportJobFilterDraft): AdminExportJobFilters {
  return {
    ...(dateFrom.trim() ? { dateFrom } : {}),
    ...(dateTo.trim() ? { dateTo } : {}),
    ...(supportsTicketCode(exportType) && ticketCode.trim() ? { ticketCode } : {}),
    ...(supportsOrderNo(exportType) && orderNo.trim() ? { orderNo } : {}),
    ...(supportsOperator(exportType) && operatorUsername.trim() ? { operatorUsername } : {}),
    ...(exportType === 'CHECK_IN_FAILURE_AUDIT' && failureCode ? { failureCode } : {}),
    ...(exportType === 'REFUND_AUDIT' && refundType ? { refundType } : {}),
    ...(supportsTrendEmpty(exportType) && includeEmpty ? { includeEmpty: true } : {}),
  }
}
