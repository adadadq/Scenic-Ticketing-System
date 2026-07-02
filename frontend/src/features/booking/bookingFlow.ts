import type { OrderCreateRequest, VisitorMe } from '../../shared/api/types'
import type { TicketProduct, TimeSlotOption } from './types'

export type BookingAuthMode = 'login' | 'register'
export type BookingReadinessStatus = 'done' | 'active' | 'blocked'

export type BookingReadinessItem = {
  detail: string
  key: 'product' | 'slot' | 'visitor' | 'order'
  label: string
  status: BookingReadinessStatus
}

type BookingSelection = {
  selectedProduct?: TicketProduct
  selectedSlot?: TimeSlotOption
  selectedVisitDate: string
}

type VisitorState = {
  isSessionLoading: boolean
  visitor: VisitorMe | null
}

type BookingGateState = BookingSelection & VisitorState & {
  quantity: number
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

export function calculateBookingTotal(selectedProduct: TicketProduct | undefined, quantity: number) {
  return (selectedProduct?.salePrice ?? 0) * quantity
}

export function canCreateBookingOrder({
  quantity,
  selectedProduct,
  selectedSlot,
  selectedVisitDate,
  visitor,
}: BookingGateState) {
  return Boolean(
    visitor?.isRegistered &&
      selectedProduct?.productId &&
      selectedSlot?.id &&
      (selectedSlot.visitDate ?? selectedVisitDate) &&
      quantity > 0,
  )
}

export function getBookingSubmitHint({
  isSessionLoading,
  selectedProduct,
  selectedSlot,
  usesProductFallback,
  usesTimeSlotFallback,
  visitor,
}: BookingGateState) {
  if (isSessionLoading) {
    return '正在检查游客会话。'
  }

  if (!visitor) {
    return '请先使用手机号登录。'
  }

  if (!visitor.isRegistered) {
    return '临时游客可浏览票品，创建订单前需要完成实名登记。'
  }

  if (usesProductFallback) {
    return '票品接口暂不可用，当前仅可浏览演示数据，不能创建订单。'
  }

  if (usesTimeSlotFallback) {
    return '时段接口暂不可用，当前仅可浏览演示数据，不能创建订单。'
  }

  if (!selectedProduct?.productId || !selectedSlot?.id) {
    return '当前显示的是演示数据，连接到真实票品和时段后可创建订单。'
  }

  return '创建后会进入待支付订单，可在“我的订单”继续模拟支付。'
}

export function getBookingReadinessItems({
  isSessionLoading,
  quantity,
  selectedProduct,
  selectedSlot,
  selectedVisitDate,
  usesProductFallback,
  usesTimeSlotFallback,
  visitor,
}: BookingGateState): BookingReadinessItem[] {
  const hasRealProduct = Boolean(selectedProduct?.productId) && !usesProductFallback
  const hasRealSlot = Boolean(selectedSlot?.id && (selectedSlot.visitDate ?? selectedVisitDate)) && !usesTimeSlotFallback
  const hasRegisteredVisitor = Boolean(visitor?.isRegistered)
  const canCreateOrder = hasRealProduct && hasRealSlot && hasRegisteredVisitor && quantity > 0

  return [
    {
      detail: hasRealProduct
        ? selectedProduct?.name ?? '已选择可售票种'
        : usesProductFallback
          ? '票品接口使用演示数据，暂不可下单'
          : '先选择一个可售票种',
      key: 'product',
      label: '票种',
      status: hasRealProduct ? 'done' : usesProductFallback ? 'blocked' : 'active',
    },
    {
      detail: hasRealSlot
        ? `${selectedSlot?.visitDate ?? selectedVisitDate} ${selectedSlot?.label ?? ''}`.trim()
        : usesTimeSlotFallback
          ? '时段接口使用演示数据，暂不可下单'
          : '选择游览日期和入园时段',
      key: 'slot',
      label: '时段',
      status: hasRealSlot ? 'done' : usesTimeSlotFallback ? 'blocked' : 'active',
    },
    {
      detail: isSessionLoading
        ? '正在检查游客会话'
        : hasRegisteredVisitor
          ? `${visitor?.visitorName} 已完成实名`
          : visitor
            ? '临时游客需要先完成实名登记'
            : '登录后才能继续创建订单',
      key: 'visitor',
      label: '实名',
      status: hasRegisteredVisitor ? 'done' : 'active',
    },
    {
      detail: canCreateOrder ? '可以创建待支付订单' : '补齐前面步骤后生成待支付订单',
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
    return '去实名登记'
  }

  return isSessionLoading ? '检查会话中' : '创建待支付订单'
}

export function getMobileActionLabel(authRequiredMode: BookingAuthMode | undefined, isSessionLoading: boolean) {
  if (authRequiredMode === 'login') {
    return '登录'
  }

  if (authRequiredMode === 'register') {
    return '去实名'
  }

  return isSessionLoading ? '检查中' : '下单'
}

export function getBookingStepIndex({
  selectedProduct,
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

  return visitor?.isRegistered ? 3 : 2
}

export function buildOrderCreateRequest({
  quantity,
  selectedProduct,
  selectedSlot,
  selectedVisitDate,
  visitor,
}: BookingGateState): OrderCreateRequest | null {
  if (!visitor || !selectedProduct?.productId || !selectedSlot?.id) {
    return null
  }

  return {
    buyerName: visitor.visitorName,
    buyerPhone: visitor.phone,
    items: [
      {
        productId: selectedProduct.productId,
        timeSlotId: selectedSlot.id,
        visitDate: selectedSlot.visitDate ?? selectedVisitDate,
        quantity,
      },
    ],
  }
}
