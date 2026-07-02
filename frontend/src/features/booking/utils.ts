import type { TimeSlotOption } from './types'

export function slotKey(slot: TimeSlotOption) {
  return slot.id ? String(slot.id) : slot.label
}
