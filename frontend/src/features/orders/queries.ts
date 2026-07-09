import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ordersApi } from '../../shared/api/endpoints'
import type { OrderCreateRequest, OrderStatusFilter } from '../../shared/api/types'
import { mapOrderDetail, mapOrderSummary } from './adapters'

export const orderQueryKeys = {
  mine: (status?: OrderStatusFilter) => ['orders', 'mine', status ?? 'ALL'] as const,
  detail: (orderNo: string) => ['orders', 'detail', orderNo] as const,
}

export type PayOrderVariables = {
  idempotencyKey: string
  orderNo: string
}

export function useCreateOrderMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (body: OrderCreateRequest) => mapOrderDetail(await ordersApi.create(body)),
    onSuccess: (order) => {
      queryClient.setQueryData(orderQueryKeys.detail(order.orderNo), order)
      queryClient.invalidateQueries({ queryKey: ['orders', 'mine'] })
    },
  })
}

export function useMyOrdersQuery(status?: OrderStatusFilter) {
  return useQuery({
    queryKey: orderQueryKeys.mine(status),
    retry: false,
    queryFn: async () => {
      const orders = await ordersApi.mine(status)
      return orders.map(mapOrderSummary)
    },
  })
}

export function useOrderDetailQuery(orderNo?: string) {
  return useQuery({
    enabled: Boolean(orderNo),
    queryKey: orderQueryKeys.detail(orderNo ?? ''),
    retry: false,
    queryFn: async () => {
      if (!orderNo) {
        return null
      }

      return mapOrderDetail(await ordersApi.detail(orderNo))
    },
  })
}

export function usePayOrderMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (variables: PayOrderVariables) =>
      mapOrderDetail(await ordersApi.pay(variables.orderNo, variables.idempotencyKey)),
    onSuccess: (order) => {
      queryClient.setQueryData(orderQueryKeys.detail(order.orderNo), order)
      queryClient.invalidateQueries({ queryKey: ['orders', 'mine'] })
    },
  })
}

export function useCancelOrderMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (orderNo: string) => mapOrderDetail(await ordersApi.cancel(orderNo)),
    onSuccess: (order) => {
      queryClient.setQueryData(orderQueryKeys.detail(order.orderNo), order)
      queryClient.invalidateQueries({ queryKey: ['orders', 'mine'] })
    },
  })
}
