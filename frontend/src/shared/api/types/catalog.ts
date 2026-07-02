export type ProductPublic = {
  productId: number
  ticketTypeId: number
  scenicSpotName: string
  productName: string
  ticketName: string
  ticketCategory: string
  originalPrice: string
  salePrice: string
  description?: string | null
  refundRule?: string | null
  realNameRequired: boolean
  tripType: string
  raftCapacity: number
  startPierName: string
  endPierName: string
  windowPhone: string
}

export type TimeSlotPublic = {
  timeSlotId: number
  productId: number
  ticketTypeId: number
  visitDate: string
  slotStartTime: string
  slotEndTime: string
  quotaRemaining: number
}
