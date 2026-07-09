import { Space, Table, Typography } from 'antd'
import type { AdminCheckInFailureAuditLog, AdminCheckInFailureCode } from '../../../shared/api/types'
import { checkInFailureCodeTag } from '../adminCheckInFailureAuditDisplay'

const { Text } = Typography

function actionLabel(action: AdminCheckInFailureAuditLog['action']) {
  return action === 'UNDO_CHECK_IN' ? '撤销核验' : '票码核验'
}

export function AdminCheckInFailureAuditTable({
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
  rows: AdminCheckInFailureAuditLog[]
  total: number
}) {
  return (
    <Table<AdminCheckInFailureAuditLog>
      className="admin-check-in-failure-log-table"
      columns={[
        {
          dataIndex: 'createdAt',
          title: '时间',
          width: 170,
          render: (createdAt: string) => createdAt.replace('T', ' ').slice(0, 19),
        },
        {
          dataIndex: 'failureCode',
          title: '失败码',
          width: 130,
          render: (code: AdminCheckInFailureCode) => checkInFailureCodeTag(code),
        },
        {
          key: 'ticket',
          title: '票码 / 动作',
          width: 190,
          render: (_, log) => (
            <Space orientation="vertical" size={0}>
              <Text code>{log.ticketCode}</Text>
              <Text type="secondary">{actionLabel(log.action)}</Text>
            </Space>
          ),
        },
        {
          dataIndex: 'failureMessage',
          title: '失败原因',
          width: 160,
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
          dataIndex: 'requestId',
          title: '请求编号',
          width: 230,
          render: (requestId: string | null) => (requestId ? <Text code>{requestId}</Text> : <Text type="secondary">无</Text>),
        },
      ]}
      dataSource={rows}
      loading={isLoading}
      locale={{ emptyText: '暂无核验失败审计记录' }}
      pagination={{
        current: currentPage,
        onChange: onPageChange,
        pageSize,
        showSizeChanger: true,
        total,
      }}
      rowKey={(log) => `${log.ticketCode}-${log.failureCode}-${log.createdAt}-${log.requestId ?? 'no-request'}`}
      scroll={{ x: 1020 }}
      size="small"
    />
  )
}
