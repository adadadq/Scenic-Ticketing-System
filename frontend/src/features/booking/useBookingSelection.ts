import { useEffect, useMemo, useState } from 'react'
import { ticketProducts as mockTicketProducts, timeSlots as mockTimeSlots } from './mockData'
import { useTicketProductsQuery, useTimeSlotsQuery } from './queries'
import type { BookingTicketSelection } from './bookingFlow'
import type { TimeSlotOption } from './types'
import { slotKey } from './utils'

function formatLocalDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatMonthDay(date: Date) {
  const month = date.getMonth() + 1
  const day = date.getDate()
  return `${month}月${day}日`
}

function addDays(date: Date, days: number) {
  const nextDate = new Date(date)
  nextDate.setDate(nextDate.getDate() + days)
  return nextDate
}

export function getVisitDateOptions(today = new Date()) {
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return Array.from({ length: 7 }, (_, index) => {
    const date = addDays(today, index)
    return {
      label: `${formatMonthDay(date)}\n${weekdays[date.getDay()]}`,
      value: formatLocalDate(date),
    }
  })
}

export const visitDateOptions = getVisitDateOptions()
const emptyTimeSlots: TimeSlotOption[] = []

function getSharedTimeSlots(timeSlots: TimeSlotOption[], selectedTicketSelections: BookingTicketSelection[]) {
  if (selectedTicketSelections.length === 0) {
    return []
  }

  if (selectedTicketSelections.some(({ product }) => !product.productId && !product.ticketTypeId)) {
    return timeSlots
  }

  const groups = new Map<string, TimeSlotOption[]>()

  timeSlots.forEach((slot) => {
    const key = `${slot.visitDate ?? ''}-${slot.label}`
    const group = groups.get(key) ?? []
    group.push(slot)
    groups.set(key, group)
  })

  return Array.from(groups.values()).flatMap((slots) => {
    const matches = selectedTicketSelections.map(({ product }) => {
      return slots.find((slot) => (
        product.productId ? slot.productId === product.productId : slot.ticketTypeId === product.ticketTypeId
      ))
    })

    if (matches.some((slot) => !slot?.id)) {
      return []
    }

    const remainingQuotas = matches
      .map((slot) => slot?.remainingQuota)
      .filter((quota): quota is number => typeof quota === 'number')
    const remainingQuota = remainingQuotas.length > 0 ? Math.min(...remainingQuotas) : undefined
    const hasSoldOut = matches.some((slot) => slot?.tone === 'sold-out')
    const hasLimited = matches.some((slot) => slot?.tone === 'limited')
    const firstSlot = matches[0]!

    return [{
      ...firstSlot,
      itemTimeSlotIds: Object.fromEntries(
        selectedTicketSelections.map(({ product }, index) => [product.key, matches[index]!.id!]),
      ),
      remainingQuota,
      status: typeof remainingQuota === 'number' ? `余票 ${remainingQuota}` : firstSlot.status,
      tone: hasSoldOut ? 'sold-out' as const : hasLimited ? 'limited' as const : 'available' as const,
    }]
  })
}

export function useBookingSelection() {
  const [selectedProductQuantities, setSelectedProductQuantities] = useState<Record<string, number>>({})
  const [hasInitializedProducts, setHasInitializedProducts] = useState(false)
  const [selectedVisitDate, setSelectedVisitDate] = useState(visitDateOptions[0].value)
  const [selectedSlotKey, setSelectedSlotKey] = useState<string>()
  const productsQuery = useTicketProductsQuery()
  const usesProductFallback = productsQuery.isError
  const ticketProducts = productsQuery.isSuccess ? productsQuery.data : usesProductFallback ? mockTicketProducts : []
  const firstAvailableProduct = ticketProducts.find((product) => !product.disabled)
  const selectedTicketSelections = ticketProducts
    .filter((product) => !product.disabled && selectedProductQuantities[product.key] > 0)
    .map((product) => ({ product, quantity: selectedProductQuantities[product.key] }))
  const selectedProduct = selectedTicketSelections[0]?.product
  const timeSlotsQuery = useTimeSlotsQuery({
    enabled: Boolean(productsQuery.isSuccess && selectedTicketSelections.length > 0),
    visitDate: selectedVisitDate,
  })
  const usesTimeSlotFallback = Boolean(!usesProductFallback && productsQuery.isSuccess && selectedProduct && timeSlotsQuery.isError)
  const usesDemoTimeSlots = usesProductFallback || usesTimeSlotFallback
  const queryTimeSlots = timeSlotsQuery.isSuccess ? timeSlotsQuery.data : emptyTimeSlots
  const timeSlots = useMemo(
    () => usesDemoTimeSlots ? mockTimeSlots : getSharedTimeSlots(queryTimeSlots, selectedTicketSelections),
    [queryTimeSlots, selectedTicketSelections, usesDemoTimeSlots],
  )
  const firstAvailableSlot = timeSlots.find((slot) => slot.tone !== 'sold-out')
  const selectedSlot =
    timeSlots.find((slot) => slotKey(slot) === selectedSlotKey && slot.tone !== 'sold-out') ?? firstAvailableSlot
  const selectedTicketName = selectedTicketSelections.length === 1
    ? selectedTicketSelections[0].product.name
    : selectedTicketSelections.length > 1
      ? `${selectedTicketSelections.length}种票`
      : '未选择票种'

  useEffect(() => {
    if (firstAvailableProduct && !hasInitializedProducts) {
      setSelectedProductQuantities({ [firstAvailableProduct.key]: 2 })
      setHasInitializedProducts(true)
    }
  }, [firstAvailableProduct, hasInitializedProducts])

  useEffect(() => {
    if (firstAvailableSlot && (!selectedSlot || slotKey(selectedSlot) !== slotKey(firstAvailableSlot)) && !selectedSlotKey) {
      setSelectedSlotKey(slotKey(firstAvailableSlot))
    }
  }, [firstAvailableSlot, selectedSlot, selectedSlotKey])

  function selectVisitDate(visitDate: string) {
    setSelectedVisitDate(visitDate)
    setSelectedSlotKey(undefined)
  }

  function toggleProduct(productKey: string) {
    setSelectedProductQuantities((current) => {
      const next = { ...current }

      if (next[productKey] > 0) {
        delete next[productKey]
      } else {
        next[productKey] = 1
      }

      return next
    })
    setSelectedSlotKey(undefined)
  }

  function setProductQuantity(productKey: string, quantity: number) {
    setSelectedProductQuantities((current) => {
      const next = { ...current }

      if (quantity <= 0) {
        delete next[productKey]
      } else {
        next[productKey] = Math.min(8, quantity)
      }

      return next
    })
  }

  return {
    productsQuery,
    selectVisitDate,
    selectedProduct,
    selectedProductQuantities,
    selectedSlot,
    selectedTicketSelections,
    selectedTicketName,
    selectedVisitDate,
    setProductQuantity,
    setSelectedSlotKey,
    ticketProducts,
    timeSlots,
    timeSlotsQuery,
    toggleProduct,
    usesProductFallback,
    usesTimeSlotFallback,
  }
}
