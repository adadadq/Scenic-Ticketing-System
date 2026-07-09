import type { OrderStatusTone } from './types'

export const orderStatusMeta: Record<string, { label: string; tone: OrderStatusTone }> = {
  CREATED: { label: '待支付', tone: 'processing' },
  PAID: { label: '已支付', tone: 'success' },
  CANCELLED: { label: '已取消', tone: 'default' },
  COMPLETED: { label: '已完成', tone: 'success' },
  REFUNDING: { label: '退款中', tone: 'warning' },
}

export function parseOrderAmount(amount: string): number {
  const value = Number(amount)

  if (!Number.isFinite(value) && import.meta.env.DEV) {
    console.warn('Invalid order amount received from API:', amount)
  }

  return Number.isFinite(value) ? value : 0
}

export function maskPhone(phone: string): string {
  return phone.replace(/^(\d{3})\d{4}(\d{4})$/, '$1****$2')
}

export function formatSlotLabel(slotStartTime?: string, slotEndTime?: string): string {
  if (!slotStartTime || !slotEndTime) {
    return '订单详情中查看'
  }

  return `${slotStartTime.slice(0, 5)}-${slotEndTime.slice(0, 5)}`
}
