import {
  Col,
  Row,
} from 'antd'
import { ApiError } from '../../shared/api/client'
import { OrderDetailPanel } from './components/OrderDetailPanel'
import { DesktopOrderDetailCard, MobileOrderDetailDrawer } from './components/OrderDetailSurfaces'
import { OrdersHeader } from './components/OrdersHeader'
import { OrdersListCard } from './components/OrdersListCard'
import { useOrderActions } from './useOrderActions'
import { statusFilterOptions, useOrdersSelection } from './useOrdersSelection'

type OrdersWorkbenchProps = {
  onOpenAuth?: () => void
  onOpenBooking?: () => void
}

export function OrdersWorkbench({ onOpenAuth, onOpenBooking }: OrdersWorkbenchProps) {
  const ordersSelection = useOrdersSelection()
  const {
    clearOrderFilters,
    filteredOrders,
    isDetailInitialLoading,
    isDetailUnavailable,
    isMobileDetailOpen,
    isSearchEmpty,
    isStatusEmpty,
    keyword,
    orderDetailQuery,
    orderCount,
    ordersQuery,
    selectOrder,
    selectedDetail,
    selectedOrder,
    selectedOrderNo,
    setKeyword,
    setMobileDetailOpen,
    setStatusFilter,
    setVisitDateFilter,
    statusFilter,
    ticketCodes,
    visitDateFilter,
  } = ordersSelection
  const isOrdersAuthRequired = ordersQuery.error instanceof ApiError && ordersQuery.error.code === 'AUTH_REQUIRED'
  const orderActions = useOrderActions({
    orderDetailQuery,
    ordersQuery,
    selectedDetail,
    selectedOrder,
    ticketCodes,
  })

  const orderDetail = (
    <OrderDetailPanel
      actions={orderActions}
      detailState={{
        detailError: orderDetailQuery.error,
        isDetailInitialLoading,
        isDetailUnavailable,
        onRetryDetail: () => orderDetailQuery.refetch(),
        selectedDetail,
        selectedOrder,
        ticketCodes,
      }}
    />
  )

  return (
    <>
      <OrdersHeader isRefreshing={ordersQuery.isFetching} onRefresh={() => ordersQuery.refetch()} />

      <Row className="orders-workbench-grid" gutter={[16, 16]} align="stretch">
        <Col xs={24} xl={16}>
          <OrdersListCard
            filteredOrders={filteredOrders}
            isAuthRequired={isOrdersAuthRequired}
            isError={ordersQuery.isError}
            isLoading={ordersQuery.isLoading}
            isSearchEmpty={isSearchEmpty}
            isStatusEmpty={isStatusEmpty}
            keyword={keyword}
            onClearFilters={clearOrderFilters}
            onKeywordChange={setKeyword}
            onOpenAuth={onOpenAuth}
            onOpenBooking={onOpenBooking}
            onRetryOrders={() => ordersQuery.refetch()}
            onSelectOrder={selectOrder}
            onShowAllStatuses={() => setStatusFilter('ALL')}
            onStatusFilterChange={setStatusFilter}
            onVisitDateFilterChange={setVisitDateFilter}
            ordersError={ordersQuery.error}
            selectedOrderNo={selectedOrderNo}
            statusFilter={statusFilter}
            statusFilterOptions={statusFilterOptions}
            totalOrderCount={orderCount}
            visitDateFilter={visitDateFilter}
          />
        </Col>

        <DesktopOrderDetailCard>
          {orderDetail}
        </DesktopOrderDetailCard>
      </Row>

      <MobileOrderDetailDrawer
        isOpen={isMobileDetailOpen}
        onClose={() => setMobileDetailOpen(false)}
        selectedOrder={selectedOrder}
      >
        {orderDetail}
      </MobileOrderDetailDrawer>
    </>
  )
}
