import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminCheckInsApi, adminOrdersApi } from '../../shared/api/endpoints'
import type {
  AdminBatchCheckInRequest,
  AdminBatchUndoCheckInRequest,
  AdminCheckInRequest,
  AdminOrderListParams,
  AdminPartialRefundRequest,
  AdminRefundRequest,
} from '../../shared/api/types'
import {
  checkInMockAdminTicket,
  checkInMockAdminTickets,
  getMockAdminOrderDetail,
  listMockAdminOrders,
  listMockAdminRefundAuditLogs,
  partialRefundMockAdminOrder,
  refundMockAdminOrder,
  undoCheckInMockAdminTickets,
} from './mockData'

export type AdminOrdersMode = 'mock' | 'api'

export const adminOrdersMode: AdminOrdersMode = import.meta.env.VITE_ADMIN_ORDERS_MODE === 'api' ? 'api' : 'mock'

export const adminOrderQueryKeys = {
  detail: (orderNo: string, mode: AdminOrdersMode = adminOrdersMode) =>
    ['admin-orders', mode, 'detail', orderNo] as const,
  list: (params: AdminOrderListParams = {}, mode: AdminOrdersMode = adminOrdersMode) =>
    ['admin-orders', mode, 'list', normalizeAdminOrderListParams(params)] as const,
  refundLogs: (orderNo: string, mode: AdminOrdersMode = adminOrdersMode) =>
    ['admin-orders', mode, 'refund-logs', orderNo] as const,
}

export function normalizeAdminOrderListParams(params: AdminOrderListParams = {}): AdminOrderListParams {
  const orderNo = params.orderNo?.trim()
  const buyerPhone = params.buyerPhone?.trim()

  return {
    ...(params.status ? { status: params.status } : {}),
    ...(params.paymentStatus ? { paymentStatus: params.paymentStatus } : {}),
    ...(orderNo ? { orderNo } : {}),
    ...(buyerPhone ? { buyerPhone } : {}),
    ...(params.page !== undefined ? { page: params.page } : {}),
    ...(params.pageSize !== undefined ? { pageSize: params.pageSize } : {}),
  }
}

export function useAdminOrdersQuery(params: AdminOrderListParams = {}) {
  const normalizedParams = normalizeAdminOrderListParams(params)

  return useQuery({
    queryKey: adminOrderQueryKeys.list(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminOrdersMode === 'api') {
        return adminOrdersApi.list(normalizedParams)
      }

      return listMockAdminOrders(normalizedParams)
    },
  })
}

export function useAdminOrderDetailQuery(orderNo?: string) {
  const normalizedOrderNo = orderNo?.trim() ?? ''

  return useQuery({
    enabled: Boolean(normalizedOrderNo),
    queryKey: adminOrderQueryKeys.detail(normalizedOrderNo),
    retry: false,
    queryFn: async () => {
      if (!normalizedOrderNo) {
        return null
      }

      if (adminOrdersMode === 'api') {
        return adminOrdersApi.detail(normalizedOrderNo)
      }

      return getMockAdminOrderDetail(normalizedOrderNo)
    },
  })
}

export function useAdminRefundAuditLogsQuery(orderNo?: string) {
  const normalizedOrderNo = orderNo?.trim() ?? ''

  return useQuery({
    enabled: Boolean(normalizedOrderNo),
    queryKey: adminOrderQueryKeys.refundLogs(normalizedOrderNo),
    retry: false,
    queryFn: async () => {
      if (!normalizedOrderNo) {
        return []
      }

      if (adminOrdersMode === 'api') {
        return adminOrdersApi.refundLogs(normalizedOrderNo)
      }

      return listMockAdminRefundAuditLogs(normalizedOrderNo)
    },
  })
}

export function useAdminCheckInMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (body: AdminCheckInRequest) => {
      if (adminOrdersMode === 'api') {
        return adminCheckInsApi.create({ ticketCode: body.ticketCode.trim() })
      }

      return checkInMockAdminTicket(body.ticketCode)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['admin-orders', adminOrdersMode] })
      queryClient.invalidateQueries({ queryKey: adminOrderQueryKeys.detail(result.orderNo) })
    },
  })
}

export function useAdminBatchCheckInMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (body: AdminBatchCheckInRequest) => {
      const normalizedBody = {
        ticketCodes: body.ticketCodes.map((ticketCode) => ticketCode.trim()),
      }

      if (adminOrdersMode === 'api') {
        return adminCheckInsApi.batch(normalizedBody)
      }

      return checkInMockAdminTickets(normalizedBody)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['admin-orders', adminOrdersMode] })
      result.results.forEach((item) => {
        if (item.success && item.checkIn) {
          queryClient.invalidateQueries({ queryKey: adminOrderQueryKeys.detail(item.checkIn.orderNo) })
        }
      })
    },
  })
}

export function useAdminBatchUndoCheckInMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (body: AdminBatchUndoCheckInRequest) => {
      const normalizedBody = {
        ticketCodes: body.ticketCodes.map((ticketCode) => ticketCode.trim()),
        ...(body.reason?.trim() ? { reason: body.reason.trim() } : {}),
      }

      if (adminOrdersMode === 'api') {
        return adminCheckInsApi.batchUndo(normalizedBody)
      }

      return undoCheckInMockAdminTickets(normalizedBody)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['admin-orders', adminOrdersMode] })
      result.results.forEach((item) => {
        if (item.success && item.undoCheckIn) {
          queryClient.invalidateQueries({ queryKey: adminOrderQueryKeys.detail(item.undoCheckIn.orderNo) })
        }
      })
    },
  })
}

export function useAdminFullRefundMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ orderNo, reason }: AdminRefundRequest & { orderNo: string }) => {
      const normalizedOrderNo = orderNo.trim()
      const body = { reason: reason?.trim() || undefined }

      if (adminOrdersMode === 'api') {
        return adminOrdersApi.refund(normalizedOrderNo, body)
      }

      return refundMockAdminOrder(normalizedOrderNo, body)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['admin-orders', adminOrdersMode] })
      queryClient.invalidateQueries({ queryKey: adminOrderQueryKeys.detail(result.orderNo) })
      queryClient.invalidateQueries({ queryKey: adminOrderQueryKeys.refundLogs(result.orderNo) })
      queryClient.invalidateQueries({ queryKey: ['admin-refund-logs'] })
      queryClient.invalidateQueries({ queryKey: ['admin-reports'] })
    },
  })
}

export function useAdminPartialRefundMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ orderNo, itemNos, reason }: AdminPartialRefundRequest & { orderNo: string }) => {
      const normalizedOrderNo = orderNo.trim()
      const body = {
        itemNos: itemNos.map((itemNo) => itemNo.trim()),
        reason: reason?.trim() || undefined,
      }

      if (adminOrdersMode === 'api') {
        return adminOrdersApi.partialRefund(normalizedOrderNo, body)
      }

      return partialRefundMockAdminOrder(normalizedOrderNo, body)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['admin-orders', adminOrdersMode] })
      queryClient.invalidateQueries({ queryKey: adminOrderQueryKeys.detail(result.orderNo) })
      queryClient.invalidateQueries({ queryKey: adminOrderQueryKeys.refundLogs(result.orderNo) })
      queryClient.invalidateQueries({ queryKey: ['admin-refund-logs'] })
      queryClient.invalidateQueries({ queryKey: ['admin-reports'] })
    },
  })
}
