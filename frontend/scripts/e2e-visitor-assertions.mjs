import {
  assert,
  assertDeepEqual,
} from './e2e-runtime-utils.mjs'

export function assertVisitorE2eState({
  bookingStepState,
  cancelNotAllowedState,
  catalogFallbackState,
  databaseHealthFailureState,
  desktopAuthActionState,
  desktopBookingVisualState,
  desktopDetailState,
  e2eIdNumber,
  e2ePhone,
  e2eVisitorName,
  emptyOrdersState,
  emptyTimeSlotsState,
  loggedOutOrdersState,
  mobileBookingVisualState,
  mobileDateStripState,
  mobileDetailActionState,
  mobileTicketCardState,
  mock,
  notPayablePaymentState,
  orderDetailErrorState,
  orderStatusFilterState,
  pageState,
  paidPageState,
  quotaPaymentState,
  sessionFailureState,
  timeSlotFallbackState,
}) {
  const expectedOrderBody = {
    buyerName: e2eVisitorName,
    buyerPhone: e2ePhone,
    items: [{ productId: 1, timeSlotId: 100, visitDate: '2026-07-01', quantity: 2 }],
  }
  const expectedRegisterBody = {
    idNumber: e2eIdNumber,
    idType: 'ID_CARD',
    phone: e2ePhone,
    visitorName: e2eVisitorName,
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
    assertDeepEqual(mock.state.loginBodies, [{ phone: e2ePhone }, { phone: e2ePhone }], 'visitor login bodies')
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
    assert(mock.state.csrfHeaders.length >= 16, 'login rate limit, register, create, pay retry, blocked payment branches, cancels, and logout should all be CSRF-protected')
    assertDeepEqual(
      mock.state.csrfHeaders,
      ['e2e-csrf-1', 'e2e-csrf-1', 'e2e-csrf-2', 'e2e-csrf-2', 'e2e-csrf-3', 'e2e-csrf-3', 'e2e-csrf-3', 'e2e-csrf-4', 'e2e-csrf-4', 'e2e-csrf-4', 'e2e-csrf-5', 'e2e-csrf-5', 'e2e-csrf-5', 'e2e-csrf-6', 'e2e-csrf-6', 'e2e-csrf-6', 'e2e-csrf-7'],
      'session-bound CSRF rotation',
    )
  }

  assert(
    !mock ||
      (loggedOutOrdersState.hasAuthError &&
        loggedOutOrdersState.canOpenLogin &&
        loggedOutOrdersState.canReturnBooking &&
        !loggedOutOrdersState.hasEmptyText),
    `logged-out orders should show auth error instead of empty state: ${JSON.stringify(loggedOutOrdersState)}`,
  )
  assert(!mock || (emptyOrdersState.hasEmptyText && emptyOrdersState.canOpenBooking), 'empty orders should offer booking action')
  assert(!mock || emptyOrdersState.mobileOrdersVisible, 'empty orders mobile list should render at 390px')
  assert(
    !mock ||
      (databaseHealthFailureState.hasDatabaseError &&
        databaseHealthFailureState.hasDiagnosticCode &&
        databaseHealthFailureState.hasDiagnosticRequestId &&
        databaseHealthFailureState.hasLoginEntry &&
        databaseHealthFailureState.hasTicketCard),
    `database health failure should not block visitor flow shell: ${JSON.stringify(databaseHealthFailureState)}`,
  )
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
        timeSlotFallbackState.hasRealProduct &&
        timeSlotFallbackState.currentStepLabel === '选择时段' &&
        timeSlotFallbackState.createButtonDisabled),
    `time slot failure should fall back to non-orderable demo slots: ${JSON.stringify(timeSlotFallbackState)}`,
  )
  assert(!mock || emptyTimeSlotsState.hasEmptyTimeSlots, 'empty time slots should show booking empty state')
  assert(!mock || emptyTimeSlotsState.createButtonDisabled, 'empty time slots should disable order creation')
  assert(!mock || bookingStepState.initialStep === '填写信息', 'booking steps should point to real-name before registration')
  assert(!mock || bookingStepState.afterRegisterStep === '支付订单', 'booking steps should advance to payment after registration')
  assert(!mock || desktopAuthActionState.loginLabel.includes('先登录'), 'desktop summary action should open login before auth')
  assert(!mock || desktopAuthActionState.registerLabel.includes('去实名登记'), 'desktop summary action should open real-name after temporary login')
  assert(
    !mock || emptyTimeSlotsState.scrollWidth === emptyTimeSlotsState.clientWidth,
    'empty time slot state should not overflow horizontally',
  )
  assert(
    mobileTicketCardState.cardScrollWidth === mobileTicketCardState.cardClientWidth,
    'mobile ticket card should not overflow horizontally',
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
    mobileBookingVisualState.actionWidth >= 128 && mobileBookingVisualState.pageFits,
    `mobile booking sticky action should fit without clipping: ${JSON.stringify(mobileBookingVisualState)}`,
  )
  assert(
    !mock ||
      (desktopBookingVisualState.hasBookingHeading &&
        desktopBookingVisualState.hasReadinessList &&
        desktopBookingVisualState.hasWorkbenchGrid &&
        desktopBookingVisualState.hasSummaryCard &&
        desktopBookingVisualState.pageFits &&
        desktopBookingVisualState.readinessItemCount === 4 &&
        desktopBookingVisualState.readinessText.includes('下单检查') &&
        desktopBookingVisualState.summaryPosition === 'sticky'),
    `desktop booking visual structure should match blueprint: ${JSON.stringify(desktopBookingVisualState)}`,
  )
  assert(mobileTicketCardState.titleLineCount <= 2, 'mobile ticket card title should clamp to two lines')
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
      paidPageState.hasTicketRegion,
    'paid order result should render',
  )
  assert(
    paidPageState.hidesStateActions,
    `paid order detail should hide state-changing actions: ${JSON.stringify(paidPageState)}`,
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
      desktopDetailState.hasTicketRegion,
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
  assert(pageState.hasCancelledStateCard, 'cancelled order detail should show read-only state card')
  assert(pageState.hasOrdersHeading && pageState.hasOrdersListCard && pageState.hasWorkflowStrip, 'mobile orders visual structure should render')
  assert(pageState.hasWorkflowCopy, 'mobile orders workflow guidance should render')
  assert(pageState.mobileOrdersVisible, 'mobile orders list should render at 390px')
  assert(pageState.mobileCardFits, 'mobile order card content should stay inside its card')
  assert(pageState.orderTableHidden, 'desktop orders table should be hidden at 390px')
  assert(pageState.scrollWidth === pageState.clientWidth, 'mobile viewport should not overflow horizontally')
}
