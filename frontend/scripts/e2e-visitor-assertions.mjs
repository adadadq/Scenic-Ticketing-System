import {
  assert,
  assertDeepEqual,
} from './e2e-runtime-utils.mjs'
import { e2eVisitDates } from './e2e-mock-api.mjs'

export function assertVisitorE2eState({
  bookingBreakpointStates,
  bookingStepState,
  cancelNotAllowedState,
  catalogFallbackState,
  desktopAuthActionState,
  desktopBookingVisualState,
  desktopDetailState,
  e2ePhone,
  e2ePassword,
  e2eUsername,
  emptyOrdersState,
  emptyTimeSlotsState,
  loggedOutOrdersState,
  mobileAuthModalState,
  mobileBookingNextState,
  mobileBookingVisualState,
  mobileDateStripState,
  mobileDetailActionState,
  mobileTicketCardState,
  mock,
  notPayablePaymentState,
  orderCardToneState,
  orderDetailErrorState,
  orderStatusFilterState,
  pageState,
  paidPageState,
  quotaPaymentState,
  sessionFailureState,
  timeSlotFallbackState,
  visitorShellState,
}) {
  const expectedOrderBody = {
    buyerName: e2eUsername,
    buyerPhone: e2ePhone,
    items: [{
      productId: 1,
      timeSlotId: 100,
      visitDate: e2eVisitDates.primaryDate,
      quantity: 2,
      passengers: [
        { passengerName: '出行人1', idType: 'ID_CARD', idNumber: '110101199001010011', phone: '13911112221' },
        { passengerName: '出行人2', idType: 'ID_CARD', idNumber: '110101199001010012', phone: '13911112222' },
      ],
    }],
  }
  const expectedRegisterBody = {
    password: e2ePassword,
    phone: e2ePhone,
    username: e2eUsername,
  }

  if (mock) {
    const firstOrderPaymentKeys = mock.state.paymentAttempts
      .filter((attempt) => attempt.orderNo === 'ORD-E2E-001')
      .map((attempt) => attempt.idempotencyKey)
    const secondOrderPaymentKeys = mock.state.paymentAttempts
      .filter((attempt) => attempt.orderNo === 'ORD-E2E-002')
      .map((attempt) => attempt.idempotencyKey)
    const thirdOrderPaymentKeys = mock.state.paymentAttempts
      .filter((attempt) => attempt.orderNo === 'ORD-E2E-003')
      .map((attempt) => attempt.idempotencyKey)
    assertDeepEqual(mock.state.loginBodies, [{ password: e2ePassword, username: e2eUsername }], 'visitor login bodies')
    assertDeepEqual(mock.state.registerBodies, [expectedRegisterBody, expectedRegisterBody], 'visitor register bodies')
    assertDeepEqual(mock.state.createOrderBody, expectedOrderBody, 'last order create body')
    assertDeepEqual(mock.state.createOrderBodies, [expectedOrderBody, expectedOrderBody, expectedOrderBody, expectedOrderBody], 'order create bodies')
    assert(firstOrderPaymentKeys[0]?.startsWith('pay:'), 'payment idempotency key should use pay prefix')
    assert(firstOrderPaymentKeys.length === 2, 'payment retry should send two payment attempts for first order')
    assert(firstOrderPaymentKeys[0] === firstOrderPaymentKeys[1], 'payment retry should reuse idempotency key')
    assert(secondOrderPaymentKeys.length === 1, 'not payable payment branch should send one second order payment attempt')
    assert(secondOrderPaymentKeys[0]?.startsWith('pay:'), 'second order payment idempotency key should use pay prefix')
    assert(secondOrderPaymentKeys[0] !== firstOrderPaymentKeys[0], 'different orders should not reuse payment idempotency keys')
    assert(thirdOrderPaymentKeys.length === 1, 'quota payment branch should send one third order payment attempt')
    assert(thirdOrderPaymentKeys[0]?.startsWith('pay:'), 'third order payment idempotency key should use pay prefix')
    assert(thirdOrderPaymentKeys[0] !== firstOrderPaymentKeys[0], 'quota order should not reuse first order payment idempotency key')
    assert(thirdOrderPaymentKeys[0] !== secondOrderPaymentKeys[0], 'quota order should not reuse second order payment idempotency key')
    assertDeepEqual(mock.state.cancelOrderNos, ['ORD-E2E-002', 'ORD-E2E-003', 'ORD-E2E-004'], 'cancelled order numbers')
    assert(mock.state.csrfFetchCount >= 3, 'auth state changes should force CSRF refetches')
    assert(mock.state.csrfHeaders.length >= 14, 'auth, create, pay retry, blocked payment branches, cancels, and logout should all be CSRF-protected')
  }

  assert(
    !mock ||
      (loggedOutOrdersState.hasAuthError &&
        loggedOutOrdersState.canOpenLogin &&
        loggedOutOrdersState.canReturnBooking &&
        !loggedOutOrdersState.hasFilters &&
        loggedOutOrdersState.fitsViewport &&
        loggedOutOrdersState.titleIsHorizontal &&
        !loggedOutOrdersState.hasEmptyText),
    `logged-out orders should show auth error instead of empty state: ${JSON.stringify(loggedOutOrdersState)}`,
  )
  assert(!mock || (emptyOrdersState.hasEmptyText && emptyOrdersState.canOpenBooking), 'empty orders should offer booking action')
  assert(!mock || emptyOrdersState.mobileOrdersVisible, 'empty orders mobile list should render at 390px')
  assert(
    !mock ||
      (sessionFailureState.hasSessionError &&
        sessionFailureState.hasDiagnosticCode &&
        sessionFailureState.hasDiagnosticRequestId &&
        sessionFailureState.hasRetryAction),
    `session failure should show diagnosable retry state: ${JSON.stringify(sessionFailureState)}`,
  )
  assert(
    !mock ||
      (catalogFallbackState.hasCatalogAlert &&
        catalogFallbackState.hasDemoHint &&
        catalogFallbackState.hasDemoSlot &&
        catalogFallbackState.hasDemoTicket &&
        catalogFallbackState.currentStepLabel === '选择票种' &&
        catalogFallbackState.createButtonDisabled),
    `catalog failure should fall back to non-orderable demo data: ${JSON.stringify(catalogFallbackState)}`,
  )
  assert(
    !mock ||
      (timeSlotFallbackState.hasTimeSlotAlert &&
        timeSlotFallbackState.hasDemoHint &&
        timeSlotFallbackState.hasDemoSlot &&
        !timeSlotFallbackState.hasEnglishTicketName &&
        timeSlotFallbackState.hasRealProduct &&
        timeSlotFallbackState.currentStepLabel === '选择时段' &&
        timeSlotFallbackState.createButtonDisabled),
    `time slot failure should fall back to non-orderable demo slots: ${JSON.stringify(timeSlotFallbackState)}`,
  )
  assert(!mock || emptyTimeSlotsState.hasEmptyTimeSlots, 'empty time slots should show booking empty state')
  assert(
    !mock || (
      !emptyTimeSlotsState.createButtonDisabled &&
      emptyTimeSlotsState.nextActionLabel.includes('选择时段') &&
      emptyTimeSlotsState.scrollTarget === 'slot'
    ),
    `empty time slots should guide visitors back to slot selection: ${JSON.stringify(emptyTimeSlotsState)}`,
  )
  assert(!mock || bookingStepState.initialStep === '填写信息', 'booking steps should point to account before registration')
  assert(!mock || bookingStepState.afterRegisterStep === '填写信息', 'booking steps should wait for passenger details after login')
  assert(!mock || bookingStepState.afterPassengersStep === '支付订单', 'booking steps should advance after passenger details')
  assert(
    !mock || (
      mobileBookingNextState.passengerActionEnabled &&
      mobileBookingNextState.passengerActionLabel.includes('填写出行人') &&
      mobileBookingNextState.passengerScrollTarget === 'passenger' &&
      mobileBookingNextState.readyActionEnabled &&
      mobileBookingNextState.readyActionLabel.includes('提交订单并支付')
    ),
    `mobile booking action should explain the next step: ${JSON.stringify(mobileBookingNextState)}`,
  )
  assert(!mock || desktopAuthActionState.loginLabel.includes('先登录'), 'desktop summary action should open login before auth')
  assert(
    !mock || (
      mobileAuthModalState.containerTop >= 0 &&
      mobileAuthModalState.containerBottom <= mobileAuthModalState.viewportHeight &&
      mobileAuthModalState.titleVisible &&
      mobileAuthModalState.switcherVisible &&
      mobileAuthModalState.canScroll &&
      mobileAuthModalState.overflowY === 'auto'
    ),
    `mobile auth modal should stay within viewport and scroll internally: ${JSON.stringify(mobileAuthModalState)}`,
  )
  assert(
    !mock || emptyTimeSlotsState.scrollWidth === emptyTimeSlotsState.clientWidth,
    'empty time slot state should not overflow horizontally',
  )
  assert(
    mobileTicketCardState.cardScrollWidth === mobileTicketCardState.cardClientWidth,
    'mobile ticket card should not overflow horizontally',
  )
  assert(
    mobileTicketCardState.contentWidth >= 120 && mobileTicketCardState.titleWidth >= 120,
    `mobile ticket card content should stay readable: ${JSON.stringify(mobileTicketCardState)}`,
  )
  assert(
    mobileTicketCardState.badgeContent === '"已选"' && !mobileTicketCardState.priceBadgeOverlap,
    `mobile selected badge should be labeled and not overlap price: ${JSON.stringify(mobileTicketCardState)}`,
  )
  assert(mobileDateStripState.chipCount >= 3, 'mobile date strip should render date chips')
  assert(mobileDateStripState.flexWrap === 'nowrap', 'mobile date strip should not wrap')
  assert(mobileDateStripState.sameRow, 'mobile date chips should stay on one row')
  assert(
    mobileDateStripState.scrollWidth === mobileDateStripState.clientWidth,
    'mobile date strip should not create page-level horizontal overflow',
  )
  assert(
    mobileBookingVisualState.hasBookingHeading &&
      mobileBookingVisualState.stickyBarVisible &&
      mobileBookingVisualState.hidesDesktopSummary,
    `mobile booking visual structure should match blueprint: ${JSON.stringify(mobileBookingVisualState)}`,
  )
  assert(
    !mock || (
      mobileBookingVisualState.mobilePassengerTriggerVisible &&
      mobileBookingVisualState.hidesPassengerHeaderTrigger &&
      mobileBookingVisualState.passengerManagerOpens
    ),
    `mobile passenger manager entry should be visible and functional: ${JSON.stringify(mobileBookingVisualState)}`,
  )
  assert(
    mobileBookingVisualState.actionWidth >= 128 && mobileBookingVisualState.pageFits,
    `mobile booking sticky action should fit without clipping: ${JSON.stringify(mobileBookingVisualState)}`,
  )
  assert(
    mobileBookingVisualState.stepsHeight > 0 &&
      mobileBookingVisualState.stepsHeight <= 96 &&
      mobileBookingVisualState.slotColumnCount === 2 &&
      mobileBookingVisualState.stepsScrollWidth === mobileBookingVisualState.stepsClientWidth &&
      mobileBookingVisualState.visibleStepTitleCount === 4,
    `mobile booking steps and slots should stay compact: ${JSON.stringify(mobileBookingVisualState)}`,
  )
  assert(
    mobileBookingVisualState.triggerInsideTopBar && mobileBookingVisualState.triggerIsButton,
    `mobile navigation trigger should stay usable inside the top bar: ${JSON.stringify(mobileBookingVisualState)}`,
  )
  const breakpointState = Object.fromEntries(bookingBreakpointStates.map((state) => [state.width, state]))
  assert(
    breakpointState[430].pageFits &&
      breakpointState[430].mobileBarDisplay === 'grid' &&
      breakpointState[430].mobilePassengerTriggerDisplay !== 'none' &&
      breakpointState[430].passengerHeaderTriggerDisplay === 'none' &&
      breakpointState[430].summaryDisplay === 'none' &&
      breakpointState[430].stepsHeight <= 96 &&
      breakpointState[430].slotColumnCount === 2 &&
      breakpointState[430].ticketTitleWidth >= 120,
    `430px booking layout should match mobile rules: ${JSON.stringify(breakpointState[430])}`,
  )
  for (const width of [640, 768, 900, 1230, 1440]) {
    assert(
      breakpointState[width].pageFits &&
        breakpointState[width].mobileBarDisplay === 'none' &&
        breakpointState[width].mobilePassengerTriggerDisplay === 'none' &&
        breakpointState[width].passengerHeaderTriggerDisplay !== 'none' &&
        breakpointState[width].summaryDisplay !== 'none' &&
        breakpointState[width].ticketTitleWidth >= 120 &&
        (width >= 992 || breakpointState[width].triggerDisplay !== 'none'),
      `${width}px booking layout should match tablet or desktop rules: ${JSON.stringify(breakpointState[width])}`,
    )
  }
  assert(
    !mock ||
      (desktopBookingVisualState.hasBookingHeading &&
        desktopBookingVisualState.hasReadinessList &&
        desktopBookingVisualState.hasWorkbenchGrid &&
        desktopBookingVisualState.hasSummaryCard &&
        desktopBookingVisualState.pageFits &&
        desktopBookingVisualState.readinessItemCount === 5 &&
        desktopBookingVisualState.readinessText.includes('下单前确认') &&
        desktopBookingVisualState.readinessText.includes('出行人') &&
        desktopBookingVisualState.summaryPosition === 'sticky'),
    `desktop booking visual structure should match blueprint: ${JSON.stringify(desktopBookingVisualState)}`,
  )
  assert(
    visitorShellState.hasVisitorShell &&
      visitorShellState.hasVisitorServiceLabel &&
      visitorShellState.hidesStatusStrip &&
      visitorShellState.hidesAdminMenuEntry &&
      visitorShellState.mobileNavigationExpands &&
      visitorShellState.mobileNavigationCloses,
    `visitor shell should not expose admin navigation: ${JSON.stringify(visitorShellState)}`,
  )
  assert(mobileTicketCardState.titleLineCount <= 2, 'mobile ticket card title should clamp to two lines')
  assert(
    mobileTicketCardState.text.includes('遇龙河成人票') &&
      !mobileTicketCardState.text.includes('Adult Ticket'),
    `mobile ticket card title should display localized ticket name: ${JSON.stringify(mobileTicketCardState)}`,
  )
  assert(
    mobileTicketCardState.hasFullTitle,
    `mobile ticket card should expose the full ticket name as title: ${JSON.stringify(mobileTicketCardState)}`,
  )
  assert(pageState.heading === '我的订单', 'orders page should be active after checkout')
  assert(
    paidPageState.hasPaymentSuccess &&
      paidPageState.hasPaymentSuccessResult &&
      paidPageState.hasStateCard &&
      paidPageState.hasTicketReadyCopy &&
      paidPageState.hasTicketRegion &&
      paidPageState.hasLocalizedTicketName &&
      paidPageState.hasNoEnglishTicketName,
    'paid order result should render',
  )
  assert(
    paidPageState.hasRefundAction &&
      (!mock || (paidPageState.hasRefundDeadline && paidPageState.hasRefundReason && paidPageState.refundModalFitsViewport)),
    `paid order detail should expose a mobile-safe self-refund confirmation: ${JSON.stringify(paidPageState)}`,
  )
  assert(
    paidPageState.scrollWidth === paidPageState.clientWidth,
    'mobile paid ticket codes should not overflow horizontally',
  )
  assert(
    desktopDetailState.detailCardVisible &&
      desktopDetailState.hasOrdersHeading &&
      desktopDetailState.hasWorkbenchGrid &&
      desktopDetailState.hasPaymentSuccessResult &&
      desktopDetailState.hasStateCard &&
      desktopDetailState.hasTicketRegion &&
      desktopDetailState.hasLocalizedTicketName &&
      desktopDetailState.hasNoEnglishTicketName,
    `desktop orders visual structure should render: ${JSON.stringify(desktopDetailState)}`,
  )
  assert(
    desktopDetailState.detailPosition === 'sticky',
    `desktop order detail card should stay sticky: ${JSON.stringify(desktopDetailState)}`,
  )
  assert(
    desktopDetailState.scrollWidth === desktopDetailState.clientWidth,
    'desktop order detail should not overflow horizontally',
  )
  assert(!mock || (paidPageState.hasMockOrder && paidPageState.hasMockTicket1 && paidPageState.hasMockTicket2), 'mock paid order and ticket codes should render')
  assert(!mock || (pageState.hasSecondOrder && pageState.hasCancelledSecondOrder), 'second order should render as cancelled')
  assert(
    !mock || (pageState.hidesCancelledStateActions && pageState.hasCancelledTicketCopy),
    `cancelled order detail should be read-only with clear ticket copy: ${JSON.stringify(pageState)}`,
  )
  assert(
    !mock ||
      (notPayablePaymentState &&
        notPayablePaymentState.hasPayFailure &&
        notPayablePaymentState.hasNotPayableMessage &&
        notPayablePaymentState.hasRefreshAction &&
        notPayablePaymentState.payButtonDisabled &&
        !notPayablePaymentState.hasRetryPayLabel),
    `ORDER_NOT_PAYABLE should block payment retry: ${JSON.stringify(notPayablePaymentState)}`,
  )
  assert(
    !mock ||
      (orderCardToneState &&
        orderCardToneState.pendingStatus === 'CREATED' &&
        orderCardToneState.pendingClass &&
        orderCardToneState.pendingAction &&
        orderCardToneState.paidStatus === 'PAID' &&
        orderCardToneState.paidClass &&
        orderCardToneState.paidAction &&
        orderCardToneState.cancelledStatus === 'CANCELLED' &&
        orderCardToneState.cancelledClass &&
        orderCardToneState.cancelledAction),
    `mobile order cards should expose status tone classes and action labels: ${JSON.stringify(orderCardToneState)}`,
  )
  assert(
    !mock ||
      (quotaPaymentState &&
        quotaPaymentState.hasPayFailure &&
        quotaPaymentState.hasQuotaMessage &&
        quotaPaymentState.hasRefreshAction &&
        quotaPaymentState.payButtonDisabled &&
        !quotaPaymentState.hasRetryPayLabel),
    `TIME_SLOT_QUOTA_NOT_ENOUGH should block payment retry: ${JSON.stringify(quotaPaymentState)}`,
  )
  assert(
    !mock ||
      (cancelNotAllowedState &&
        cancelNotAllowedState.hasCancelAction &&
        cancelNotAllowedState.hasCancelFailure &&
        cancelNotAllowedState.hasNotCancelableMessage &&
        cancelNotAllowedState.hasPayAction &&
        cancelNotAllowedState.hasRequestId &&
        !cancelNotAllowedState.hasCancelledStatus &&
        cancelNotAllowedState.stillPending),
    `ORDER_NOT_CANCELABLE should keep the order pending and actions visible: ${JSON.stringify(cancelNotAllowedState)}`,
  )
  if (mock) {
    assertDeepEqual(
      mock.state.orderErrors.filter((error) => error.endpoint === 'pay' && error.orderNo === 'ORD-E2E-002'),
      [{ code: 'ORDER_NOT_PAYABLE', endpoint: 'pay', orderNo: 'ORD-E2E-002' }],
      'not payable payment failure should use only ORDER_NOT_PAYABLE',
    )
    assertDeepEqual(
      mock.state.orderErrors.filter((error) => error.endpoint === 'pay' && error.orderNo === 'ORD-E2E-003'),
      [{ code: 'TIME_SLOT_QUOTA_NOT_ENOUGH', endpoint: 'pay', orderNo: 'ORD-E2E-003' }],
      'quota payment failure should use only TIME_SLOT_QUOTA_NOT_ENOUGH',
    )
    assertDeepEqual(
      mock.state.orderErrors.filter((error) => error.endpoint === 'cancel' && error.orderNo === 'ORD-E2E-004'),
      [{ code: 'ORDER_NOT_CANCELABLE', endpoint: 'cancel', orderNo: 'ORD-E2E-004' }],
      'cancel failure should use only ORDER_NOT_CANCELABLE',
    )
  }
  assert(!mock || orderStatusFilterState.paidFilterShowsDetailLoading, 'historical paid order should show detail loading state')
  assert(!mock || orderStatusFilterState.paidFilterShowsResult, 'historical paid order should show payment result')
  assert(
    !mock ||
      (orderDetailErrorState &&
        orderDetailErrorState.hasDetailError &&
        orderDetailErrorState.hasOrderNotFoundMessage &&
        orderDetailErrorState.hasRequestId &&
        orderDetailErrorState.hasRetryAction &&
        !orderDetailErrorState.hasStateActions &&
        !orderDetailErrorState.hasPayAction &&
        !orderDetailErrorState.hasCancelAction &&
        !orderDetailErrorState.hasPendingTicketAlert),
    `detail error should not expose state-changing actions: ${JSON.stringify(orderDetailErrorState)}`,
  )
  assert(
    !mock ||
      mock.state.orderErrors.some((error) =>
        error.code === 'ORDER_NOT_FOUND' &&
        error.endpoint === 'detail' &&
        error.orderNo === 'ORD-E2E-404'
      ),
    'order detail failure should use ORDER_NOT_FOUND',
  )
  assert(!mock || orderStatusFilterState.cancelledFilterShowsCancelledOnly, 'cancelled status filter should show cancelled orders only')
  assert(!mock || orderStatusFilterState.emptyStatusFilterCleared, 'empty status filter should return to populated order list')
  assert(!mock || orderStatusFilterState.searchCleared, 'clearing an empty order search should reset the search input')
  assert(!mock || orderStatusFilterState.workflowActiveStatus === 'CANCELLED', 'orders workflow should track active status filter')
  assert(!mock || orderStatusFilterState.workflowHasCancelledCopy, 'orders workflow should explain cancelled order boundary')
  assert(
    !mock || (
      orderStatusFilterState.refundedCardVisualState.hasRefundedTone &&
      orderStatusFilterState.refundedCardVisualState.keepsTicketImage
    ),
    'refunded order card should keep a subdued ticket image',
  )
  assert(
    !mock || orderStatusFilterState.scrollWidth === orderStatusFilterState.clientWidth,
    'order status filter should not overflow horizontally',
  )
  assert(mobileDetailActionState.position === 'fixed', 'mobile order detail actions should be fixed')
  assert(
    Math.abs(mobileDetailActionState.bottomGap) <= 1,
    `mobile order detail actions should sit at viewport bottom: ${JSON.stringify(mobileDetailActionState)}`,
  )
  assert(mobileDetailActionState.buttonCount >= 2, 'mobile order detail actions should expose pay and cancel buttons')
  assert(
    mobileDetailActionState.firstButtonWidth > 300 && mobileDetailActionState.secondButtonWidth > 300,
    'mobile order detail action buttons should span the drawer width',
  )
  assert(pageState.mobileDetailDrawerVisible, 'mobile order detail drawer should be visible after selecting an order')
  assert(!mock || pageState.hasCancelledStateCard, 'cancelled order detail should show read-only state card')
  assert(pageState.hasOrdersHeading && pageState.hasOrdersListCard && pageState.hasWorkflowStrip, 'mobile orders visual structure should render')
  assert(pageState.hasWorkflowCopy, 'mobile orders workflow guidance should render')
  assert(pageState.mobileOrdersVisible, 'mobile orders list should render at 390px')
  assert(pageState.mobileCardFits, 'mobile order card content should stay inside its card')
  assert(pageState.orderTableHidden, 'desktop orders table should be hidden at 390px')
  assert(pageState.scrollWidth === pageState.clientWidth, 'mobile viewport should not overflow horizontally')
}
