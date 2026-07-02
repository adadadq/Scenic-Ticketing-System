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
}: OrdersListCardProps) {
  const errorTitle = isAuthRequired ? '请先登录后查看订单' : '订单加载失败'
  const errorFallback = isAuthRequired
    ? '当前会话未登录，请先使用手机号登录后再查看订单。'
    : '订单列表暂时无法读取，请稍后重试。'
  const errorSupportingText = isAuthRequired
    ? '订单只展示当前游客会话下的数据，登录后不会泄露其他游客订单。'
    : '如持续失败，请保留错误码和请求编号，便于后端或客服定位问题。'
  const hasSearchFilters = Boolean(keyword.trim() || visitDateFilter)

  return (
    <Card className="workspace-card orders-card orders-list-card">
      <OrderStatusFilters
        filteredOrderCount={filteredOrders.length}
        isLoading={isLoading}
        keyword={keyword}
        onClearFilters={onClearFilters}
        onKeywordChange={onKeywordChange}
        onStatusFilterChange={onStatusFilterChange}
        onVisitDateFilterChange={onVisitDateFilterChange}
        statusFilter={statusFilter}
        statusFilterOptions={statusFilterOptions}
        totalOrderCount={totalOrderCount}
        visitDateFilter={visitDateFilter}
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
