import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { catalogApi, passengerTemplatesApi } from '../../shared/api/endpoints'
import type { PassengerTemplateRequest } from '../../shared/api/types'
import { mapProductToTicketProduct, mapTimeSlotToOption } from './adapters'

export const bookingQueryKeys = {
  passengerTemplates: ['booking', 'passengerTemplates'] as const,
  products: ['booking', 'products'] as const,
  timeSlots: (ticketTypeId: number | undefined, visitDate: string) =>
    ['booking', 'timeSlots', ticketTypeId ?? 'all', visitDate] as const,
}

export function usePassengerTemplatesQuery(enabled = true) {
  return useQuery({
    enabled,
    queryKey: bookingQueryKeys.passengerTemplates,
    retry: false,
    queryFn: () => passengerTemplatesApi.list(),
  })
}

export function useCreatePassengerTemplateMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: PassengerTemplateRequest) => passengerTemplatesApi.create(body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: bookingQueryKeys.passengerTemplates }),
  })
}

export function useUpdatePassengerTemplateMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ templateId, body }: { templateId: number; body: PassengerTemplateRequest }) =>
      passengerTemplatesApi.update(templateId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: bookingQueryKeys.passengerTemplates }),
  })
}

export function useDeletePassengerTemplateMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (templateId: number) => passengerTemplatesApi.delete(templateId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: bookingQueryKeys.passengerTemplates }),
  })
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
  const enabled = Boolean(params.visitDate) && (params.enabled ?? true)

  return useQuery({
    enabled,
    queryKey: bookingQueryKeys.timeSlots(params.ticketTypeId, params.visitDate ?? ''),
    retry: false,
    queryFn: async () => {
      if (!params.visitDate) {
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
