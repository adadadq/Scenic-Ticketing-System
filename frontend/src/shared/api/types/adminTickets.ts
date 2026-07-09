export type AdminTicketStatus = 'ON_SALE' | 'OFF_SALE'

export type AdminTicket = {
  allocatedQuota: number
  dateFrom?: string | null
  dateTo?: string | null
  description?: string | null
  id: number
  name: string
  route: string
  salePrice: string
  slotQuota: number
  slotQuotas?: AdminTicketSlotQuota[]
  status: AdminTicketStatus
  stock: number
  type: string
}

export type AdminTicketSlotQuota = {
  slotStartTime: string
  slotEndTime: string
  quota: number
}

export type AdminTicketSaveRequest = {
  dateFrom?: string
  dateTo?: string
  description?: string
  name: string
  route: string
  salePrice: number
  slotQuota: number
  slotQuotas?: AdminTicketSlotQuota[]
  status: AdminTicketStatus
  stock: number
  type: string
}
