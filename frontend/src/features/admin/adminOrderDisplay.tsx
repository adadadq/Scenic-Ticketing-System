import { Tag } from 'antd'
import type {
  AdminOrderDetail,
  AdminOrderStatus,
  AdminOrderStatusFilter,
  AdminPaymentStatus,
  AdminPaymentStatusFilter,
  OrderItemStatus,
} from '../../shared/api/types'

const orderStatusMeta: Record<string, { color: string; label: string }> = {
  CANCELLED: { color: 'default', label: '已取消' },
  COMPLETED: { color: 'green', label: '已完成' },
  CREATED: { color: 'blue', label: '待支付' },
  PAID: { color: 'green', label: '已支付' },
  REFUNDED: { color: 'default', label: '已退款' },
  REFUNDING: { color: 'orange', label: '退款中' },
}

const paymentStatusMeta: Record<string, { color: string; label: string }> = {
  FAILED: { color: 'red', label: '支付失败' },
  PAID: { color: 'green', label: '已支付' },
  PARTIAL_REFUND: { color: 'orange', label: '部分退款' },
  REFUNDED: { color: 'default', label: '已退款' },
  UNPAID: { color: 'blue', label: '未支付' },
}

const itemStatusMeta: Record<string, { color: string; label: string }> = {
  CANCELLED: { color: 'default', label: '已取消' },
  PENDING_PAYMENT: { color: 'blue', label: '待支付' },
  REFUNDED: { color: 'default', label: '已退款' },
  REFUNDING: { color: 'orange', label: '退款中' },
  UNUSED: { color: 'green', label: '未使用' },
  USED: { color: 'purple', label: '已核验' },
}

export const orderStatusOptions = [
  { label: '全部订单状态', value: 'ALL' },
  { label: '待支付', value: 'CREATED' },
  { label: '已支付', value: 'PAID' },
  { label: '已取消', value: 'CANCELLED' },
  { label: '已完成', value: 'COMPLETED' },
  { label: '退款中', value: 'REFUNDING' },
  { label: '已退款', value: 'REFUNDED' },
] satisfies Array<{ label: string; value: AdminOrderStatusFilter | 'ALL' }>

export const paymentStatusOptions = [
  { label: '全部支付状态', value: 'ALL' },
  { label: '未支付', value: 'UNPAID' },
  { label: '已支付', value: 'PAID' },
  { label: '部分退款', value: 'PARTIAL_REFUND' },
  { label: '已退款', value: 'REFUNDED' },
  { label: '支付失败', value: 'FAILED' },
] satisfies Array<{ label: string; value: AdminPaymentStatusFilter | 'ALL' }>

export function statusTag(status: AdminOrderStatus) {
  const meta = orderStatusMeta[status] ?? { color: 'default', label: status }
  return <Tag color={meta.color}>{meta.label}</Tag>
}

export function paymentTag(status: AdminPaymentStatus) {
  const meta = paymentStatusMeta[status] ?? { color: 'default', label: status }
  return <Tag color={meta.color}>{meta.label}</Tag>
}

export function itemStatusTag(status: OrderItemStatus) {
  const meta = itemStatusMeta[status] ?? { color: 'default', label: status }
  return <Tag color={meta.color}>{meta.label}</Tag>
}

export function itemStatusLabel(status: OrderItemStatus) {
  return itemStatusMeta[status]?.label ?? status
}

export function amountLabel(amount: string) {
  return `¥ ${amount}`
}

export function normalizeAdminPhoneFilter(value: string) {
  const trimmed = value.trim()

  if (!trimmed) {
    return ''
  }

  const digits = trimmed.replace(/\D/g, '')

  if ((trimmed.includes('*') || digits.length === 11) && digits.length >= 4) {
    return digits.slice(-4)
  }

  return trimmed
}

export function slotLabel(item: AdminOrderDetail['items'][number]) {
  return `${item.visitDate} ${item.slotStartTime.slice(0, 5)}-${item.slotEndTime.slice(0, 5)}`
}

export function raftLabel(item?: Pick<AdminOrderDetail['items'][number], 'raftNo' | 'raftSeatNo'> | null) {
  return item?.raftNo && item?.raftSeatNo ? `竹筏 ${item.raftNo} / 座位 ${item.raftSeatNo}` : '待核验分配'
}

export function canCheckInItem(detail: AdminOrderDetail, item: AdminOrderDetail['items'][number]) {
  return (
    detail.orderStatus === 'PAID' &&
    (detail.paymentStatus === 'PAID' || detail.paymentStatus === 'PARTIAL_REFUND') &&
    item.itemStatus === 'UNUSED' &&
    Boolean(item.ticketCode)
  )
}

export function canFullRefundOrder(detail: AdminOrderDetail) {
  return (
    detail.orderStatus === 'PAID' &&
    detail.paymentStatus === 'PAID' &&
    detail.items.length > 0 &&
    detail.items.every((item) => item.itemStatus === 'UNUSED')
  )
}

export function canPartialRefundOrder(detail: AdminOrderDetail) {
  return (
    detail.orderStatus === 'PAID' &&
    (detail.paymentStatus === 'PAID' || detail.paymentStatus === 'PARTIAL_REFUND') &&
    detail.items.some((item) => item.itemStatus === 'UNUSED') &&
    detail.items.every((item) => item.itemStatus === 'UNUSED' || item.itemStatus === 'REFUNDED')
  )
}

export function canPartialRefundItem(detail: AdminOrderDetail, item: AdminOrderDetail['items'][number]) {
  return canPartialRefundOrder(detail) && item.itemStatus === 'UNUSED'
}
