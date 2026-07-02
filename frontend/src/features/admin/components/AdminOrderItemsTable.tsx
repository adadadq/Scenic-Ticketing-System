import { CheckCircleOutlined } from '@ant-design/icons'
import { Button, Popconfirm, Space, Table, Tag, Typography } from 'antd'
import type { AdminOrderDetail } from '../../../shared/api/types'
import { canCheckInItem, slotLabel } from '../adminOrderDisplay'

const { Text } = Typography

type AdminOrderItemsTableProps = {
  detail: AdminOrderDetail
  isCheckingIn: boolean
  onCheckIn: (ticketCode: string) => void
  pendingTicketCode?: string
}

export function AdminOrderItemsTable({
  detail,
  isCheckingIn,
  onCheckIn,
  pendingTicketCode,
}: AdminOrderItemsTableProps) {
  return (
    <Table
      className="admin-order-items-table"
      columns={[
        { dataIndex: 'itemNo', title: '票项号' },
        {
          key: 'ticket',
          title: '票型',
          render: (_, item) => (
            <Space orientation="vertical" size={0}>
              <Text>{item.productName}</Text>
              <Text type="secondary">{item.ticketName}</Text>
            </Space>
          ),
        },
        {
          key: 'slot',
          title: '游览时段',
          render: (_, item) => slotLabel(item),
        },
        {
          dataIndex: 'itemStatus',
          title: '票项状态',
          render: (status: string) => <Tag>{status}</Tag>,
        },
        {
          dataIndex: 'ticketCode',
          title: '票码',
          render: (ticketCode?: string | null) => ticketCode ? <Text code>{ticketCode}</Text> : <Text type="secondary">未出票</Text>,
        },
        {
          key: 'checkIn',
          title: '核验',
          render: (_, item) => {
            const ticketCode = item.ticketCode ?? ''
            const canCheckIn = canCheckInItem(detail, item)

            return (
              <Popconfirm
                cancelText="取消"
                disabled={!canCheckIn || isCheckingIn}
                okText="确认核验"
                onConfirm={() => onCheckIn(ticketCode)}
                title="确认核验这张票？"
              >
                <Button
                  className="admin-check-in-action"
                  disabled={!canCheckIn || isCheckingIn}
                  icon={<CheckCircleOutlined />}
                  loading={isCheckingIn && pendingTicketCode === ticketCode}
                  size="small"
                >
                  核验
                </Button>
              </Popconfirm>
            )
          },
        },
      ]}
      dataSource={detail.items}
      pagination={false}
      rowKey="itemNo"
      scroll={{ x: 860 }}
      size="small"
    />
  )
}
