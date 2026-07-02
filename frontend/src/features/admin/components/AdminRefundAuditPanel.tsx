import { Alert, Button, Flex, Table, Tag, Typography } from 'antd'
import type { AdminRefundAuditLog } from '../../../shared/api/types'
import { amountLabel } from '../adminOrderDisplay'
import { AdminRefundAuditErrorDetails } from './AdminOrderDetailErrorDetails'

const { Text, Title } = Typography

type AdminRefundAuditPanelProps = {
  onRetry: () => void
  refundLogs: AdminRefundAuditLog[]
  refundLogsError: unknown
  refundLogsLoading: boolean
}

export function AdminRefundAuditPanel({
  onRetry,
  refundLogs,
  refundLogsError,
  refundLogsLoading,
}: AdminRefundAuditPanelProps) {
  return (
    <div className="admin-refund-audit-panel">
      <Flex align="center" justify="space-between" wrap>
        <Title level={3}>退款审计日志</Title>
        <Text type="secondary">只读 GET，不提交操作人、金额或状态。</Text>
      </Flex>
      {refundLogsError ? (
        <Alert
          showIcon
          type="error"
          title="退款审计日志读取失败"
          description={<AdminRefundAuditErrorDetails error={refundLogsError} />}
          action={(
            <Button size="small" onClick={onRetry}>
              重试
            </Button>
          )}
        />
      ) : (
        <Table<AdminRefundAuditLog>
          className="admin-refund-audit-table"
          columns={[
            {
              dataIndex: 'refundType',
              title: '类型',
              render: (refundType: AdminRefundAuditLog['refundType']) =>
                <Tag color={refundType === 'FULL' ? 'red' : 'orange'}>{refundType === 'FULL' ? '整单' : '部分'}</Tag>,
            },
            {
              dataIndex: 'refundedAmount',
              title: '退款金额',
              render: (amount: string) => amountLabel(amount),
            },
            {
              dataIndex: 'refundedItemNos',
              title: '票项',
              render: (itemNos: string[]) => itemNos.length > 0 ? itemNos.join('、') : '整单',
            },
            { dataIndex: 'reason', title: '原因', render: (reason: string | null) => reason || '未填写' },
            {
              key: 'operator',
              title: '操作人',
              render: (_, log) => `${log.operatorDisplayName} @${log.operatorUsername}`,
            },
            {
              dataIndex: 'requestId',
              title: '请求编号',
              render: (requestId: string | null) => requestId ? <Text code>{requestId}</Text> : <Text type="secondary">无</Text>,
            },
            { dataIndex: 'createdAt', title: '时间' },
          ]}
          dataSource={refundLogs}
          loading={refundLogsLoading}
          locale={{ emptyText: '暂无退款审计记录' }}
          pagination={false}
          rowKey={(log) =>
            `${log.orderNo}-${log.refundType}-${log.createdAt}-${log.requestId ?? log.refundedItemNos.join('-')}`
          }
          scroll={{ x: 940 }}
          size="small"
        />
      )}
    </div>
  )
}
