import { CheckCircleOutlined, ClockCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { Flex, Tag, Typography } from 'antd'
import type { ReactNode } from 'react'
import type { OrderStatusFilterValue } from '../types'

const { Text } = Typography

type OrderWorkflowItem = {
  detail: string
  icon: ReactNode
  key: Exclude<OrderStatusFilterValue, 'ALL'>
  label: string
  tag: string
  tone: string
}

const orderWorkflowItems: OrderWorkflowItem[] = [
  {
    detail: '继续支付，或在未支付前取消订单。',
    icon: <ClockCircleOutlined />,
    key: 'CREATED',
    label: '待支付',
    tag: '可操作',
    tone: 'processing',
  },
  {
    detail: '查看入园票码，已支付订单不再显示取消入口。',
    icon: <CheckCircleOutlined />,
    key: 'PAID',
    label: '已支付',
    tag: '看票码',
    tone: 'success',
  },
  {
    detail: '查看取消记录，已取消订单不会生成票码。',
    icon: <CloseCircleOutlined />,
    key: 'CANCELLED',
    label: '已取消',
    tag: '只读',
    tone: 'default',
  },
]

type OrderWorkflowStripProps = {
  hasSearchFilters: boolean
  isLoading: boolean
  statusFilter: OrderStatusFilterValue
  visibleOrderCount: number
}

export function OrderWorkflowStrip({
  hasSearchFilters,
  isLoading,
  statusFilter,
  visibleOrderCount,
}: OrderWorkflowStripProps) {
  const activeStatusLabel =
    orderWorkflowItems.find((item) => item.key === statusFilter)?.label ?? '全部状态'

  return (
    <section className="orders-workflow-strip" aria-label="订单状态" data-active-status={statusFilter}>
      <Flex className="orders-workflow-heading" align="center" justify="space-between" gap={8} wrap>
        <div>
          <Text className="orders-workflow-title">订单状态</Text>
          <Text className="orders-workflow-subtitle" type="secondary">
            当前筛选：{activeStatusLabel}
          </Text>
        </div>
        <Tag color={isLoading ? 'default' : 'cyan'}>
          {isLoading ? '加载中' : `当前视图 ${visibleOrderCount} 笔`}
        </Tag>
      </Flex>

      <div className="orders-workflow-items">
        {orderWorkflowItems.map((item) => {
          const isActive = statusFilter === item.key

          return (
            <div className={isActive ? 'orders-workflow-item is-active' : 'orders-workflow-item'} key={item.key}>
              <span className="orders-workflow-icon" aria-hidden="true">
                {item.icon}
              </span>
              <div className="orders-workflow-copy">
                <Flex align="center" justify="space-between" gap={8}>
                  <Text strong>{item.label}</Text>
                  <Tag color={isActive ? item.tone : 'default'}>{item.tag}</Tag>
                </Flex>
                <Text type="secondary">{item.detail}</Text>
              </div>
            </div>
          )
        })}
      </div>

      <Text className="orders-workflow-note" type="secondary">
        {hasSearchFilters
          ? '筛选只改变当前列表，不会影响订单。'
          : '先从列表选择订单，再在详情中完成支付、取消或查看票码。'}
      </Text>
    </section>
  )
}
