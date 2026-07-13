import { useEffect, useRef } from 'react'
import { ApiError, createIdempotencyKey } from '../../shared/api/client'
import { useCancelOrderMutation, usePayOrderMutation, useRefundOrderMutation } from './queries'
import type { OrderDetail, OrderListItem } from './types'

type RefreshableOrderDetailQuery = {
  isFetching: boolean
  refetch: () => Promise<{ data?: OrderDetail | null }>
}

type RefreshableOrdersQuery = {
  isFetching: boolean
  refetch: () => Promise<unknown>
}

type OrderActionsParams = {
  orderDetailQuery: RefreshableOrderDetailQuery
  ordersQuery: RefreshableOrdersQuery
  selectedDetail?: OrderDetail | null
  selectedOrder?: OrderListItem
  ticketCodes: string[]
}

function isBlockingPaymentError(error: unknown) {
  return error instanceof ApiError && (
    error.code === 'ORDER_NOT_PAYABLE' ||
    error.code === 'TIME_SLOT_QUOTA_NOT_ENOUGH'
  )
}

export function useOrderActions({
  orderDetailQuery,
  ordersQuery,
  selectedDetail,
  selectedOrder,
  ticketCodes,
}: OrderActionsParams) {
  const paymentKeys = useRef(new Map<string, string>())
  const payOrderMutation = usePayOrderMutation()
  const cancelOrderMutation = useCancelOrderMutation()
  const refundOrderMutation = useRefundOrderMutation()
  const canPay = selectedDetail?.orderStatus === 'CREATED' && selectedDetail.paymentStatus === 'UNPAID'
  const canCancel = canPay
  const canRefund = selectedDetail?.canSelfRefund === true
  const paymentSucceeded = selectedOrder?.paymentStatus === 'PAID' && ticketCodes.length > 0
  const paymentErrorMatchesSelectedOrder = Boolean(
    selectedOrder && payOrderMutation.variables?.orderNo === selectedOrder.orderNo,
  )
  const isPaymentBlocked = paymentErrorMatchesSelectedOrder && isBlockingPaymentError(payOrderMutation.error)
  const shouldShowPaymentError = payOrderMutation.isError && paymentErrorMatchesSelectedOrder
  const isRefreshingBlockedPayment = isPaymentBlocked && (orderDetailQuery.isFetching || ordersQuery.isFetching)
  const canSubmitPayment = canPay && !isPaymentBlocked && !isRefreshingBlockedPayment

  useEffect(() => {
    if (
      cancelOrderMutation.isSuccess &&
      paymentErrorMatchesSelectedOrder &&
      cancelOrderMutation.variables === selectedOrder?.orderNo
    ) {
      payOrderMutation.reset()
    }
  }, [
    cancelOrderMutation.isSuccess,
    cancelOrderMutation.variables,
    payOrderMutation,
    paymentErrorMatchesSelectedOrder,
    selectedOrder?.orderNo,
  ])

  function paySelectedOrder() {
    if (!selectedOrder || !canSubmitPayment) {
      return
    }

    const idempotencyKey = paymentKeys.current.get(selectedOrder.orderNo) ?? createIdempotencyKey('pay')
    paymentKeys.current.set(selectedOrder.orderNo, idempotencyKey)
    payOrderMutation.mutate({ idempotencyKey, orderNo: selectedOrder.orderNo })
  }

  function cancelSelectedOrder() {
    if (!selectedOrder || !canCancel) {
      return
    }

    cancelOrderMutation.mutate(selectedOrder.orderNo)
  }

  function refundSelectedOrder(reason?: string) {
    if (!selectedOrder || !canRefund) {
      return
    }
    refundOrderMutation.mutate({ orderNo: selectedOrder.orderNo, reason })
  }

  async function refreshSelectedOrder() {
    if (!selectedOrder) {
      return
    }

    const refreshedOrderNo = selectedOrder.orderNo
    const [detailResult] = await Promise.all([
      orderDetailQuery.refetch(),
      ordersQuery.refetch(),
    ])
    const refreshedOrder = detailResult.data

    if (
      refreshedOrder?.orderNo === refreshedOrderNo &&
      (refreshedOrder.orderStatus !== 'CREATED' || refreshedOrder.paymentStatus !== 'UNPAID')
    ) {
      payOrderMutation.reset()
    }
  }

  return {
    canCancel,
    canPay,
    canRefund,
    canSubmitPayment,
    cancelError: cancelOrderMutation.error,
    isCancelError: cancelOrderMutation.isError,
    isCanceling: cancelOrderMutation.isPending,
    isPaymentBlocked,
    isPaying: payOrderMutation.isPending,
    isRefundError: refundOrderMutation.isError,
    isRefunding: refundOrderMutation.isPending,
    isRefreshingBlockedPayment,
    onCancelOrder: cancelSelectedOrder,
    onPayOrder: paySelectedOrder,
    onRefundOrder: refundSelectedOrder,
    onRefreshBlockedPayment: refreshSelectedOrder,
    paymentError: payOrderMutation.error,
    paymentSucceeded,
    refundError: refundOrderMutation.error,
    refundSucceeded: refundOrderMutation.isSuccess,
    shouldShowPaymentError,
  }
}
