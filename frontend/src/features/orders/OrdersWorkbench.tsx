import {
  Col,
  Row,
} from 'antd'
import {
  CheckCircleOutlined,
  CustomerServiceOutlined,
  SafetyCertificateOutlined,
  SyncOutlined,
} from '@ant-design/icons'
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
  onOpenService?: () => void
}

const serviceItems = [
  { icon: <CheckCircleOutlined />, title: '官方票务', text: '正品保障 · 放心出行' },
  { icon: <SyncOutlined />, title: '灵活改签', text: '支持改期 · 灵活便捷' },
  { icon: <SafetyCertificateOutlined />, title: '安全支付', text: '多种方式 · 安全可靠' },
  { icon: <CustomerServiceOutlined />, title: '优质服务', text: '7×12小时 · 贴心服务' },
]

export function OrdersWorkbench({ onOpenAuth, onOpenBooking, onOpenService }: OrdersWorkbenchProps) {
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
    <section className="orders-page">
      <OrdersHeader onOpenService={onOpenService} />

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
            onRefreshOrders={() => ordersQuery.refetch()}
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
            isRefreshing={ordersQuery.isFetching}
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

      <section className="orders-service-strip" aria-label="订单服务保障">
        {serviceItems.map((item) => (
          <div className="orders-service-item" key={item.title}>
            <span>{item.icon}</span>
            <div>
              <strong>{item.title}</strong>
              <small>{item.text}</small>
            </div>
          </div>
        ))}
      </section>
    </section>
  )
}
