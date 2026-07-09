import { Tag } from 'antd'
import type { AdminRefundType } from '../../shared/api/types'

export type RefundTypeFilter = AdminRefundType | 'ALL'

export const refundTypeOptions = [
  { label: '全部退款类型', value: 'ALL' },
  { label: '整单退款', value: 'FULL' },
  { label: '部分退款', value: 'PARTIAL' },
] satisfies Array<{ label: string; value: RefundTypeFilter }>

export function amountLabel(amount: string) {
  return `¥ ${amount}`
}

export function refundTypeTag(type: AdminRefundType) {
  return type === 'FULL' ? <Tag color="red">整单退款</Tag> : <Tag color="orange">部分退款</Tag>
}
