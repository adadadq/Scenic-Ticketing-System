import type { OrderCreateRequest, VisitorMe } from '../../shared/api/types'
import type { TicketProduct, TimeSlotOption } from './types'

export type BookingAuthMode = 'login' | 'register'
export type BookingReadinessStatus = 'done' | 'active' | 'blocked'

export type BookingReadinessItem = {
  detail: string
  key: 'product' | 'slot' | 'visitor' | 'passenger' | 'order'
  label: string
  status: BookingReadinessStatus
}

export type BookingTicketSelection = {
  product: TicketProduct
  quantity: number
}

export type BookingPassengerDraft = {
  idNumber: string
  idType: string
  passengerName: string
  phone: string
  templateId?: number
}

export type BookingPassengerLine = {
  key: string
  label: string
  product: TicketProduct
  ticketIndex: number
}

type BookingSelection = {
  selectedProduct?: TicketProduct
  selectedTicketSelections: BookingTicketSelection[]
  selectedSlot?: TimeSlotOption
  selectedVisitDate: string
}

type VisitorState = {
  isSessionLoading: boolean
  visitor: VisitorMe | null
}

type BookingGateState = BookingSelection & VisitorState & {
  passengerDrafts: Record<string, BookingPassengerDraft>
  usesProductFallback: boolean
  usesTimeSlotFallback: boolean
}

export function getBookingAuthMode({ isSessionLoading, visitor }: VisitorState): BookingAuthMode | undefined {
  if (isSessionLoading) {
    return undefined
  }

  if (!visitor) {
    return 'login'
  }

  return visitor.isRegistered ? undefined : 'register'
}

export function getBookingTotalQuantity(selectedTicketSelections: BookingTicketSelection[]) {
  return selectedTicketSelections.reduce((sum, item) => sum + item.quantity, 0)
}

export function getBookingTicketSummary(selectedTicketSelections: BookingTicketSelection[]) {
  if (selectedTicketSelections.length === 0) {
    return '未选择票种'
  }

  if (selectedTicketSelections.length === 1) {
    const [selection] = selectedTicketSelections
    return `${selection.product.name} × ${selection.quantity}`
  }

  return `${selectedTicketSelections.length}种票 × ${getBookingTotalQuantity(selectedTicketSelections)}`
}

export function calculateBookingTotal(selectedTicketSelections: BookingTicketSelection[]) {
  return selectedTicketSelections.reduce((sum, item) => sum + item.product.salePrice * item.quantity, 0)
}

function getSelectedTimeSlotId(product: TicketProduct, selectedSlot?: TimeSlotOption) {
  if (!selectedSlot) {
    return undefined
  }

  if (selectedSlot.itemTimeSlotIds?.[product.key]) {
    return selectedSlot.itemTimeSlotIds[product.key]
  }

  if (product.productId && selectedSlot.productId === product.productId) {
    return selectedSlot.id
  }

  if (!product.productId && product.ticketTypeId && selectedSlot.ticketTypeId === product.ticketTypeId) {
    return selectedSlot.id
  }

  return undefined
}

function hasOrderableTicketSelections(selectedTicketSelections: BookingTicketSelection[], selectedSlot?: TimeSlotOption) {
  return selectedTicketSelections.length > 0 &&
    selectedTicketSelections.every(({ product, quantity }) => (
      quantity > 0 &&
      Boolean(product.productId) &&
      Boolean(getSelectedTimeSlotId(product, selectedSlot))
    ))
}

export function getBookingPassengerLines(selectedTicketSelections: BookingTicketSelection[]) {
  return selectedTicketSelections.flatMap(({ product, quantity }) =>
    Array.from({ length: quantity }, (_, index) => ({
      key: `${product.key}-${index + 1}`,
      label: `${product.name} 第 ${index + 1} 张`,
      product,
      ticketIndex: index + 1,
    })),
  )
}

function isPassengerDraftComplete(draft?: BookingPassengerDraft) {
  return Boolean(
    draft?.passengerName.trim() &&
      draft.idType.trim() &&
      draft.idNumber.trim() &&
      /^1\d{10}$/.test(draft.phone.trim()),
  )
}

function hasReadyPassengers(
  selectedTicketSelections: BookingTicketSelection[],
  passengerDrafts: Record<string, BookingPassengerDraft>,
) {
  const passengerLines = getBookingPassengerLines(selectedTicketSelections)
  return passengerLines.length > 0 && passengerLines.every((line) => isPassengerDraftComplete(passengerDrafts[line.key]))
}

export function canCreateBookingOrder({
  passengerDrafts,
  selectedTicketSelections,
  selectedSlot,
  selectedVisitDate,
  visitor,
}: BookingGateState) {
  return Boolean(
    visitor?.isRegistered &&
      selectedSlot?.id &&
      (selectedSlot.visitDate ?? selectedVisitDate) &&
      hasOrderableTicketSelections(selectedTicketSelections, selectedSlot) &&
      hasReadyPassengers(selectedTicketSelections, passengerDrafts),
  )
}

export function getBookingSubmitHint({
  isSessionLoading,
  passengerDrafts,
  selectedTicketSelections,
  selectedSlot,
  usesProductFallback,
  usesTimeSlotFallback,
  visitor,
}: BookingGateState) {
  if (isSessionLoading) {
    return '正在确认登录状态。'
  }

  if (!visitor) {
    return '请先登录账号。'
  }

  if (!visitor.isRegistered) {
    return '注册账号后即可提交订单。'
  }

  if (usesProductFallback) {
    return '票务服务暂时不稳定，请稍后再提交订单。'
  }

  if (usesTimeSlotFallback) {
    return '预约时段暂时不稳定，请稍后再提交订单。'
  }

  if (!selectedSlot?.id || !hasOrderableTicketSelections(selectedTicketSelections, selectedSlot)) {
    return '请重新选择门票和游玩时间。'
  }

  if (!hasReadyPassengers(selectedTicketSelections, passengerDrafts)) {
    return '请为每一张票填写出行人。'
  }

  return '提交后可在“我的订单”继续支付。'
}

export function getBookingReadinessItems({
  isSessionLoading,
  passengerDrafts,
  selectedTicketSelections,
  selectedSlot,
  selectedVisitDate,
  usesProductFallback,
  usesTimeSlotFallback,
  visitor,
}: BookingGateState): BookingReadinessItem[] {
  const hasRealProduct = selectedTicketSelections.length > 0 &&
    selectedTicketSelections.every(({ product, quantity }) => quantity > 0 && Boolean(product.productId)) &&
    !usesProductFallback
  const hasRealSlot = Boolean(selectedSlot?.id && (selectedSlot.visitDate ?? selectedVisitDate)) && !usesTimeSlotFallback
  const hasRegisteredVisitor = Boolean(visitor?.isRegistered)
  const passengerLines = getBookingPassengerLines(selectedTicketSelections)
  const readyPassengerCount = passengerLines.filter((line) => isPassengerDraftComplete(passengerDrafts[line.key])).length
  const hasPassengers = passengerLines.length > 0 && readyPassengerCount === passengerLines.length
  const canCreateOrder = hasRealProduct &&
    hasRealSlot &&
    hasRegisteredVisitor &&
    hasOrderableTicketSelections(selectedTicketSelections, selectedSlot) &&
    hasPassengers

  return [
    {
      detail: hasRealProduct
        ? getBookingTicketSummary(selectedTicketSelections)
        : usesProductFallback
          ? '票务服务暂时不稳定'
          : '先选择可售票种',
      key: 'product',
      label: '票种',
      status: hasRealProduct ? 'done' : usesProductFallback ? 'blocked' : 'active',
    },
    {
      detail: hasRealSlot
        ? `${selectedSlot?.visitDate ?? selectedVisitDate} ${selectedSlot?.label ?? ''}`.trim()
        : usesTimeSlotFallback
          ? '预约时段暂时不稳定'
          : '选择游览日期和入园时段',
      key: 'slot',
      label: '时段',
      status: hasRealSlot ? 'done' : usesTimeSlotFallback ? 'blocked' : 'active',
    },
    {
      detail: isSessionLoading
        ? '正在确认登录状态'
        : hasRegisteredVisitor
          ? `${visitor?.visitorName} 已登录`
          : visitor
            ? '请先注册账号'
            : '登录后才能继续创建订单',
      key: 'visitor',
      label: '账号',
      status: hasRegisteredVisitor ? 'done' : 'active',
    },
    {
      detail: hasPassengers
        ? `${readyPassengerCount} 位出行人已确认`
        : passengerLines.length > 0
          ? `已填写 ${readyPassengerCount}/${passengerLines.length} 位`
          : '选择票种后填写出行人',
      key: 'passenger',
      label: '出行人',
      status: hasPassengers ? 'done' : 'active',
    },
    {
      detail: canCreateOrder ? '可以提交订单' : '补齐前面信息后提交订单',
      key: 'order',
      label: '下单',
      status: canCreateOrder ? 'done' : 'active',
    },
  ]
}

export function getPrimaryActionLabel(authRequiredMode: BookingAuthMode | undefined, isSessionLoading: boolean) {
  if (authRequiredMode === 'login') {
    return '先登录'
  }

  if (authRequiredMode === 'register') {
    return '去注册'
  }

  return isSessionLoading ? '检查中' : '提交订单'
}

export function getMobileActionLabel(authRequiredMode: BookingAuthMode | undefined, isSessionLoading: boolean) {
  if (authRequiredMode === 'login') {
    return '登录'
  }

  if (authRequiredMode === 'register') {
    return '注册'
  }

  return isSessionLoading ? '检查中' : '下单'
}

export function getBookingStepIndex({
  passengerDrafts,
  selectedProduct,
  selectedTicketSelections,
  selectedSlot,
  usesProductFallback,
  usesTimeSlotFallback,
  visitor,
}: BookingGateState) {
  if (usesProductFallback || !selectedProduct) {
    return 0
  }

  if (usesTimeSlotFallback || !selectedSlot) {
    return 1
  }

  if (!visitor?.isRegistered || !hasReadyPassengers(selectedTicketSelections, passengerDrafts)) {
    return 2
  }

  return 3
}

export function buildOrderCreateRequest({
  passengerDrafts,
  selectedTicketSelections,
  selectedSlot,
  selectedVisitDate,
  visitor,
}: BookingGateState): OrderCreateRequest | null {
  if (!visitor || selectedTicketSelections.length === 0 || !selectedSlot?.id) {
    return null
  }

  if (!hasOrderableTicketSelections(selectedTicketSelections, selectedSlot)) {
    return null
  }

  if (!hasReadyPassengers(selectedTicketSelections, passengerDrafts)) {
    return null
  }

  return {
    buyerName: visitor.visitorName,
    buyerPhone: visitor.phone,
    items: selectedTicketSelections.map(({ product, quantity }) => {
      const timeSlotId = getSelectedTimeSlotId(product, selectedSlot)!

      return {
        productId: product.productId!,
        timeSlotId,
        visitDate: selectedSlot.visitDate ?? selectedVisitDate,
        quantity,
        passengers: Array.from({ length: quantity }, (_, index) => {
          const draft = passengerDrafts[`${product.key}-${index + 1}`]

          return {
            passengerName: draft.passengerName.trim(),
            idType: draft.idType.trim(),
            idNumber: draft.idNumber.trim(),
            phone: draft.phone.trim(),
          }
        }),
      }
    }),
  }
}
