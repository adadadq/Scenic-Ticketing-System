import { Button, Empty, Flex, Skeleton, Typography } from 'antd'
import type { OrderDetail, OrderListItem } from '../types'
import {
  OrderDetailActionBar,
  OrderDetailFacts,
  OrderDetailHeader,
  OrderDetailStateCard,
  OrderPaymentSummary,
  OrderTicketCodeSection,
} from './OrderDetailSections'
import { OrderContractError } from './OrderContractError'

const { Text } = Typography

type OrderDetailPanelActions = {
  canCancel: boolean
  canPay: boolean
  canSubmitPayment: boolean
  cancelError: unknown
  isCancelError: boolean
  isCanceling: boolean
  isPaymentBlocked: boolean
  isPaying: boolean
  isRefreshingBlockedPayment: boolean
  onCancelOrder: () => void
  onPayOrder: () => void
  onRefreshBlockedPayment: () => void
  paymentError: unknown
  paymentSucceeded: boolean
  shouldShowPaymentError: boolean
}

type OrderDetailPanelState = {
  detailError: unknown
  isDetailInitialLoading: boolean
  isDetailUnavailable: boolean
  onRetryDetail: () => void
  selectedDetail?: OrderDetail | null
  selectedOrder?: OrderListItem
  ticketCodes: string[]
}

type OrderDetailPanelProps = {
  actions: OrderDetailPanelActions
  detailState: OrderDetailPanelState
}

export function OrderDetailPanel({ actions, detailState }: OrderDetailPanelProps) {
  const {
    canCancel,
    canPay,
    canSubmitPayment,
    cancelError,
    isCancelError,
    isCanceling,
    isPaymentBlocked,
    isPaying,
    isRefreshingBlockedPayment,
    onCancelOrder,
    onPayOrder,
    onRefreshBlockedPayment,
    paymentError,
    paymentSucceeded,
    shouldShowPaymentError,
  } = actions
  const {
    detailError,
    isDetailInitialLoading,
    isDetailUnavailable,
    onRetryDetail,
    selectedDetail,
    selectedOrder,
    ticketCodes,
  } = detailState

  if (!selectedOrder) {
    return <Empty description="选择一笔订单查看详情" image={Empty.PRESENTED_IMAGE_SIMPLE} />
  }

  const detailHeader = <OrderDetailHeader order={selectedOrder} />

  if (isDetailInitialLoading) {
    return (
      <Flex vertical gap={16}>
        {detailHeader}
        <div className="order-detail-loading" aria-live="polite">
          <Skeleton active paragraph={{ rows: 5 }} title={false} />
          <Text type="secondary">订单详情加载中...</Text>
        </div>
      </Flex>
    )
  }

  if (isDetailUnavailable) {
    return (
      <Flex vertical gap={16}>
        {detailHeader}
        <OrderContractError
          action={(
            <Button onClick={onRetryDetail} size="small">
              重试加载
            </Button>
          )}
          error={detailError}
          fallback="订单不存在或当前会话无权查看。"
          title="详情加载失败"
        />
      </Flex>
    )
  }

  return (
    <Flex vertical gap={16}>
      {detailHeader}

      <OrderDetailStateCard
        canCancel={canCancel}
        canPay={canPay}
        isPaymentBlocked={isPaymentBlocked}
        order={selectedOrder}
        paymentSucceeded={paymentSucceeded}
        ticketCodes={ticketCodes}
      />
      <OrderDetailFacts detail={selectedDetail} order={selectedOrder} />
      <OrderPaymentSummary canPay={canPay} order={selectedOrder} />
      <OrderTicketCodeSection
        canPay={canPay}
        order={selectedOrder}
        paymentSucceeded={paymentSucceeded}
        ticketCodes={ticketCodes}
      />

      {shouldShowPaymentError ? (
        <OrderContractError
          action={isPaymentBlocked ? (
            <Button loading={isRefreshingBlockedPayment} onClick={onRefreshBlockedPayment} size="small">
              刷新订单
            </Button>
          ) : undefined}
          error={paymentError}
          fallback={isPaymentBlocked ? '订单状态已变化，请刷新订单。' : '请检查库存、订单状态或稍后重试。'}
          title="支付失败"
        />
      ) : null}

      {isCancelError ? (
        <OrderContractError
          error={cancelError}
          fallback="订单状态可能已变化，请刷新后重试。"
          title="取消失败"
        />
      ) : null}

      {canPay || canCancel || isPaymentBlocked || isPaying || isCanceling ? (
        <OrderDetailActionBar
          canCancel={canCancel}
          canPay={canPay}
          canSubmitPayment={canSubmitPayment}
          isCanceling={isCanceling}
          isPaying={isPaying}
          isPaymentBlocked={isPaymentBlocked}
          onCancelOrder={onCancelOrder}
          onPayOrder={onPayOrder}
        />
      ) : null}
    </Flex>
  )
}
