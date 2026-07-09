import { Space, Table, Typography } from 'antd'
import type { AdminRefundAuditLog, AdminRefundType } from '../../../shared/api/types'
import { amountLabel, refundTypeTag } from '../adminRefundAuditDisplay'

const { Text } = Typography

export function AdminRefundAuditTable({
  currentPage,
  isLoading,
  onPageChange,
  pageSize,
  rows,
  total,
}: {
  currentPage: number
  isLoading: boolean
  onPageChange: (nextPage: number, nextPageSize: number) => void
  pageSize: number
  rows: AdminRefundAuditLog[]
  total: number
}) {
  return (
    <Table<AdminRefundAuditLog>
      className="admin-refund-log-table"
      columns={[
        {
          dataIndex: 'createdAt',
          title: '时间',
          width: 170,
          render: (createdAt: string) => createdAt.replace('T', ' ').slice(0, 19),
        },
        {
          dataIndex: 'refundType',
          title: '类型',
          width: 96,
          render: (type: AdminRefundType) => refundTypeTag(type),
        },
        {
          key: 'order',
          title: '订单 / 金额',
          width: 160,
          render: (_, log) => (
            <Space orientation="vertical" size={0}>
              <Text>{log.orderNo}</Text>
              <Text type="secondary">{amountLabel(log.refundedAmount)} · {log.refundedItemCount} 张</Text>
            </Space>
          ),
        },
        {
          key: 'operator',
          title: '操作人',
          width: 140,
          render: (_, log) => (
            <Space orientation="vertical" size={0}>
              <Text>{log.operatorDisplayName}</Text>
              <Text type="secondary">@{log.operatorUsername}</Text>
            </Space>
          ),
        },
        {
          dataIndex: 'reason',
          title: '原因',
          width: 150,
          render: (reason: string | null) => reason || '未填写',
        },
        {
          dataIndex: 'requestId',
          title: '请求编号',
          width: 210,
          render: (requestId: string | null) => (requestId ? <Text code>{requestId}</Text> : <Text type="secondary">无</Text>),
        },
      ]}
      dataSource={rows}
      loading={isLoading}
      locale={{ emptyText: '暂无退款审计记录' }}
      pagination={{
        current: currentPage,
        onChange: onPageChange,
        pageSize,
        showSizeChanger: true,
        total,
      }}
      rowKey={(log) => `${log.orderNo}-${log.refundType}-${log.createdAt}-${log.requestId ?? log.refundedItemNos.join('-')}`}
      scroll={{ x: 940 }}
      size="small"
    />
  )
}
