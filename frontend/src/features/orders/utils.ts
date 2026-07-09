import type { OrderListItem } from './types'

const paymentHoldMinutes = 15

export function orderStatusColor(tone: OrderListItem['orderStatusTone']) {
  if (tone === 'success') {
    return 'green'
  }

  if (tone === 'warning') {
    return 'gold'
  }

  if (tone === 'processing') {
    return 'blue'
  }

  return 'default'
}

export function formatCurrency(amount: number) {
  return new Intl.NumberFormat('zh-CN', {
    currency: 'CNY',
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    style: 'currency',
  }).format(amount)
}

export function formatPaymentDeadline(orderTime: string) {
  const startedAt = new Date(orderTime)

  if (Number.isNaN(startedAt.getTime())) {
    return '请尽快完成支付，余票以支付结果为准。'
  }

  const deadline = new Date(startedAt.getTime() + paymentHoldMinutes * 60 * 1000)
  return `建议于 ${deadline.toLocaleString('zh-CN', {
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    month: '2-digit',
  })} 前完成支付，余票以支付结果为准。`
}
