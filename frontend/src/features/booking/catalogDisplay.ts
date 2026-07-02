import type { ProductPublic, TimeSlotPublic } from '../../shared/api/types'
import type { TimeSlotOption } from './types'

function trimTime(value: string) {
  return value.slice(0, 5)
}

export function parseCatalogPrice(value: string) {
  const price = Number(value)

  return Number.isFinite(price) ? price : 0
}

export function mapTicketAudience(category: string) {
  if (category === 'ADULT') {
    return '成人票'
  }

  if (category === 'CHILD') {
    return '儿童票'
  }

  if (category === 'FAMILY') {
    return '家庭票'
  }

  return category
}

export function mapProductContent(product: ProductPublic) {
  if (product.description) {
    return product.description
  }

  return `${product.startPierName} 至 ${product.endPierName}`
}

export function mapSlotTone(quotaRemaining: number): TimeSlotOption['tone'] {
  if (quotaRemaining <= 0) {
    return 'sold-out'
  }

  return quotaRemaining <= 20 ? 'limited' : 'available'
}

export function mapSlotStatus(slot: TimeSlotPublic) {
  if (slot.quotaRemaining <= 0) {
    return '已售罄'
  }

  return slot.quotaRemaining > 20 ? '充足' : `余 ${slot.quotaRemaining}`
}

export function mapSlotLabel(slot: TimeSlotPublic) {
  return `${trimTime(slot.slotStartTime)}-${trimTime(slot.slotEndTime)}`
}
