import { useEffect, useMemo, useState } from 'react'
import type { OrderStatusFilter } from '../../shared/api/types'
import { useMyOrdersQuery, useOrderDetailQuery } from './queries'
import type { OrderListItem, OrderStatusFilterValue } from './types'

export const statusFilterOptions = [
  { label: '全部', value: 'ALL' },
  { label: '待支付', value: 'CREATED' },
  { label: '已支付', value: 'PAID' },
  { label: '已取消', value: 'CANCELLED' },
  { label: '已退款', value: 'REFUNDED' },
] satisfies Array<{ label: string; value: OrderStatusFilterValue }>

const emptyOrders: OrderListItem[] = []

export function useOrdersSelection(initialOrderNo?: string) {
  const [statusFilter, setStatusFilter] = useState<OrderStatusFilterValue>('ALL')
  const [keyword, setKeyword] = useState('')
  const [visitDateFilter, setVisitDateFilter] = useState('')
  const [selectedOrderNo, setSelectedOrderNo] = useState<string | undefined>(initialOrderNo)
  const [isMobileDetailOpen, setMobileDetailOpen] = useState(
    () => Boolean(initialOrderNo && window.matchMedia('(max-width: 768px)').matches),
  )
  const orderStatus: OrderStatusFilter | undefined = statusFilter === 'ALL' ? undefined : statusFilter
  const ordersQuery = useMyOrdersQuery(orderStatus)
  const orderDetailQuery = useOrderDetailQuery(selectedOrderNo)

  const orders = ordersQuery.data ?? emptyOrders
  const normalizedKeyword = keyword.trim()
  const filteredOrders = useMemo(
    () =>
      orders.filter((order) => {
        const matchesKeyword = normalizedKeyword ? order.orderNo.includes(normalizedKeyword) : true
        const matchesVisitDate = visitDateFilter ? order.visitDate === visitDateFilter : true
        return matchesKeyword && matchesVisitDate
      }),
    [normalizedKeyword, orders, visitDateFilter],
  )
  const hasOrders = orders.length > 0
  const isStatusEmpty = !ordersQuery.isLoading && orderStatus !== undefined && orders.length === 0
  const isSearchEmpty = hasOrders && filteredOrders.length === 0

  useEffect(() => {
    if (!selectedOrderNo && filteredOrders[0]) {
      setSelectedOrderNo(filteredOrders[0].orderNo)
      return
    }

    if (selectedOrderNo && !filteredOrders.some((order) => order.orderNo === selectedOrderNo)) {
      if (selectedOrderNo === initialOrderNo) {
        return
      }

      setSelectedOrderNo(filteredOrders[0]?.orderNo)
    }
  }, [filteredOrders, initialOrderNo, selectedOrderNo])

  const selectedListOrder = filteredOrders.find((order) => order.orderNo === selectedOrderNo)
  const selectedDetail = orderDetailQuery.data
  const selectedOrder = selectedDetail ?? selectedListOrder
  const ticketCodes = selectedDetail?.ticketCodes ?? []
  const isDetailInitialLoading = Boolean(selectedOrder && orderDetailQuery.isLoading && !selectedDetail)
  const isDetailUnavailable = Boolean(selectedOrder && orderDetailQuery.isError && !selectedDetail)

  useEffect(() => {
    if (
      initialOrderNo &&
      selectedOrder?.orderNo === initialOrderNo &&
      window.matchMedia('(max-width: 768px)').matches
    ) {
      setMobileDetailOpen(true)
      return
    }

    if (!selectedOrder && !initialOrderNo) {
      setMobileDetailOpen(false)
    }
  }, [initialOrderNo, selectedOrder])

  useEffect(() => {
    const desktopQuery = window.matchMedia('(min-width: 769px)')
    const closeMobileDetailOnDesktop = () => {
      if (desktopQuery.matches) {
        setMobileDetailOpen(false)
      }
    }

    closeMobileDetailOnDesktop()
    desktopQuery.addEventListener('change', closeMobileDetailOnDesktop)

    return () => desktopQuery.removeEventListener('change', closeMobileDetailOnDesktop)
  }, [])

  function clearOrderFilters() {
    setKeyword('')
    setVisitDateFilter('')
  }

  function selectOrder(orderNo: string, options?: { openMobileDetail?: boolean }) {
    setSelectedOrderNo(orderNo)

    if (options?.openMobileDetail) {
      setMobileDetailOpen(true)
    }
  }

  return {
    clearOrderFilters,
    filteredOrders,
    isDetailInitialLoading,
    isDetailUnavailable,
    isMobileDetailOpen,
    isSearchEmpty,
    isStatusEmpty,
    keyword,
    orderDetailQuery,
    orderCount: orders.length,
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
  }
}
