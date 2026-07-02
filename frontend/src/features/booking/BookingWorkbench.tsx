import {
  Col,
  Flex,
  Row,
} from 'antd'
import { useVisitorSessionQuery } from '../auth/queries'
import { useCreateOrderMutation } from '../orders/queries'
import {
  buildOrderCreateRequest,
  calculateBookingTotal,
  canCreateBookingOrder,
  getBookingAuthMode,
  getBookingReadinessItems,
  getBookingStepIndex,
  getBookingSubmitHint,
  getMobileActionLabel,
  getPrimaryActionLabel,
} from './bookingFlow'
import type { BookingAuthMode } from './bookingFlow'
import { DateSlotPicker } from './components/DateSlotPicker'
import { BookingHeader } from './components/BookingHeader'
import { BookingMobileActionBar } from './components/BookingMobileActionBar'
import { BookingStepsCard } from './components/BookingStepsCard'
import { OrderSummaryPanel } from './components/OrderSummaryPanel'
import { TicketSelector } from './components/TicketSelector'
import { useBookingSelection, visitDateOptions } from './useBookingSelection'

type BookingWorkbenchProps = {
  onOpenAuth?: (mode: BookingAuthMode) => void
  onOpenOrders?: () => void
}

const bookingStepItems = [
  { title: '选择票种', content: '选择门票类型' },
  { title: '选择时段', content: '选择日期和时段' },
  { title: '填写信息', content: '确认游客信息' },
  { title: '支付订单', content: '模拟支付' },
]

export function BookingWorkbench({ onOpenAuth, onOpenOrders }: BookingWorkbenchProps) {
  const bookingSelection = useBookingSelection()
  const sessionQuery = useVisitorSessionQuery()
  const createOrderMutation = useCreateOrderMutation()
  const {
    productsQuery,
    quantity,
    selectVisitDate,
    selectedProduct,
    selectedSlot,
    selectedTicketName,
    selectedVisitDate,
    setQuantity,
    setSelectedProductKey,
    setSelectedSlotKey,
    ticketProducts,
    timeSlots,
    timeSlotsQuery,
    usesProductFallback,
    usesTimeSlotFallback,
  } = bookingSelection
  const visitor = sessionQuery.data ?? null
  const bookingGateState = {
    isSessionLoading: sessionQuery.isLoading,
    quantity,
    selectedProduct,
    selectedSlot,
    selectedVisitDate,
    usesProductFallback,
    usesTimeSlotFallback,
    visitor,
  }
  const authRequiredMode = getBookingAuthMode(bookingGateState)
  const totalAmount = calculateBookingTotal(selectedProduct, quantity)
  const canCreateOrder = canCreateBookingOrder(bookingGateState)
  const submitHint = getBookingSubmitHint(bookingGateState)
  const readinessItems = getBookingReadinessItems(bookingGateState)
  const primaryActionLabel = getPrimaryActionLabel(authRequiredMode, sessionQuery.isLoading)
  const mobileActionLabel = getMobileActionLabel(authRequiredMode, sessionQuery.isLoading)
  const isFallbackCatalogMode = usesProductFallback || usesTimeSlotFallback
  const primaryActionDisabled = isFallbackCatalogMode || (!authRequiredMode && !canCreateOrder)
  const currentStep = getBookingStepIndex(bookingGateState)
  const currentStepLabel = bookingStepItems[currentStep].title

  function createPendingOrder() {
    const orderRequest = buildOrderCreateRequest(bookingGateState)

    if (!canCreateOrder || !orderRequest) {
      return
    }

    createOrderMutation.mutate(
      orderRequest,
      {
        onSuccess: () => {
          onOpenOrders?.()
        },
      },
    )
  }

  function handlePrimaryAction() {
    if (isFallbackCatalogMode) {
      return
    }

    if (authRequiredMode) {
      onOpenAuth?.(authRequiredMode)
      return
    }

    createPendingOrder()
  }

  return (
    <>
      <BookingHeader onOpenOrders={onOpenOrders} />
      <BookingStepsCard currentStep={currentStep} currentStepLabel={currentStepLabel} items={bookingStepItems} />

      <Row className="booking-workbench-grid" gutter={[16, 16]} align="stretch">
        <Col xs={24} xl={17}>
          <Flex vertical gap={16} className="main-stack">
            <TicketSelector
              isLoading={productsQuery.isLoading}
              onSelectProduct={setSelectedProductKey}
              products={ticketProducts}
              productError={productsQuery.error}
              selectedProduct={selectedProduct}
              usesProductFallback={usesProductFallback}
            />

            <DateSlotPicker
              isLoading={timeSlotsQuery.isLoading}
              onSelectSlot={setSelectedSlotKey}
              onSelectVisitDate={selectVisitDate}
              selectedSlot={selectedSlot}
              selectedVisitDate={selectedVisitDate}
              timeSlotError={timeSlotsQuery.error}
              timeSlots={timeSlots}
              usesTimeSlotFallback={usesTimeSlotFallback}
              visitDateOptions={visitDateOptions}
            />
          </Flex>
        </Col>

        <Col xs={24} xl={7}>
          <OrderSummaryPanel
            canCreateOrder={canCreateOrder}
            createOrderError={createOrderMutation.error}
            isCreateOrderError={createOrderMutation.isError}
            isCreatingOrder={createOrderMutation.isPending}
            onPrimaryAction={handlePrimaryAction}
            onQuantityChange={setQuantity}
            primaryActionDisabled={primaryActionDisabled}
            primaryActionLabel={primaryActionLabel}
            quantity={quantity}
            readinessItems={readinessItems}
            selectedSlot={selectedSlot}
            selectedTicketName={selectedTicketName}
            selectedVisitDate={selectedVisitDate}
            submitHint={submitHint}
            totalAmount={totalAmount}
            visitor={visitor}
          />
        </Col>
      </Row>

      <BookingMobileActionBar
        disabled={primaryActionDisabled}
        isLoading={createOrderMutation.isPending}
        label={mobileActionLabel}
        onPrimaryAction={handlePrimaryAction}
        quantity={quantity}
        selectedTicketName={selectedTicketName}
        totalAmount={totalAmount}
      />
    </>
  )
}
