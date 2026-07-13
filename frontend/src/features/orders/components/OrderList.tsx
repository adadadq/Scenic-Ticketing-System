import { CalendarOutlined, ClockCircleOutlined, FieldTimeOutlined, ShoppingCartOutlined } from '@ant-design/icons'
import { Button, Empty, Table, Tag, Typography } from 'antd'
import type { TableProps } from 'antd'
import type { OrderListItem } from '../types'
import { formatCurrency, orderStatusColor } from '../utils'

const { Text } = Typography

const columns: TableProps<OrderListItem>['columns'] = [
  {
    title: '订单号',
    dataIndex: 'orderNo',
    render: (orderNo: string) => <Text copyable>{orderNo}</Text>,
    width: 210,
  },
  {
    title: '状态',
    dataIndex: 'orderStatusLabel',
    render: (label: string, row) => <Tag color={orderStatusColor(row.orderStatusTone)}>{label}</Tag>,
    width: 96,
  },
  {
    title: '游览日期',
    dataIndex: 'visitDate',
    render: (visitDate: string) => visitDate || '详情中查看',
    responsive: ['md'],
  },
  {
    title: '时段',
    dataIndex: 'timeSlotLabel',
    responsive: ['lg'],
  },
  {
    title: '张数',
    dataIndex: 'itemCount',
    align: 'right',
    width: 80,
  },
  {
    title: '应付',
    dataIndex: 'payableAmount',
    align: 'right',
    render: (amount: number) => <Text className="price">{formatCurrency(amount)}</Text>,
    width: 120,
  },
]

function formatMobileOrderTime(orderTime: string) {
  const parsed = new Date(orderTime)

  if (Number.isNaN(parsed.getTime())) {
    return orderTime || '详情中查看'
  }

  return parsed.toLocaleString('zh-CN', {
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    month: '2-digit',
  })
}

function getMobileOrderActionLabel(order: OrderListItem) {
  if (order.orderStatus === 'CREATED') {
    return '查看并处理'
  }

  if (order.orderStatus === 'PAID' || order.orderStatus === 'COMPLETED') {
    return '查看凭证'
  }

  return '查看详情'
}

function getMobileOrderToneClass(order: OrderListItem) {
  if (order.orderStatus === 'CREATED') {
    return 'is-pending'
  }

  if (order.orderStatus === 'PAID' || order.orderStatus === 'COMPLETED') {
    return 'is-paid'
  }

  if (order.orderStatus === 'CANCELLED') {
    return 'is-cancelled'
  }

  if (order.orderStatus === 'REFUNDED') {
    return 'is-refunded'
  }

  return 'is-readonly'
}

type OrderListProps = {
  filteredOrders: OrderListItem[]
  isLoading: boolean
  isSearchEmpty: boolean
  isStatusEmpty: boolean
  onClearFilters: () => void
  onOpenBooking?: () => void
  onSelectOrder: (orderNo: string, options?: { openMobileDetail?: boolean }) => void
  onShowAllStatuses: () => void
  selectedOrderNo?: string
}

export function OrderList({
  filteredOrders,
  isLoading,
  isSearchEmpty,
  isStatusEmpty,
  onClearFilters,
  onOpenBooking,
  onSelectOrder,
  onShowAllStatuses,
  selectedOrderNo,
}: OrderListProps) {
  function renderEmptyOrders() {
    if (isSearchEmpty) {
      return (
        <Empty description="未找到匹配订单" image={Empty.PRESENTED_IMAGE_SIMPLE}>
          <Button onClick={onClearFilters}>清空筛选</Button>
        </Empty>
      )
    }

    if (isStatusEmpty) {
      return (
        <Empty description="当前状态暂无订单" image={Empty.PRESENTED_IMAGE_SIMPLE}>
          <Button onClick={onShowAllStatuses}>查看全部</Button>
        </Empty>
      )
    }

    return (
      <Empty description="暂无订单" image={Empty.PRESENTED_IMAGE_SIMPLE}>
        <Button icon={<ShoppingCartOutlined />} onClick={onOpenBooking} type="primary">
          去购票
        </Button>
      </Empty>
    )
  }

  return (
    <>
      <Table
        className="orders-table"
        columns={columns}
        dataSource={filteredOrders}
        loading={isLoading}
        locale={{
          emptyText: renderEmptyOrders(),
        }}
        onRow={(record) => ({
          onClick: () => onSelectOrder(record.orderNo),
        })}
        pagination={{ pageSize: 6, showSizeChanger: false }}
        rowClassName={(record) => (record.orderNo === selectedOrderNo ? 'selected-order-row' : '')}
        rowKey="orderNo"
        scroll={{ x: 720 }}
      />

      <ul className="orders-mobile-list" aria-label="订单列表">
        {isLoading ? (
          <li className="orders-mobile-empty">
            <Text type="secondary">订单加载中...</Text>
          </li>
        ) : filteredOrders.length > 0 ? (
          filteredOrders.map((order) => (
            <li key={order.orderNo}>
              <button
                className={[
                  'order-mobile-card',
                  getMobileOrderToneClass(order),
                  order.orderNo === selectedOrderNo ? 'active' : '',
                ].filter(Boolean).join(' ')}
                data-order-status={order.orderStatus}
                onClick={() => onSelectOrder(order.orderNo, { openMobileDetail: true })}
                type="button"
              >
                <span className="order-mobile-card-header">
                  <Text className="order-mobile-card-no" strong>
                    订单号：{order.orderNo}
                  </Text>
                  <Tag color={orderStatusColor(order.orderStatusTone)}>{order.orderStatusLabel}</Tag>
                </span>
                <span className="order-mobile-card-main">
                  <span className="order-mobile-card-art" aria-hidden="true" />
                  <span className="order-mobile-card-copy">
                    <Text className="order-mobile-ticket" strong>
                      {order.ticketName}
                    </Text>
                    <Text className="order-mobile-product" type="secondary">
                      {order.productName}
                    </Text>
                    <span className="order-mobile-card-meta">
                      <span>
                        <CalendarOutlined /> {order.visitDate || '详情中查看'}
                      </span>
                      <span>
                        <ClockCircleOutlined /> {order.timeSlotLabel}
                      </span>
                    </span>
                  </span>
                </span>
                <span className="order-mobile-card-facts">
                  <span>数量：{order.itemCount} 张</span>
                  <span>
                    <FieldTimeOutlined /> 下单时间：{formatMobileOrderTime(order.orderTime)}
                  </span>
                </span>
                <span className="order-mobile-card-footer">
                  <Text type="secondary">{order.orderStatus === 'REFUNDED' ? '已退金额' : '应付金额'}</Text>
                  <Text className="price">{formatCurrency(order.payableAmount)}</Text>
                </span>
                <span className="order-mobile-card-action">{getMobileOrderActionLabel(order)}</span>
              </button>
            </li>
          ))
        ) : (
          <li className="orders-mobile-empty">
            {renderEmptyOrders()}
          </li>
        )}
      </ul>
    </>
  )
}
