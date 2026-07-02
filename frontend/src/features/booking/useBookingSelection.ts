import { useEffect, useState } from 'react'
import { ticketProducts as mockTicketProducts, timeSlots as mockTimeSlots } from './mockData'
import { useTicketProductsQuery, useTimeSlotsQuery } from './queries'
import { slotKey } from './utils'

export const visitDateOptions = [
  { label: '演示日 07-01', value: '2026-07-01' },
  { label: '今日 06-29', value: '2026-06-29' },
  { label: '明日 06-30', value: '2026-06-30' },
]

export function useBookingSelection() {
  const [selectedProductKey, setSelectedProductKey] = useState<string>()
  const [selectedVisitDate, setSelectedVisitDate] = useState(visitDateOptions[0].value)
  const [selectedSlotKey, setSelectedSlotKey] = useState<string>()
  const [quantity, setQuantity] = useState(2)
  const productsQuery = useTicketProductsQuery()
  const usesProductFallback = productsQuery.isError
  const ticketProducts = productsQuery.isSuccess ? productsQuery.data : usesProductFallback ? mockTicketProducts : []
  const firstAvailableProduct = ticketProducts.find((product) => !product.disabled)
  const selectedProduct =
    ticketProducts.find((product) => product.key === selectedProductKey && !product.disabled) ?? firstAvailableProduct
  const timeSlotsQuery = useTimeSlotsQuery({
    enabled: Boolean(productsQuery.isSuccess && selectedProduct?.ticketTypeId),
    ticketTypeId: selectedProduct?.ticketTypeId,
    visitDate: selectedVisitDate,
  })
  const usesTimeSlotFallback = Boolean(!usesProductFallback && productsQuery.isSuccess && selectedProduct && timeSlotsQuery.isError)
  const usesDemoTimeSlots = usesProductFallback || usesTimeSlotFallback
  const timeSlots = timeSlotsQuery.isSuccess ? timeSlotsQuery.data : usesDemoTimeSlots ? mockTimeSlots : []
  const firstAvailableSlot = timeSlots.find((slot) => slot.tone !== 'sold-out')
  const selectedSlot =
    timeSlots.find((slot) => slotKey(slot) === selectedSlotKey && slot.tone !== 'sold-out') ?? firstAvailableSlot
  const selectedTicketName = selectedProduct?.name ?? '未选择票种'

  useEffect(() => {
    if (firstAvailableProduct && selectedProduct?.key !== firstAvailableProduct.key && !selectedProductKey) {
      setSelectedProductKey(firstAvailableProduct.key)
    }
  }, [firstAvailableProduct, selectedProduct?.key, selectedProductKey])

  useEffect(() => {
    if (firstAvailableSlot && (!selectedSlot || slotKey(selectedSlot) !== slotKey(firstAvailableSlot)) && !selectedSlotKey) {
      setSelectedSlotKey(slotKey(firstAvailableSlot))
    }
  }, [firstAvailableSlot, selectedSlot, selectedSlotKey])

  function selectVisitDate(visitDate: string) {
    setSelectedVisitDate(visitDate)
    setSelectedSlotKey(undefined)
  }

  return {
    productsQuery,
    quantity,
    selectVisitDate,
    selectedProduct,
    selectedSlot,
    selectedTicketName,
    selectedVisitDate,
    setQuantity,
    setSelectedProductKey,
    setSelectedSlotKey,
    ticketProducts,
    timeSlots,
    timeSlotsQuery,
    usesProductFallback,
    usesTimeSlotFallback,
  }
}
