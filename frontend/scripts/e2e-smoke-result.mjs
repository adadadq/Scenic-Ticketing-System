import { assert } from './e2e-runtime-utils.mjs'

function maskPhone(phone) {
  return typeof phone === 'string' && phone.length >= 7
    ? `${phone.slice(0, 3)}****${phone.slice(-4)}`
    : null
}

export function finishE2eSmoke({
  adminBatchCheckInState,
  adminBatchUndoCheckInState,
  adminCheckInAuditExportState,
  adminCheckInFailureAuditExportState,
  adminCheckInFailureLogSearchState,
  adminDetailState,
  adminExportJobCreateState,
  adminFilterState,
  adminFullRefundState,
  adminIntermediateState,
  adminLoggedOutState,
  adminMobileState,
  adminPageSeparationState,
  adminPartialRefundState,
  adminRefundAuditExportState,
  adminRefundAuditState,
  adminRefundLogSearchState,
  adminReportState,
  adminReportTrendExportState,
  adminReportZeroFillState,
  adminReturnToVisitorState,
  adminShellState,
  adminTabletState,
  adminTicketsState,
  apiBaseUrl,
  bookingStepState,
  catalogFallbackState,
  desktopAuthActionState,
  desktopBookingVisualState,
  desktopDetailState,
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
  orderDetailErrorState,
  orderStatusFilterState,
  pageState,
  paidPageState,
  sessionFailureState,
  timeSlotFallbackState,
}) {
  assert(!mock || mock.state.adminAuthMeCount === 0, 'mock admin shell should not call real admin auth session endpoint')
  assert(
    adminLoggedOutState.hasLoginGate &&
      adminLoggedOutState.hasLoginCard &&
      adminLoggedOutState.hidesAdminHeader &&
      adminLoggedOutState.hidesAdminShell &&
      adminLoggedOutState.hidesAdminSider &&
      adminLoggedOutState.hidesAdminMobileTabbar &&
      adminLoggedOutState.hidesAccessCard &&
      adminLoggedOutState.hidesWorkbenchGrid,
    `admin logged-out shell should render the standalone login gate: ${JSON.stringify(adminLoggedOutState)}`,
  )
  assert(adminLoggedOutState.hidesOrderRows && adminLoggedOutState.hidesMaskedPhone, 'admin orders should stay hidden before admin login')
  assert(adminLoggedOutState.hidesReportRows && adminLoggedOutState.hidesReportTotals, 'admin reports should stay hidden before admin login')
  assert(adminLoggedOutState.hidesAuditSearchPanel && adminLoggedOutState.hidesAuditSearchRows, 'admin refund audit search should stay hidden before admin login')
  assert(
    adminLoggedOutState.hidesCheckInFailureAuditSearchPanel &&
    adminLoggedOutState.hidesCheckInFailureAuditSearchRows,
    'admin check-in failure audit search should stay hidden before admin login',
  )
  assert(adminShellState.heading === '后台运营工作台', 'admin shell should be reachable from admin route')
  assert(
    adminShellState.hasAdminShell && adminShellState.hasAdminOnlyNav && adminShellState.hasBackToVisitorAction,
    `admin shell should stay separated from visitor navigation: ${JSON.stringify(adminShellState)}`,
  )
  assert(
    adminReturnToVisitorState.hash === '#/visitor/booking' &&
      adminReturnToVisitorState.hasVisitorShell &&
      adminReturnToVisitorState.hidesAdminShell &&
      adminReturnToVisitorState.title === '购买门票',
    `admin shell return action should open the visitor booking shell: ${JSON.stringify(adminReturnToVisitorState)}`,
  )
  assert(
    adminShellState.hasAdminHeading &&
      adminShellState.hasWorkbenchGrid &&
      adminShellState.hasAuthenticatedWorkbench &&
      adminShellState.hasAuthenticatedAccessSummary &&
      adminShellState.hasOperationCards &&
      adminShellState.hasOperationsWorkflowStrip &&
      adminShellState.hasOperationsWorkflowCopy &&
      adminShellState.operationsWorkflowItemCount === 5 &&
      adminShellState.hasOperationsBoundaryStrip &&
      adminShellState.hasOperationsBoundaryCopy &&
      adminShellState.hasOverviewEntryCards,
    `admin shell should render the operations workspace skeleton: ${JSON.stringify(adminShellState)}`,
  )
  assert(
    adminShellState.scrollWidth === adminShellState.clientWidth,
    `admin desktop viewport should not overflow horizontally: ${JSON.stringify(adminShellState)}`,
  )
  assert(
    adminIntermediateState.scrollWidth === adminIntermediateState.clientWidth &&
      adminIntermediateState.hasAuthenticatedWorkbench &&
      !adminIntermediateState.hasAccessCard,
    `admin intermediate orders page should hide authenticated access card without overflow: ${JSON.stringify(adminIntermediateState)}`,
  )
  assert(
    adminTabletState.scrollWidth === adminTabletState.clientWidth,
    `admin tablet viewport should not overflow horizontally: ${JSON.stringify(adminTabletState)}`,
  )
  assert(
    adminTabletState.hasAuthenticatedWorkbench &&
      !adminTabletState.hasAccessCard &&
      adminTabletState.hasMobileOrderCards,
    `admin tablet orders page should keep authenticated layout and mobile order cards: ${JSON.stringify(adminTabletState)}`,
  )
  assert(adminShellState.hasAdminSession, 'admin shell should show mock admin session after login')
  assert(adminShellState.hasMockAuthMode, 'admin shell should run in mock auth mode by default')
  assert(adminShellState.hasCsrfBoundary && adminShellState.hasHttpOnlyBoundary, 'admin shell should show security boundaries')
  assert(adminShellState.hasAuditBoundary, 'admin shell should show audit boundary')
  assert(adminShellState.hasOverviewEntryCards, 'admin shell should expose separate admin page entry cards')
  assert(
    adminPageSeparationState.overview.hash === '#/admin' &&
      adminPageSeparationState.overview.heading === '后台运营工作台' &&
      adminPageSeparationState.overview.hasOverviewEntryCards &&
      !adminPageSeparationState.overview.hasReportWorkspace &&
      !adminPageSeparationState.overview.hasTicketsWorkspace &&
      !adminPageSeparationState.overview.hasOrdersWorkspace &&
      !adminPageSeparationState.overview.hasAuditWorkspace,
    `admin overview page should only show routing entry cards: ${JSON.stringify(adminPageSeparationState)}`,
  )
  assert(
      adminPageSeparationState.tickets.hash === '#/admin/tickets' &&
      adminPageSeparationState.tickets.heading === '票种管理' &&
      !adminPageSeparationState.tickets.hasAccessCard &&
      adminPageSeparationState.tickets.hasTicketsWorkspace &&
      !adminPageSeparationState.tickets.hasReportWorkspace &&
      !adminPageSeparationState.tickets.hasOrdersWorkspace &&
      !adminPageSeparationState.tickets.hasAuditWorkspace,
    `admin tickets page should only render the tickets workspace: ${JSON.stringify(adminPageSeparationState)}`,
  )
  assert(
    adminShellState.hasTicketsPanel &&
      adminShellState.hasTicketRows &&
      adminShellState.hasTicketActions &&
      adminShellState.hasTicketAuditBoundary &&
      adminTicketsState.hasCreatedTicket &&
      adminTicketsState.hasPriceEdited &&
      adminTicketsState.hasStatusChanged &&
      adminTicketsState.hasDeletedTicket &&
      adminTicketsState.hasAuditBoundary &&
      adminTicketsState.hasNoSensitiveFields,
    `admin tickets page should support mock ticket management safely: ${JSON.stringify({ adminShellState, adminTicketsState })}`,
  )
  assert(
      adminPageSeparationState.reports.hash === '#/admin/reports' &&
      adminPageSeparationState.reports.heading === '运营报表' &&
      !adminPageSeparationState.reports.hasAccessCard &&
      adminPageSeparationState.reports.hasReportWorkspace &&
      !adminPageSeparationState.reports.hasTicketsWorkspace &&
      !adminPageSeparationState.reports.hasOrdersWorkspace &&
      !adminPageSeparationState.reports.hasAuditWorkspace,
    `admin reports page should only render the reports workspace: ${JSON.stringify(adminPageSeparationState)}`,
  )
  assert(
    adminPageSeparationState.orders.hash === '#/admin/orders' &&
      adminPageSeparationState.orders.heading === '订单运营' &&
      !adminPageSeparationState.orders.hasReportWorkspace &&
      !adminPageSeparationState.orders.hasTicketsWorkspace &&
      adminPageSeparationState.orders.hasOrdersWorkspace &&
      !adminPageSeparationState.orders.hasAuditWorkspace,
    `admin orders page should only render the orders workspace: ${JSON.stringify(adminPageSeparationState)}`,
  )
  assert(
    adminPageSeparationState.audit.hash === '#/admin/audit' &&
      adminPageSeparationState.audit.heading === '审计导出' &&
      !adminPageSeparationState.audit.hasReportWorkspace &&
      !adminPageSeparationState.audit.hasTicketsWorkspace &&
      !adminPageSeparationState.audit.hasOrdersWorkspace &&
      adminPageSeparationState.audit.hasAuditWorkspace,
    `admin audit page should only render the audit workspace: ${JSON.stringify(adminPageSeparationState)}`,
  )
  assert(adminShellState.hasMockOrdersMode, 'admin shell should run order read-model in mock mode by default')
  assert(adminShellState.hasMockReportsMode, 'admin shell should run report read-model in mock mode by default')
  assert(adminShellState.hasMockAuditMode, 'admin shell should run refund audit search in mock mode by default')
  assert(adminShellState.hasMockExportJobsMode, 'admin shell should run export jobs in mock mode by default')
  assert(adminShellState.hasMockCheckInAuditMode, 'admin shell should run check-in audit export in mock mode by default')
  assert(adminShellState.hasMockCheckInFailureAuditMode, 'admin shell should run check-in failure audit search in mock mode by default')
  assert(adminShellState.hasOrderReadModel, 'admin shell should render admin order read-model rows')
  assert(adminShellState.hasBatchCheckInPanel, 'admin shell should render batch check-in panel')
  assert(adminShellState.hasBatchCheckInAction, 'admin shell should keep empty batch check-in action disabled')
  assert(adminShellState.hasBatchUndoCheckInPanel, 'admin shell should render batch undo check-in panel')
  assert(adminShellState.hasBatchUndoCheckInAction, 'admin shell should keep empty batch undo check-in action disabled')
  assert(adminShellState.hasReportReadModel, 'admin shell should render admin report read-model')
  assert(adminShellState.hasCsvExportAction, 'admin shell should expose admin order CSV export action after admin login')
  assert(adminShellState.hasXlsxExportAction, 'admin shell should expose admin order XLSX export action after admin login')
  assert(
    adminShellState.hasExportJobsPanel &&
      adminShellState.hasExportJobsBoundary &&
      adminShellState.hasExportJobRows &&
      adminShellState.hasExportJobCreateAction &&
      adminShellState.hasExportJobDownloadBoundary &&
      adminShellState.hasNoExportJobInternalFields,
    `admin shell should render async export jobs boundary and mock task rows: ${JSON.stringify(adminShellState)}`,
  )
  assert(
    adminExportJobCreateState.hasCreatedAlert &&
      adminExportJobCreateState.hasCreatedJobId &&
      adminExportJobCreateState.hasPendingStatus &&
      adminExportJobCreateState.keepsCreateBoundary &&
      adminExportJobCreateState.hasNoSensitiveExportPayload,
    `admin export job create should add a mock pending task without sensitive fields: ${JSON.stringify(adminExportJobCreateState)}`,
  )
  assert(adminShellState.hasCheckInAuditExportPanel, 'admin shell should render check-in audit export panel')
  assert(adminShellState.hasCheckInFailureAuditPanel, 'admin shell should render check-in failure audit search panel')
  assert(adminShellState.hasCheckInLogCsvExportAction, 'admin shell should expose check-in audit CSV export action after admin login')
  assert(adminShellState.hasCheckInLogXlsxExportAction, 'admin shell should expose check-in audit XLSX export action after admin login')
  assert(adminShellState.hasCheckInFailureLogCsvExportAction, 'admin shell should expose check-in failure audit CSV export action after admin login')
  assert(adminShellState.hasCheckInFailureLogXlsxExportAction, 'admin shell should expose check-in failure audit XLSX export action after admin login')
  assert(adminShellState.hasRefundLogCsvExportAction, 'admin shell should expose refund audit CSV export action after admin login')
  assert(adminShellState.hasRefundLogXlsxExportAction, 'admin shell should expose refund audit XLSX export action after admin login')
  assert(
    adminCheckInAuditExportState.hasCsvBlobType && adminCheckInAuditExportState.hasCsvFileName,
    'admin check-in audit CSV export should create a typed mock CSV download',
  )
  assert(
    adminCheckInAuditExportState.hasXlsxBlobType && adminCheckInAuditExportState.hasXlsxFileName,
    'admin check-in audit XLSX export should create a typed mock XLSX download',
  )
  assert(
    adminCheckInFailureAuditExportState.hasCsvBlobType && adminCheckInFailureAuditExportState.hasCsvFileName,
    'admin check-in failure audit CSV export should create a typed mock CSV download',
  )
  assert(
    adminCheckInFailureAuditExportState.hasXlsxBlobType && adminCheckInFailureAuditExportState.hasXlsxFileName,
    'admin check-in failure audit XLSX export should create a typed mock XLSX download',
  )
  assert(
    adminRefundAuditExportState.hasCsvBlobType && adminRefundAuditExportState.hasCsvFileName,
    'admin refund audit CSV export should create a typed mock CSV download',
  )
  assert(
    adminRefundAuditExportState.hasXlsxBlobType && adminRefundAuditExportState.hasXlsxFileName,
    'admin refund audit XLSX export should create a typed mock XLSX download',
  )
  assert(adminReportState.hasNetPaidAmount && adminReportState.hasTrendAmount, 'admin reports should render summary and daily trend metrics')
  assert(adminReportState.hasFourColumnSummaryMetrics, 'admin report summary metrics should keep four desktop columns')
  assert(adminReportState.hasDateFilters && adminReportState.hasZeroFillControl, 'admin reports should expose date filters and trend zero-fill control')
  assert(adminReportZeroFillState.hasZeroFillCopy && adminReportZeroFillState.hasHourlyZeroBucket, 'admin reports should render zero-filled trend buckets when enabled')
  assert(adminReportState.hasHourlyTrend && adminReportState.hasHourlyTrendAmount, 'admin reports should render hourly trend metrics')
  assert(adminReportState.hasMonthlyTrend && adminReportState.hasMonthlyTrendAmount, 'admin reports should render monthly trend metrics')
  assert(adminReportState.hasProductBreakdown, 'admin reports should render product breakdown rows')
  assert(adminReportState.hasNoEnglishTicketName, 'admin reports should not render legacy English ticket names')
  assert(adminReportState.hasPaymentReconciliationPanel, 'admin reports should render payment reconciliation summary')
  assert(adminReportState.hasPaymentReconciliationBoundary, 'admin payment reconciliation should show sensitive-field boundary')
  assert(adminReportState.hasReadOnlyBoundary, 'admin reports should show read-only boundary copy')
  assert(adminReportState.hasCsvExportAction, 'admin reports should expose CSV export action')
  assert(adminReportState.hasXlsxExportAction, 'admin reports should expose XLSX export action')
  assert(adminReportState.hasPaymentReconciliationCsvExportAction, 'admin reports should expose payment reconciliation CSV export action')
  assert(adminReportState.hasPaymentReconciliationXlsxExportAction, 'admin reports should expose payment reconciliation XLSX export action')
  assert(adminReportState.hasProductBreakdownCsvExportAction, 'admin reports should expose product breakdown CSV export action')
  assert(adminReportState.hasProductBreakdownXlsxExportAction, 'admin reports should expose product breakdown XLSX export action')
  assert(
    adminReportState.hasTrendExportScope &&
      adminReportState.hasDailyTrendCsvExportAction &&
      adminReportState.hasHourlyTrendCsvExportAction &&
      adminReportState.hasMonthlyTrendCsvExportAction &&
      adminReportState.hasDailyTrendXlsxExportAction &&
      adminReportState.hasHourlyTrendXlsxExportAction &&
      adminReportState.hasMonthlyTrendXlsxExportAction,
    'admin reports should expose trend CSV/XLSX export actions with scoped copy',
  )
  assert(
    adminReportTrendExportState.hasHourlyTrendCsvDownload,
    'admin hourly trend CSV export should create a typed mock CSV download',
  )
  assert(
    adminReportTrendExportState.hasHourlyTrendXlsxDownload,
    'admin hourly trend XLSX export should create a typed mock XLSX download',
  )
  assert(
    adminReportTrendExportState.hasPaymentReconciliationCsvDownload,
    'admin payment reconciliation CSV export should create a typed mock CSV download',
  )
  assert(
    adminReportTrendExportState.hasPaymentReconciliationXlsxDownload,
    'admin payment reconciliation XLSX export should create a typed mock XLSX download',
  )
  assert(
    adminReportTrendExportState.hasProductBreakdownCsvDownload,
    'admin product breakdown CSV export should create a typed mock CSV download',
  )
  assert(
    adminReportTrendExportState.hasProductBreakdownXlsxDownload,
    'admin product breakdown XLSX export should create a typed mock XLSX download',
  )
  assert(adminReportState.hasNoPhone && adminReportState.hasNoIdNumber && adminReportState.hasNoSqlText, 'admin reports should not expose sensitive fields or SQL text')
  assert(adminBatchCheckInState.hasPanel && adminBatchCheckInState.hasBoundary, 'admin batch check-in should render mutation boundary')
  assert(
    adminBatchCheckInState.hasResultSummary &&
    adminBatchCheckInState.hasSuccessRow &&
    adminBatchCheckInState.hasFailureRow,
    'admin batch check-in should render mixed success and business failure results',
  )
  assert(
    adminBatchCheckInState.hasNoInternalAdminId &&
    adminBatchCheckInState.hasNoOrderInternalId &&
    adminBatchCheckInState.hasNoFullPhone &&
    adminBatchCheckInState.hasNoSessionText &&
    adminBatchCheckInState.hasNoCsrfText &&
    adminBatchCheckInState.hasNoPasswordText &&
    adminBatchCheckInState.hasNoHashText &&
    adminBatchCheckInState.hasNoSqlText,
    'admin batch check-in should not expose sensitive fields',
  )
  assert(
    adminBatchUndoCheckInState.hasPanel &&
      adminBatchUndoCheckInState.hasBoundary &&
      adminBatchUndoCheckInState.hasReasonInput &&
      adminBatchUndoCheckInState.hasReasonEcho,
    'admin batch undo check-in should render mutation boundary and optional reason',
  )
  assert(
    adminBatchUndoCheckInState.hasResultSummary &&
    adminBatchUndoCheckInState.hasSuccessRow &&
    adminBatchUndoCheckInState.hasFailureRow,
    'admin batch undo check-in should render mixed success and business failure results',
  )
  assert(
    adminBatchUndoCheckInState.hasNoInternalAdminId &&
    adminBatchUndoCheckInState.hasNoOrderInternalId &&
    adminBatchUndoCheckInState.hasNoFullPhone &&
    adminBatchUndoCheckInState.hasNoSessionText &&
    adminBatchUndoCheckInState.hasNoCsrfText &&
    adminBatchUndoCheckInState.hasNoPasswordText &&
    adminBatchUndoCheckInState.hasNoHashText &&
    adminBatchUndoCheckInState.hasNoSqlText,
    'admin batch undo check-in should not expose sensitive fields',
  )
  assert(adminCheckInFailureLogSearchState.hasPanel && adminCheckInFailureLogSearchState.hasReadOnlyBoundary, 'admin check-in failure audit search should render read-only panel')
  assert(
    adminCheckInFailureLogSearchState.hasMissingTicketFailure && adminCheckInFailureLogSearchState.hasAlreadyUsedFailure,
    'admin check-in failure audit search should render business failure rows',
  )
  assert(adminCheckInFailureLogSearchState.hasUndoFailure, 'admin check-in failure audit search should render undo failure rows')
  assert(adminCheckInFailureLogSearchState.hasOperatorDisplay, 'admin check-in failure audit search should render operator display fields')
  assert(adminCheckInFailureLogSearchState.hasInvalidDateRangeError, 'admin check-in failure audit search should mirror API invalid date range error')
  assert(
    adminCheckInFailureLogSearchState.filterKeepsMissingTicketLog &&
    adminCheckInFailureLogSearchState.filterHidesAlreadyUsedLog,
    'admin check-in failure audit search filters should narrow rows',
  )
  assert(
    adminCheckInFailureLogSearchState.hasNoInternalAdminId &&
    adminCheckInFailureLogSearchState.hasNoOrderInternalId &&
    adminCheckInFailureLogSearchState.hasNoFullPhone &&
    adminCheckInFailureLogSearchState.hasNoIdNumber &&
    adminCheckInFailureLogSearchState.hasNoSessionText &&
    adminCheckInFailureLogSearchState.hasNoCsrfText &&
    adminCheckInFailureLogSearchState.hasNoPasswordText &&
    adminCheckInFailureLogSearchState.hasNoHashText &&
    adminCheckInFailureLogSearchState.hasNoSqlText,
    'admin check-in failure audit search should not expose sensitive fields',
  )
  assert(adminRefundLogSearchState.hasPanel && adminRefundLogSearchState.hasReadOnlyBoundary, 'admin refund audit search should render read-only panel')
  assert(adminRefundLogSearchState.hasFullRefundLog && adminRefundLogSearchState.hasPartialRefundLog, 'admin refund audit search should render full and partial logs')
  assert(adminRefundLogSearchState.hasOperatorDisplay, 'admin refund audit search should render operator display fields')
  assert(adminRefundLogSearchState.hasInvalidDateRangeError, 'admin refund audit search should mirror API invalid date range error')
  assert(adminRefundLogSearchState.filterKeepsPartialLog && adminRefundLogSearchState.filterHidesFullLog, 'admin refund audit search filters should narrow rows')
  assert(
    adminRefundLogSearchState.hasNoInternalAdminId &&
    adminRefundLogSearchState.hasNoFullPhone &&
    adminRefundLogSearchState.hasNoIdNumber &&
    adminRefundLogSearchState.hasNoSessionText &&
    adminRefundLogSearchState.hasNoCsrfText &&
    adminRefundLogSearchState.hasNoPasswordText &&
    adminRefundLogSearchState.hasNoHashText &&
    adminRefundLogSearchState.hasNoSqlText,
    'admin refund audit search should not expose sensitive fields',
  )
  assert(adminFullRefundState.canSubmit && adminFullRefundState.hasBoundary, 'admin full refund should expose guarded mutation action')
  assert(adminFullRefundState.hasReasonInput && adminFullRefundState.hasSuccess, 'admin full refund should submit optional reason and render success')
  assert(adminFullRefundState.hasRefundedStatus && adminFullRefundState.disablesAfterRefund, 'admin full refund should refresh order state and disable duplicate refund')
  assert(adminFullRefundState.hasAuditLog && adminFullRefundState.globalAuditUpdated, 'admin full refund should append order and global audit logs')
  assert(
    adminFullRefundState.hasNoInternalAdminId &&
    adminFullRefundState.hasNoFullPhone &&
    adminFullRefundState.hasNoSqlText,
    'admin full refund should not expose sensitive fields',
  )
  assert(adminPartialRefundState.disablesBeforeSelection && adminPartialRefundState.hasBoundary, 'admin partial refund should require an item selection and show mutation boundary')
  assert(adminPartialRefundState.hasItemSelector && adminPartialRefundState.hasSuccess, 'admin partial refund should select items and render success')
  assert(adminPartialRefundState.hasPartialStatus && adminPartialRefundState.refundedItemDisabled, 'admin partial refund should refresh order state and disable refunded items')
  assert(adminPartialRefundState.hasAuditLog && adminPartialRefundState.globalAuditUpdated, 'admin partial refund should append order and global audit logs')
  assert(
    adminPartialRefundState.hasNoInternalAdminId &&
    adminPartialRefundState.hasNoFullPhone &&
    adminPartialRefundState.hasNoSqlText,
    'admin partial refund should not expose sensitive fields',
  )
  assert(adminShellState.hasMaskedPhone && adminShellState.hasNoFullMockPhone, 'admin shell should only expose masked buyer phone')
  assert(adminShellState.hasDisabledFutureActions, 'admin shell future actions should stay disabled')
  assert(adminShellState.hasNoLegacyRefundEntry, 'admin shell should not expose legacy refund entry')
  assert(adminShellState.orderFutureActionsDisabled, 'admin order future actions must stay disabled')
  assert(adminFilterState.createdOrderVisible && adminFilterState.hidesPaidOrderByStatus, 'admin order status filter should narrow read-model rows')
  assert(adminFilterState.orderNoFilterVisible && adminFilterState.hidesOtherOrderByOrderNo, 'admin order number filter should narrow read-model rows')
  assert(adminFilterState.partialRefundOrderVisible && adminFilterState.hidesPaidOrder, 'admin payment status filter should narrow read-model rows')
  assert(adminFilterState.phoneFilterOrderVisible && adminFilterState.hidesOtherMaskedPhone, 'admin buyer phone filter should accept masked input and narrow read-model rows')
  assert(adminRefundAuditState.hasPartialLog && adminRefundAuditState.hasReason, 'admin refund audit panel should render partial refund log')
  assert(adminRefundAuditState.hasRequestId && adminRefundAuditState.hasOperatorDisplay, 'admin refund audit panel should render traceable operator and request id')
  assert(adminRefundAuditState.hasReadOnlyBoundary, 'admin refund audit panel should show read-only boundary')
  assert(adminRefundAuditState.hasNoInternalAdminId && adminRefundAuditState.hasNoFullPhone && adminRefundAuditState.hasNoSqlText, 'admin refund audit panel should not expose sensitive fields')
  assert(adminDetailState.hasTicketCode && adminDetailState.hasReadOnlyBoundary, 'admin detail drawer should show read-only ticket details')
  assert(adminDetailState.hasDetailSummaryCard, 'admin detail drawer should render mutation-oriented summary card')
  assert(adminDetailState.hasNoEnglishTicketName, 'admin detail drawer should not render legacy English ticket names')
  assert(adminDetailState.hasMaskedPhone && adminDetailState.hasNoFullPhone, 'admin detail drawer should only expose masked buyer phone')
  assert(adminDetailState.hasRefundAuditEmptyState, 'admin detail drawer should show empty refund audit state for orders without logs')
  assert(adminDetailState.hasCheckInAction, 'admin detail drawer should expose check-in for unused tickets')
  assert(adminDetailState.hasFullRefundAction && adminDetailState.hasRefundBoundary && adminDetailState.hasRefundStatePath, 'admin detail drawer should expose full refund before ticket use')
  assert(adminDetailState.hasCheckInSuccess && adminDetailState.hasUsedTicketState, 'admin detail check-in should update mock ticket state')
  assert(adminDetailState.disablesCheckedInAction, 'admin detail check-in action should disable after ticket is used')
  assert(adminDetailState.disablesRefundAfterCheckIn, 'admin detail refund action should disable after ticket is used')
  assert(
    adminMobileState.scrollWidth === adminMobileState.clientWidth,
    `admin mobile viewport should not overflow horizontally: ${JSON.stringify(adminMobileState)}`,
  )
  assert(
      adminMobileState.hasWorkbenchGrid &&
      adminMobileState.hasMobileTabbar &&
      adminMobileState.mobileTabbarLabels.join('|') === '工作台|票种|报表|订单|审计' &&
      adminMobileState.hashAfterMobileOrderTab === '#/admin/orders' &&
      adminMobileState.activeMobileTabLabel === '订单' &&
      adminMobileState.hasOrderAnchor &&
      adminMobileState.hasMobileOrderCards,
    `admin mobile orders page should keep responsive tab navigation and order cards: ${JSON.stringify(adminMobileState)}`,
  )

  const mockDiagnostics = mock
    ? {
        createOrderItemCount: mock.state.createOrderBody?.items?.length ?? 0,
        createOrderSubmitted: Boolean(mock.state.createOrderBody),
        csrfFetchCount: mock.state.csrfFetchCount,
        csrfHeaderCount: mock.state.csrfHeaders.length,
        idempotencyKeyCount: mock.state.idempotencyKeys.length,
        loginBodyCount: mock.state.loginBodies.length,
        orderErrorCount: mock.state.orderErrors.length,
        paymentAttemptCount: mock.state.paymentAttempts.length,
        rateLimitedLoginUsernameCount: mock.state.rateLimitedLoginUsernames.size,
        registerBodyCount: mock.state.registerBodies.length,
        registerConflictPhoneCount: mock.state.registerConflictPhones.size,
      }
    : null

  console.log(`E2E smoke passed (${mock ? 'mock API' : 'real API proxy'})`)
  console.log(JSON.stringify({
    apiBaseUrl,
    adminDetailState,
    adminExportJobCreateState,
    adminFilterState,
    adminFullRefundState,
    adminIntermediateState,
    adminPartialRefundState,
    adminLoggedOutState,
    adminMobileState,
    adminPageSeparationState,
    adminReportState,
    adminRefundAuditState,
    adminRefundLogSearchState,
    adminShellState,
    adminTabletState,
    adminTicketsState,
    adminAuthMeCount: mock?.state.adminAuthMeCount,
    bookingStepState,
    catalogFallbackState,
    mockDiagnostics,
    sessionFailureState,
    loggedOutOrdersState,
    mobileDateStripState,
    desktopBookingVisualState,
    desktopAuthActionState,
    mobileBookingVisualState,
    mobileTicketCardState,
    mobileDetailActionState,
    orderDetailErrorState,
    desktopDetailState,
    emptyOrdersState,
    emptyTimeSlotsState,
    orderStatusFilterState,
    paidPageState,
    pageState,
    timeSlotFallbackState,
    visitor: { name: e2eVisitorName, phoneMasked: maskPhone(e2ePhone) },
  }, null, 2))
}
