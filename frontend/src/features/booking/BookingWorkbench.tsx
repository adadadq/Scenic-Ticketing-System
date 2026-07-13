import {
  Col,
  Flex,
  Row,
} from 'antd'
import { useEffect, useMemo, useState } from 'react'
import {
  CustomerServiceOutlined,
  SafetyCertificateOutlined,
  ScheduleOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { useVisitorSessionQuery } from '../auth/queries'
import { useCreateOrderMutation } from '../orders/queries'
import {
  buildOrderCreateRequest,
  calculateBookingTotal,
  canCreateBookingOrder,
  getBookingPassengerLines,
  getBookingAuthMode,
  getBookingReadinessItems,
  getBookingTicketSummary,
  getBookingStepIndex,
  getBookingSubmitHint,
  getMobileActionLabel,
  getPrimaryActionLabel,
} from './bookingFlow'
import type { BookingAuthMode, BookingPassengerDraft } from './bookingFlow'
import { DateSlotPicker } from './components/DateSlotPicker'
import { BookingHeader } from './components/BookingHeader'
import { BookingMobileActionBar } from './components/BookingMobileActionBar'
import { BookingStepsCard } from './components/BookingStepsCard'
import { OrderSummaryPanel } from './components/OrderSummaryPanel'
import { PassengerAssignmentPanel } from './components/PassengerAssignmentPanel'
import { TicketSelector } from './components/TicketSelector'
import {
  useCreatePassengerTemplateMutation,
  useDeletePassengerTemplateMutation,
  usePassengerTemplatesQuery,
  useUpdatePassengerTemplateMutation,
} from './queries'
import { useBookingSelection, visitDateOptions } from './useBookingSelection'

type BookingWorkbenchProps = {
  onOpenAuth?: (mode: BookingAuthMode) => void
  onOrderCreated?: (orderNo: string) => void
  onOpenOrders?: () => void
  onOpenService?: () => void
}

const bookingStepItems = [
  { title: '选择票种', content: '选择门票类型' },
  { title: '选择时段', content: '选择日期和时段' },
  { title: '填写信息', content: '确认游客信息' },
  { title: '支付订单', content: '完成支付' },
]

export function BookingWorkbench({ onOpenAuth, onOpenOrders, onOpenService, onOrderCreated }: BookingWorkbenchProps) {
  const bookingSelection = useBookingSelection()
  const sessionQuery = useVisitorSessionQuery()
  const createOrderMutation = useCreateOrderMutation()
  const [passengerDrafts, setPassengerDrafts] = useState<Record<string, BookingPassengerDraft>>({})
  const {
    productsQuery,
    selectVisitDate,
    selectedProduct,
    selectedProductQuantities,
    selectedSlot,
    selectedTicketSelections,
    selectedTicketName,
    selectedVisitDate,
    setProductQuantity,
    setSelectedSlotKey,
    ticketProducts,
    timeSlots,
    timeSlotsQuery,
    toggleProduct,
    usesProductFallback,
    usesTimeSlotFallback,
  } = bookingSelection
  const visitor = sessionQuery.data ?? null
  const passengerLines = useMemo(
    () => getBookingPassengerLines(selectedTicketSelections),
    [selectedTicketSelections],
  )
  const passengerLineKeySignature = passengerLines.map((line) => line.key).join('|')
  const passengerTemplatesQuery = usePassengerTemplatesQuery(Boolean(visitor?.isRegistered))
  const createPassengerTemplateMutation = useCreatePassengerTemplateMutation()
  const updatePassengerTemplateMutation = useUpdatePassengerTemplateMutation()
  const deletePassengerTemplateMutation = useDeletePassengerTemplateMutation()
  const bookingGateState = {
    isSessionLoading: sessionQuery.isLoading,
    passengerDrafts,
    selectedProduct,
    selectedTicketSelections,
    selectedSlot,
    selectedVisitDate,
    usesProductFallback,
    usesTimeSlotFallback,
    visitor,
  }
  const authRequiredMode = getBookingAuthMode(bookingGateState)
  const totalAmount = calculateBookingTotal(selectedTicketSelections)
  const selectedTicketSummary = getBookingTicketSummary(selectedTicketSelections)
  const canCreateOrder = canCreateBookingOrder(bookingGateState)
  const submitHint = getBookingSubmitHint(bookingGateState)
  const readinessItems = getBookingReadinessItems(bookingGateState)
  const primaryActionLabel = getPrimaryActionLabel(authRequiredMode, sessionQuery.isLoading)
  const isFallbackCatalogMode = usesProductFallback || usesTimeSlotFallback
  const primaryActionDisabled = isFallbackCatalogMode || (!authRequiredMode && !canCreateOrder)
  const currentStep = getBookingStepIndex(bookingGateState)
  const mobileActionLabel = getMobileActionLabel(authRequiredMode, sessionQuery.isLoading, currentStep)
  const mobileActionDisabled = isFallbackCatalogMode || sessionQuery.isLoading
  const currentStepLabel = bookingStepItems[currentStep].title

  useEffect(() => {
    setPassengerDrafts((current) => {
      const activeKeys = new Set(passengerLineKeySignature ? passengerLineKeySignature.split('|') : [])
      if (Object.keys(current).every((key) => activeKeys.has(key))) {
        return current
      }
      const next = Object.fromEntries(Object.entries(current).filter(([key]) => activeKeys.has(key)))
      return next
    })
  }, [passengerLineKeySignature])

  function handlePassengerDraftChange(lineKey: string, draft: BookingPassengerDraft) {
    setPassengerDrafts((current) => ({
      ...current,
      [lineKey]: draft,
    }))
  }

  function createPendingOrder() {
    const orderRequest = buildOrderCreateRequest(bookingGateState)

    if (!canCreateOrder || !orderRequest) {
      return
    }

    createOrderMutation.mutate(
      orderRequest,
      {
        onSuccess: (order) => {
          if (onOrderCreated) {
            onOrderCreated(order.orderNo)
          } else {
            onOpenOrders?.()
          }
        },
      },
    )
  }

  function scrollToBookingSection(selector: string) {
    document.querySelector(selector)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
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

  function handleMobilePrimaryAction() {
    if (isFallbackCatalogMode || sessionQuery.isLoading) {
      return
    }

    if (authRequiredMode) {
      onOpenAuth?.(authRequiredMode)
      return
    }

    if (currentStep === 0) {
      scrollToBookingSection('.booking-selector-card')
      return
    }

    if (currentStep === 1) {
      scrollToBookingSection('.booking-slot-card')
      return
    }

    if (currentStep === 2) {
      scrollToBookingSection('.booking-passenger-card')
      return
    }

    createPendingOrder()
  }

  return (
    <>
      <BookingHeader onOpenOrders={onOpenOrders} onOpenService={onOpenService} />
      <BookingStepsCard currentStep={currentStep} currentStepLabel={currentStepLabel} items={bookingStepItems} />

      <Row className="booking-workbench-grid" gutter={[16, 16]} align="stretch">
        <Col xs={24} xl={17}>
          <section className="booking-selection-panel">
            <Flex vertical gap={16} className="main-stack">
              <TicketSelector
                isLoading={productsQuery.isLoading}
                onSelectProduct={toggleProduct}
                products={ticketProducts}
                productError={productsQuery.error}
                selectedProductQuantities={selectedProductQuantities}
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

              <PassengerAssignmentPanel
                drafts={passengerDrafts}
                isTemplateLoading={passengerTemplatesQuery.isLoading}
                lines={passengerLines}
                onCreateTemplate={(body) => createPassengerTemplateMutation.mutateAsync(body)}
                onDeleteTemplate={(templateId) => deletePassengerTemplateMutation.mutateAsync(templateId)}
                onDraftChange={handlePassengerDraftChange}
                onUpdateTemplate={(templateId, body) => updatePassengerTemplateMutation.mutateAsync({ templateId, body })}
                templates={passengerTemplatesQuery.data ?? []}
              />
            </Flex>
          </section>
        </Col>

        <Col xs={24} xl={7}>
          <OrderSummaryPanel
            canCreateOrder={canCreateOrder}
            createOrderError={createOrderMutation.error}
            isCreateOrderError={createOrderMutation.isError}
            isCreatingOrder={createOrderMutation.isPending}
            onPrimaryAction={handlePrimaryAction}
            onQuantityChange={setProductQuantity}
            primaryActionDisabled={primaryActionDisabled}
            primaryActionLabel={primaryActionLabel}
            readinessItems={readinessItems}
            selectedTicketSelections={selectedTicketSelections}
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
        disabled={mobileActionDisabled}
        isLoading={createOrderMutation.isPending}
        label={mobileActionLabel}
        onPrimaryAction={handleMobilePrimaryAction}
        selectedTicketName={selectedTicketSummary}
        totalAmount={totalAmount}
      />

      <div className="booking-service-strip" aria-label="票务服务保障">
        {[
          { icon: <SafetyCertificateOutlined />, title: '官方票务', text: '正品保障' },
          { icon: <SyncOutlined />, title: '灵活改签', text: '支持改期' },
          { icon: <ScheduleOutlined />, title: '安全支付', text: '多种支付方式' },
          { icon: <CustomerServiceOutlined />, title: '优质服务', text: '7×12小时服务' },
        ].map((item) => (
          <div className="booking-service-item" key={item.title}>
            {item.icon}
            <span>
              <strong>{item.title}</strong>
              <small>{item.text}</small>
            </span>
          </div>
        ))}
      </div>
    </>
  )
}
