import { useQuery } from '@tanstack/react-query'
import { catalogApi } from '../../shared/api/endpoints'
import { mapProductToTicketProduct, mapTimeSlotToOption } from './adapters'

export const bookingQueryKeys = {
  products: ['booking', 'products'] as const,
  timeSlots: (ticketTypeId: number, visitDate: string) =>
    ['booking', 'timeSlots', ticketTypeId, visitDate] as const,
}

export function useTicketProductsQuery() {
  return useQuery({
    queryKey: bookingQueryKeys.products,
    retry: false,
    queryFn: async () => {
      const products = await catalogApi.products()
      return products.map(mapProductToTicketProduct)
    },
  })
}

export function useTimeSlotsQuery(params: {
  enabled?: boolean
  ticketTypeId?: number
  visitDate?: string
}) {
  const enabled = Boolean(params.ticketTypeId && params.visitDate) && (params.enabled ?? true)

  return useQuery({
    enabled,
    queryKey: bookingQueryKeys.timeSlots(params.ticketTypeId ?? 0, params.visitDate ?? ''),
    retry: false,
    queryFn: async () => {
      if (!params.ticketTypeId || !params.visitDate) {
        return []
      }

      const timeSlots = await catalogApi.timeSlots({
        ticketTypeId: params.ticketTypeId,
        visitDate: params.visitDate,
      })

      return timeSlots.map(mapTimeSlotToOption)
    },
  })
}
