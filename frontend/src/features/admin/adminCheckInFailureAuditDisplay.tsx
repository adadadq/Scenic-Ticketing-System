import { Tag } from 'antd'
import type { AdminCheckInFailureCode } from '../../shared/api/types'

export type CheckInFailureCodeFilter = 'ALL' | AdminCheckInFailureCode

export const checkInFailureCodeOptions: Array<{ label: string; value: CheckInFailureCodeFilter }> = [
  { label: '全部失败码', value: 'ALL' },
  { label: '票码不存在', value: 'TICKET_NOT_FOUND' },
  { label: '票码已核销', value: 'TICKET_ALREADY_USED' },
  { label: '状态不可核验', value: 'TICKET_NOT_CHECKABLE' },
  { label: '票码未核销', value: 'TICKET_NOT_CHECKED_IN' },
  { label: '撤销状态不允许', value: 'TICKET_UNDO_NOT_ALLOWED' },
]

const failureCodeMeta: Record<string, { color: string; label: string }> = {
  TICKET_NOT_FOUND: { color: 'red', label: '票码不存在' },
  TICKET_ALREADY_USED: { color: 'orange', label: '票码已核销' },
  TICKET_NOT_CHECKABLE: { color: 'volcano', label: '状态不可核验' },
  TICKET_NOT_CHECKED_IN: { color: 'blue', label: '票码未核销' },
  TICKET_UNDO_NOT_ALLOWED: { color: 'purple', label: '撤销状态不允许' },
}

export function checkInFailureCodeTag(code: AdminCheckInFailureCode) {
  const meta = failureCodeMeta[code] ?? { color: 'default', label: code }
  return <Tag color={meta.color}>{meta.label}</Tag>
}
