import { LockOutlined } from '@ant-design/icons'
import { Button, Card, Space } from 'antd'
import type { OrderListItem, OrderStatusFilterValue } from '../types'
import { OrderContractError } from './OrderContractError'
import { OrderList } from './OrderList'
import { OrderStatusFilters } from './OrderStatusFilters'
import { OrderWorkflowStrip } from './OrderWorkflowStrip'

type OrdersListCardProps = {
  filteredOrders: OrderListItem[]
  isAuthRequired: boolean
  isError: boolean
  isLoading: boolean
  isSearchEmpty: boolean
  isStatusEmpty: boolean
  keyword: string
  onClearFilters: () => void
  onKeywordChange: (keyword: string) => void
  onOpenAuth?: () => void
  onOpenBooking?: () => void
  onRefreshOrders: () => void
  onRetryOrders: () => void
  onSelectOrder: (orderNo: string, options?: { openMobileDetail?: boolean }) => void
  onShowAllStatuses: () => void
  onStatusFilterChange: (status: OrderStatusFilterValue) => void
  onVisitDateFilterChange: (visitDate: string) => void
  ordersError: unknown
  selectedOrderNo?: string
  statusFilter: OrderStatusFilterValue
  statusFilterOptions: Array<{ label: string; value: OrderStatusFilterValue }>
  totalOrderCount: number
  visitDateFilter: string
  isRefreshing: boolean
}

export function OrdersListCard({
  filteredOrders,
  isAuthRequired,
  isError,
  isLoading,
  isSearchEmpty,
  isStatusEmpty,
  keyword,
  onClearFilters,
  onKeywordChange,
  onOpenAuth,
  onOpenBooking,
  onRefreshOrders,
  onRetryOrders,
  onSelectOrder,
  onShowAllStatuses,
  onStatusFilterChange,
  onVisitDateFilterChange,
  ordersError,
  selectedOrderNo,
  statusFilter,
  statusFilterOptions,
  totalOrderCount,
  visitDateFilter,
  isRefreshing,
}: OrdersListCardProps) {
  const errorTitle = '订单加载失败'
  const errorFallback = '订单列表暂时无法读取，请稍后重试。'
  const errorSupportingText = '如多次失败，请联系客服并提供页面上的问题编号。'
  const hasSearchFilters = Boolean(keyword.trim() || visitDateFilter)

  return (
    <Card className="workspace-card orders-card orders-list-card">
      {!isAuthRequired ? (
        <>
          <OrderStatusFilters
            filteredOrderCount={filteredOrders.length}
            isLoading={isLoading}
            keyword={keyword}
            onClearFilters={onClearFilters}
            onKeywordChange={onKeywordChange}
            onRefreshOrders={onRefreshOrders}
            onStatusFilterChange={onStatusFilterChange}
            onVisitDateFilterChange={onVisitDateFilterChange}
            statusFilter={statusFilter}
            statusFilterOptions={statusFilterOptions}
            totalOrderCount={totalOrderCount}
            visitDateFilter={visitDateFilter}
            isRefreshing={isRefreshing}
          />

          <OrderWorkflowStrip
            hasSearchFilters={hasSearchFilters}
            isLoading={isLoading}
            statusFilter={statusFilter}
            visibleOrderCount={filteredOrders.length}
          />
        </>
      ) : null}

      {isError ? (
        isAuthRequired ? (
          <section className="orders-login-state" role="alert">
            <span className="orders-login-state-icon" aria-hidden="true">
              <LockOutlined />
            </span>
            <div className="orders-login-state-copy">
              <h2>登录后查看订单</h2>
              <p>订单、支付状态和入园票码仅对当前账号可见。</p>
            </div>
            <Button
              className="orders-login-state-primary"
              onClick={onOpenAuth}
              size="large"
              type="primary"
            >
              立即登录
            </Button>
            <div className="orders-login-state-secondary">
              <Button onClick={onRetryOrders}>重新检查</Button>
              <Button onClick={onOpenBooking}>返回购票</Button>
            </div>
          </section>
        ) : (
          <OrderContractError
            action={(
              <Space className="orders-error-actions" wrap>
                <Button onClick={onRetryOrders} size="small">
                  重试
                </Button>
                <Button onClick={onOpenBooking} size="small">
                  返回购票
                </Button>
              </Space>
            )}
            error={ordersError}
            fallback={errorFallback}
            showMeta
            supportingText={errorSupportingText}
            title={errorTitle}
          />
        )
      ) : (
        <OrderList
          filteredOrders={filteredOrders}
          isLoading={isLoading}
          isSearchEmpty={isSearchEmpty}
          isStatusEmpty={isStatusEmpty}
          onClearFilters={onClearFilters}
          onOpenBooking={onOpenBooking}
          onSelectOrder={onSelectOrder}
          onShowAllStatuses={onShowAllStatuses}
          selectedOrderNo={selectedOrderNo}
        />
      )}
    </Card>
  )
}
