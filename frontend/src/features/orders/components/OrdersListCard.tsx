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
  const errorTitle = isAuthRequired ? '请先登录后查看订单' : '订单加载失败'
  const errorFallback = isAuthRequired
    ? '请先登录账号后再查看订单。'
    : '订单列表暂时无法读取，请稍后重试。'
  const errorSupportingText = isAuthRequired
    ? '登录后只会看到你自己的订单。'
    : '如多次失败，请联系客服并提供页面上的问题编号。'
  const hasSearchFilters = Boolean(keyword.trim() || visitDateFilter)

  return (
    <Card className="workspace-card orders-card orders-list-card">
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

      {isError ? (
        <OrderContractError
          action={(
            <Space className="orders-error-actions" wrap>
              {isAuthRequired ? (
                <Button onClick={onOpenAuth} size="small" type="primary">
                  去登录
                </Button>
              ) : null}
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
          showMeta={!isAuthRequired}
          supportingText={errorSupportingText}
          title={errorTitle}
          type={isAuthRequired ? 'warning' : 'error'}
        />
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
