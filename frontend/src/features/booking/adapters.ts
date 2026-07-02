import type { ProductPublic, TimeSlotPublic } from '../../shared/api/types'
import type { TicketProduct, TimeSlotOption } from './types'
import {
  mapProductContent,
  mapSlotLabel,
  mapSlotStatus,
  mapSlotTone,
  mapTicketAudience,
  parseCatalogPrice,
} from './catalogDisplay'

export function mapProductToTicketProduct(product: ProductPublic): TicketProduct {
  return {
    key: String(product.productId),
    productId: product.productId,
    ticketTypeId: product.ticketTypeId,
    productName: product.productName,
    name: product.ticketName,
    audience: mapTicketAudience(product.ticketCategory),
    content: mapProductContent(product),
    listPrice: parseCatalogPrice(product.originalPrice),
    salePrice: parseCatalogPrice(product.salePrice),
    availability: 'onSale',
    disabled: false,
  }
}

export function mapTimeSlotToOption(slot: TimeSlotPublic): TimeSlotOption {
  return {
    id: slot.timeSlotId,
    ticketTypeId: slot.ticketTypeId,
    visitDate: slot.visitDate,
    label: mapSlotLabel(slot),
    status: mapSlotStatus(slot),
    tone: mapSlotTone(slot.quotaRemaining),
    remainingQuota: slot.quotaRemaining,
  }
}
