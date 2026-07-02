import { Button, Flex, Input, Select } from 'antd'
import { refundTypeOptions, type RefundTypeFilter } from '../adminRefundAuditDisplay'

export function AdminRefundAuditToolbar({
  dateFrom,
  dateTo,
  onClear,
  onDateFromChange,
  onDateToChange,
  onOperatorUsernameChange,
  onOrderNoChange,
  onRefundTypeChange,
  operatorUsername,
  orderNo,
  refundType,
}: {
  dateFrom: string
  dateTo: string
  onClear: () => void
  onDateFromChange: (value: string) => void
  onDateToChange: (value: string) => void
  onOperatorUsernameChange: (value: string) => void
  onOrderNoChange: (value: string) => void
  onRefundTypeChange: (value: RefundTypeFilter) => void
  operatorUsername: string
  orderNo: string
  refundType: RefundTypeFilter
}) {
  return (
    <Flex className="admin-refund-log-toolbar" gap={10} wrap>
      <Select<RefundTypeFilter>
        aria-label="退款类型筛选"
        className="admin-refund-log-type-select admin-refund-log-control"
        classNames={{ popup: { root: 'admin-refund-log-type-popup' } }}
        onChange={onRefundTypeChange}
        options={refundTypeOptions}
        value={refundType}
      />
      <Input
        allowClear
        className="admin-refund-log-control"
        onChange={(event) => onOrderNoChange(event.target.value)}
        placeholder="搜索审计订单号"
        value={orderNo}
      />
      <Input
        allowClear
        className="admin-refund-log-control"
        onChange={(event) => onOperatorUsernameChange(event.target.value)}
        placeholder="操作人用户名"
        value={operatorUsername}
      />
      <Input
        allowClear
        className="admin-refund-log-control"
        onChange={(event) => onDateFromChange(event.target.value)}
        placeholder="开始日期"
        value={dateFrom}
      />
      <Input
        allowClear
        className="admin-refund-log-control"
        onChange={(event) => onDateToChange(event.target.value)}
        placeholder="结束日期"
        value={dateTo}
      />
      <Button className="admin-refund-log-reset-action" onClick={onClear}>
        重置审计筛选
      </Button>
    </Flex>
  )
}
