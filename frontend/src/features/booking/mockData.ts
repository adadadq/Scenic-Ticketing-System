import type { TicketProduct, TimeSlotOption } from './types'

export const ticketProducts: TicketProduct[] = [
  {
    key: 'adult',
    name: '遇龙河成人票',
    audience: '18周岁（含）- 60周岁（含）',
    content: '景区门票 + 竹筏漂流',
    listPrice: 168,
    salePrice: 128,
    tag: '推荐',
    availability: 'onSale',
    disabled: false,
  },
  {
    key: 'child',
    name: '遇龙河儿童票',
    audience: '6周岁（含）- 18周岁（不含）',
    content: '景区门票 + 竹筏漂流',
    listPrice: 84,
    salePrice: 68,
    availability: 'onSale',
    disabled: false,
  },
  {
    key: 'family',
    name: '遇龙河家庭票',
    audience: '2名成人 + 1名儿童',
    content: '景区门票 + 竹筏漂流',
    listPrice: 420,
    salePrice: 328,
    tag: '优惠',
    availability: 'onSale',
    disabled: false,
  },
]

export const timeSlots: TimeSlotOption[] = [
  { label: '08:30-10:30', status: '充足', tone: 'available' },
  { label: '10:30-12:30', status: '充足', tone: 'available' },
  { label: '12:30-14:30', status: '充足', tone: 'available' },
  { label: '14:30-16:30', status: '较少', tone: 'limited' },
  { label: '16:30-18:30', status: '较少', tone: 'limited' },
  { label: '18:30-20:30', status: '已售罄', tone: 'sold-out' },
]
