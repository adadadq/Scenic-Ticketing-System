import { Button, Empty, Flex, Input, Modal, Skeleton, Typography } from 'antd'
import { useEffect, useState } from 'react'
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
  canRefund: boolean
  cancelError: unknown
  isCancelError: boolean
  isCanceling: boolean
  isPaymentBlocked: boolean
  isPaying: boolean
  isRefundError: boolean
  isRefunding: boolean
  isRefreshingBlockedPayment: boolean
  onCancelOrder: () => void
  onPayOrder: () => void
  onRefundOrder: (reason?: string) => void
  onRefreshBlockedPayment: () => void
  paymentError: unknown
  paymentSucceeded: boolean
  refundError: unknown
  refundSucceeded: boolean
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
  const [isRefundModalOpen, setRefundModalOpen] = useState(false)
  const [refundReason, setRefundReason] = useState('')
  const {
    canCancel,
    canPay,
    canSubmitPayment,
    canRefund,
    cancelError,
    isCancelError,
    isCanceling,
    isPaymentBlocked,
    isPaying,
    isRefundError,
    isRefunding,
    isRefreshingBlockedPayment,
    onCancelOrder,
    onPayOrder,
    onRefundOrder,
    onRefreshBlockedPayment,
    paymentError,
    paymentSucceeded,
    refundError,
    refundSucceeded,
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

  useEffect(() => {
    if (refundSucceeded) {
      setRefundModalOpen(false)
      setRefundReason('')
    }
  }, [refundSucceeded])

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
          fallback="订单不存在，或你暂无权限查看。"
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

      {isRefundError ? (
        <OrderContractError
          error={refundError}
          fallback="订单状态或退款截止时间可能已变化，请刷新后重试。"
          title="退款失败"
        />
      ) : null}

      {canPay || canCancel || canRefund || isPaymentBlocked || isPaying || isCanceling || isRefunding ? (
        <OrderDetailActionBar
          canCancel={canCancel}
          canPay={canPay}
          canSubmitPayment={canSubmitPayment}
          canRefund={canRefund}
          isCanceling={isCanceling}
          isPaying={isPaying}
          isPaymentBlocked={isPaymentBlocked}
          isRefunding={isRefunding}
          onCancelOrder={onCancelOrder}
          onPayOrder={onPayOrder}
          onRefundOrder={() => setRefundModalOpen(true)}
        />
      ) : null}

      <Modal
        cancelText="暂不退款"
        centered
        confirmLoading={isRefunding}
        destroyOnHidden
        okButtonProps={{ danger: true }}
        okText="确认退款"
        onCancel={() => setRefundModalOpen(false)}
        onOk={() => onRefundOrder(refundReason.trim() || undefined)}
        open={isRefundModalOpen}
        title="确认申请整单退款？"
      >
        <Flex vertical gap={12}>
          {isRefundError ? (
            <OrderContractError
              error={refundError}
              fallback="订单状态或退款截止时间可能已变化，请关闭后刷新订单。"
              title="退款失败"
            />
          ) : null}
          <Text>退款后全部票码立即失效，已售库存会自动释放。</Text>
          {selectedDetail?.refundDeadline ? (
            <Text type="secondary">退款截止：{new Date(selectedDetail.refundDeadline).toLocaleString('zh-CN', { hour12: false })}</Text>
          ) : null}
          <Input.TextArea
            maxLength={100}
            onChange={(event) => setRefundReason(event.target.value)}
            placeholder="退款原因（选填）"
            rows={3}
            showCount
            value={refundReason}
          />
        </Flex>
      </Modal>
    </Flex>
  )
}
