import type { ProductPublic, TimeSlotPublic } from '../../shared/api/types'
import { scenicProductName, scenicTicketName } from '../../shared/display/scenicText'
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
    productName: scenicProductName(product.productName, product.ticketCategory),
    name: scenicTicketName(product.ticketName, product.ticketCategory),
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
    productId: slot.productId,
    ticketTypeId: slot.ticketTypeId,
    visitDate: slot.visitDate,
    label: mapSlotLabel(slot),
    status: mapSlotStatus(slot),
    tone: mapSlotTone(slot.quotaRemaining),
    remainingQuota: slot.quotaRemaining,
  }
}
