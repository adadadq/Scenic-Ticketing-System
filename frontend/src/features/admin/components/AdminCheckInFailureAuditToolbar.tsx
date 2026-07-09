import { Button, Flex, Input, Select } from 'antd'
import {
  checkInFailureCodeOptions,
  type CheckInFailureCodeFilter,
} from '../adminCheckInFailureAuditDisplay'

export function AdminCheckInFailureAuditToolbar({
  dateFrom,
  dateTo,
  failureCode,
  onClear,
  onDateFromChange,
  onDateToChange,
  onFailureCodeChange,
  onOperatorUsernameChange,
  onTicketCodeChange,
  operatorUsername,
  ticketCode,
}: {
  dateFrom: string
  dateTo: string
  failureCode: CheckInFailureCodeFilter
  onClear: () => void
  onDateFromChange: (value: string) => void
  onDateToChange: (value: string) => void
  onFailureCodeChange: (value: CheckInFailureCodeFilter) => void
  onOperatorUsernameChange: (value: string) => void
  onTicketCodeChange: (value: string) => void
  operatorUsername: string
  ticketCode: string
}) {
  return (
    <Flex className="admin-check-in-failure-log-toolbar" gap={10} wrap>
      <Select<CheckInFailureCodeFilter>
        aria-label="核验失败码筛选"
        className="admin-check-in-failure-log-control"
        classNames={{ popup: { root: 'admin-check-in-failure-log-popup' } }}
        onChange={onFailureCodeChange}
        options={checkInFailureCodeOptions}
        value={failureCode}
      />
      <Input
        allowClear
        aria-label="核验失败票码筛选"
        className="admin-check-in-failure-log-control"
        onChange={(event) => onTicketCodeChange(event.target.value)}
        placeholder="失败票码"
        value={ticketCode}
      />
      <Input
        allowClear
        aria-label="核验失败操作人筛选"
        className="admin-check-in-failure-log-control"
        onChange={(event) => onOperatorUsernameChange(event.target.value)}
        placeholder="失败操作人用户名"
        value={operatorUsername}
      />
      <Input
        allowClear
        aria-label="核验失败开始日期筛选"
        className="admin-check-in-failure-log-control"
        onChange={(event) => onDateFromChange(event.target.value)}
        placeholder="失败日期从"
        value={dateFrom}
      />
      <Input
        allowClear
        aria-label="核验失败结束日期筛选"
        className="admin-check-in-failure-log-control"
        onChange={(event) => onDateToChange(event.target.value)}
        placeholder="失败日期至"
        value={dateTo}
      />
      <Button className="admin-check-in-failure-log-reset-action" onClick={onClear}>
        重置失败筛选
      </Button>
    </Flex>
  )
}
