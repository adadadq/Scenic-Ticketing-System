export type TicketProduct = {
  key: string
  productId?: number
  ticketTypeId?: number
  productName?: string
  name: string
  audience: string
  content: string
  listPrice: number
  salePrice: number
  tag?: string
  availability: 'onSale' | 'soldOut' | 'suspended'
  disabled: boolean
}

export type TimeSlotOption = {
  id?: number
  productId?: number
  ticketTypeId?: number
  visitDate?: string
  label: string
  status: string
  tone: 'available' | 'limited' | 'sold-out'
  remainingQuota?: number
  itemTimeSlotIds?: Record<string, number>
}
