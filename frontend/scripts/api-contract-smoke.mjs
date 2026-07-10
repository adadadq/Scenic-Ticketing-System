import {
  assert,
  assertContains,
  assertEndpoint,
  assertFetchOptions,
  assertHeadersSetInBranch,
  assertNotContains,
  assertThrows,
  findFunction,
  loadRuntimeFunctions,
  readStoreZipEntryText,
} from './api-contract-smoke-utils.mjs'
import { runApiEndpointContracts } from './api-contract-endpoint-smoke.mjs'
import { loadApiContractSourceBundle } from './api-contract-source-bundle.mjs'
import { runSharedApiTypeContracts } from './api-contract-type-smoke.mjs'

await runSharedApiTypeContracts()

const {
  endpoints,
  searchBuilders,
  client,
  scenicText,
  bookingAdapters,
  bookingFlow,
  bookingWorkbench,
  bookingHeader,
  bookingReadinessList,
  bookingStepsCard,
  ticketSelector,
  dateSlotPicker,
  bookingCss,
  orderAdapters,
  ordersWorkbench,
  ordersHeader,
  ordersListCard,
  orderWorkflowStrip,
  orderDetailSurfaces,
  orderDetailSections,
  ordersCss,
  adminAuthQueries,
  adminAuthController,
  adminOrderQueries,
  adminOrderMockData,
  adminOrderMockSeeds,
  adminAppShell,
  adminWorkbench,
  adminOrdersPanel,
  adminAuditPanel,
  adminOrderDisplay,
  adminBatchCheckInPanel,
  adminBatchUndoCheckInPanel,
  adminOrderDetailErrorDetails,
  adminOrderDetailDrawer,
  adminOrderDetailSummary,
  adminOrderItemsTable,
  adminOrderRefundPanels,
  adminRefundAuditPanel,
  adminCheckInAuditExportPanel,
  adminExportJobsPanel,
  adminExportJobDisplay,
  adminExportJobCreateToolbar,
  adminExportJobTable,
  adminExportJobQueries,
  adminExportJobMockData,
  adminCheckInAuditExportCsv,
  adminCheckInAuditExportXlsx,
  adminExportErrorDetails,
  adminCheckInAuditCsvExportErrorDetails,
  adminCheckInAuditExportErrorDetails,
  adminCheckInFailureLogQueries,
  adminCheckInFailureLogMockData,
  adminCheckInFailureAuditExportCsv,
  adminCheckInFailureAuditExportXlsx,
  adminCheckInFailureLogPanel,
  adminCheckInFailureAuditDisplay,
  adminCheckInFailureAuditCsvErrorDetails,
  adminCheckInFailureAuditErrorDetails,
  adminCheckInFailureAuditXlsxErrorDetails,
  adminCheckInFailureAuditTable,
  adminCheckInFailureAuditToolbar,
  adminRefundLogQueries,
  adminRefundLogMockData,
  adminRefundAuditExportCsv,
  adminRefundAuditExportXlsx,
  adminRefundLogPanel,
  adminRefundAuditDisplay,
  adminRefundAuditCsvErrorDetails,
  adminRefundAuditErrorDetails,
  adminRefundAuditXlsxErrorDetails,
  adminRefundAuditTable,
  adminRefundAuditToolbar,
  adminReportQueries,
  adminReportMockData,
  adminReportExportCsv,
  adminReportExportsHook,
  adminReportXlsxWorkbook,
  adminReportsPanel,
  adminReportDisplay,
  adminReportCsvErrorDetails,
  adminPaymentReconciliationPanel,
  adminReportProductPanel,
  adminReportSummaryMetrics,
  adminReportTrendExportBar,
  adminReportTrendPanel,
  adminReportXlsxErrorDetails,
  appCss,
  appLayoutCss,
  adminCss,
  adminReportCss,
  adminReportSurfaceText,
  adminOrderMockSurfaceText,
  adminOrderDetailSurfaceText,
  adminRefundAuditSurfaceText,
} = await loadApiContractSourceBundle()
const { requests } = runApiEndpointContracts({ client, endpoints, searchBuilders })

assertContains(client.text, "const DEFAULT_CSRF_HEADER = 'x-csrf-token'", 'default CSRF header')
assertContains(client.text, "const IDEMPOTENCY_HEADER = 'Idempotency-Key'", 'idempotency header')
assertContains(bookingAdapters.text, 'parseCatalogPrice(product.originalPrice)', 'catalog original price mapping')
assertContains(bookingAdapters.text, 'parseCatalogPrice(product.salePrice)', 'catalog sale price mapping')
assertContains(bookingAdapters.text, 'mapSlotLabel(slot)', 'time slot label mapping')
assertContains(bookingFlow.text, 'buyerName: visitor.visitorName', 'order create buyer name')
assertContains(bookingFlow.text, 'buyerPhone: visitor.phone', 'order create buyer phone')
assertContains(bookingFlow.text, 'items: selectedTicketSelections.map', 'order create supports multiple ticket selections')
assertContains(bookingFlow.text, 'productId: product.productId', 'order create item product id')
assertContains(bookingFlow.text, 'getSelectedTimeSlotId(product, selectedSlot)', 'order create item time slot id')
assertContains(bookingFlow.text, 'visitDate: selectedSlot.visitDate ?? selectedVisitDate', 'order create visit date fallback')
assertContains(bookingFlow.text, 'quantity', 'order create quantity')
assertContains(bookingFlow.text, "export type BookingReadinessStatus = 'done' | 'active' | 'blocked'", 'booking readiness status contract')
assertContains(bookingFlow.text, 'getBookingReadinessItems', 'booking readiness workflow helper')
assertContains(bookingFlow.text, '票务服务暂时不稳定', 'booking readiness must explain product fallback')
assertContains(bookingFlow.text, '预约时段暂时不稳定', 'booking readiness must explain slot fallback')
assertContains(bookingFlow.text, '请先注册账号', 'booking readiness must explain account gate')
assertContains(bookingHeader.text, 'className="page-heading booking-heading"', 'booking page heading visual boundary class')
assertContains(bookingHeader.text, 'className="booking-heading-action"', 'booking page orders action visual class')
assertContains(bookingWorkbench.text, 'className="booking-workbench-grid"', 'booking workbench responsive grid class')
assertContains(bookingWorkbench.text, 'getBookingReadinessItems(bookingGateState)', 'booking workbench must derive readiness from gate state')
assertContains(bookingReadinessList.text, 'className="booking-readiness"', 'booking readiness workflow list class')
assertContains(bookingReadinessList.text, '确认信息后再提交', 'booking readiness list must name pre-submit guidance')
assertContains(bookingStepsCard.text, 'className="step-card booking-step-card"', 'booking steps visual hierarchy class')
assertContains(ticketSelector.text, 'workspace-card booking-selector-card', 'booking ticket selector visual class')
assertContains(dateSlotPicker.text, 'workspace-card booking-slot-card', 'booking date and slot visual class')
assertContains(bookingCss.text, '.booking-heading', 'booking css must include page-specific heading rules')
assertContains(bookingCss.text, 'grid-template-columns: minmax(0, 1fr) minmax(128px, 42vw)', 'booking mobile action bar must reserve button width')
assertContains(bookingCss.text, '.ticket-table .ant-table-row-selected > td', 'booking ticket table selected state must be visible')
assertContains(bookingCss.text, '.booking-summary-card .pay-button', 'booking summary primary action sizing')
assertContains(bookingCss.text, '.booking-readiness-list', 'booking readiness list styling')
assertContains(ordersHeader.text, 'className="page-heading orders-heading"', 'orders page heading visual boundary class')
assertContains(ordersHeader.text, 'className="orders-heading-action"', 'orders page refresh action visual class')
assertContains(ordersWorkbench.text, 'className="orders-workbench-grid"', 'orders workbench responsive grid class')
assertContains(ordersListCard.text, 'workspace-card orders-card orders-list-card', 'orders list visual class')
assertContains(ordersListCard.text, '<OrderWorkflowStrip', 'orders list must expose workflow guidance')
assertContains(orderWorkflowStrip.text, 'data-active-status={statusFilter}', 'orders workflow must expose active status for smoke checks')
assertContains(orderWorkflowStrip.text, '筛选只改变当前列表，不会影响订单。', 'orders workflow must explain filters do not mutate order state')
assertContains(orderWorkflowStrip.text, '已支付订单不再显示取消入口', 'orders workflow must explain paid order read-only action boundary')
assertContains(orderDetailSurfaces.text, 'summary-card order-detail-card orders-detail-card-shell', 'orders detail visual class')
assertContains(orderDetailSections.text, 'className="order-detail-header"', 'orders detail header visual boundary class')
assertContains(orderDetailSections.text, 'OrderDetailStateCard', 'orders detail must expose status guidance card')
assertContains(orderDetailSections.text, '票码生成后可在详情中查看', 'orders detail state card must avoid premature ticket display')
assertContains(orderDetailSections.text, '已取消订单不会生成入园票码', 'orders detail state card must explain cancelled ticket boundary')
assertContains(orderDetailSections.text, '订单状态可能已更新，请刷新后再继续操作。', 'orders detail state card must explain blocked payment refresh')
assertContains(ordersCss.text, '.orders-heading', 'orders css must include page-specific heading rules')
assertContains(ordersCss.text, '.orders-table .ant-table-thead > tr > th', 'orders table header state must be visible')
assertContains(ordersCss.text, '.orders-workflow-strip', 'orders workflow strip styling')
assertContains(ordersCss.text, '.order-detail-state-card', 'orders detail state card styling')
assertContains(ordersCss.text, '.mobile-order-detail-drawer .order-detail-actions', 'orders mobile detail action bar must stay fixed')
assertContains(orderAdapters.text, 'orderStatusMeta[order.orderStatus]', 'order status mapping')
assertContains(orderAdapters.text, 'parseOrderAmount(order.payableAmount)', 'order amount mapping')
assertContains(orderAdapters.text, 'maskPhone(order.buyerPhone)', 'order buyer phone masking')
assertContains(adminAuthQueries.text, "error.code === 'ADMIN_AUTH_REQUIRED'", 'admin auth required handling')
assertContains(adminAuthQueries.text, "error.code === 'ADMIN_FORBIDDEN'", 'admin forbidden handling')
assertContains(adminAuthQueries.text, 'queryClient.setQueryData(authQueryKeys.me, null)', 'admin login clears visitor session cache')
assertContains(adminAuthQueries.text, "queryKey: ['orders']", 'admin auth resets visitor orders')
assertContains(adminAuthController.text, "export type AdminAuthMode = 'api'", 'admin auth is API-only')
assertContains(adminAuthController.text, "const adminAuthMode: AdminAuthMode = 'api'", 'admin auth defaults to API')
assertContains(adminAuthController.text, 'logoutError: logoutMutation.error', 'admin logout error exposure')
assertContains(adminOrderQueries.text, 'VITE_ADMIN_ORDERS_MODE', 'admin orders mode env')
assertContains(adminOrderQueries.text, "import.meta.env.VITE_ADMIN_ORDERS_MODE === 'mock' ? 'mock' : 'api'", 'admin orders default to API')
assertContains(adminOrderQueries.text, "['admin-orders', mode, 'list'", 'admin orders query key namespace')
assertContains(adminOrderQueries.text, "if (adminOrdersMode === 'api')", 'admin orders API mode branch')
assertContains(adminOrderQueries.text, 'adminOrdersApi.list(normalizedParams)', 'admin orders list API client')
assertContains(adminOrderQueries.text, 'adminOrdersApi.detail(normalizedOrderNo)', 'admin orders detail API client')
assertContains(adminOrderQueries.text, 'adminOrdersApi.refundLogs(normalizedOrderNo)', 'admin refund audit logs API client')
assertContains(adminRefundLogQueries.text, 'VITE_ADMIN_REFUND_LOGS_MODE', 'admin refund audit search mode env')
assertContains(adminRefundLogQueries.text, "import.meta.env.VITE_ADMIN_REFUND_LOGS_MODE === 'mock' ? 'mock' : 'api'", 'admin refund audit search defaults to API')
assertContains(adminRefundLogQueries.text, "['admin-refund-logs', mode, 'list'", 'admin refund audit search query key namespace')
assertContains(adminRefundLogQueries.text, 'adminRefundAuditLogsApi.list(normalizedParams)', 'admin refund audit search API client')
assertContains(adminRefundLogQueries.text, 'listMockAdminRefundAuditLogSearch(normalizedParams)', 'admin refund audit search mock client')
assertContains(adminRefundAuditExportCsv.text, 'adminRefundAuditLogExportsApi.csv(normalizedParams)', 'admin refund audit CSV API client')
assertContains(adminRefundAuditExportCsv.text, 'listMockAdminRefundAuditCsvRows(normalizedParams)', 'admin refund audit CSV mock client')
assertContains(adminRefundAuditExportCsv.text, 'buildAdminRefundAuditCsvText', 'admin refund audit CSV mock builder')
assertContains(adminRefundAuditExportCsv.text, 'admin-refund-logs-${dateFrom}-${dateTo}.csv', 'admin refund audit CSV mock file name')
assertContains(adminRefundAuditExportXlsx.text, 'adminRefundAuditLogExportsApi.xlsx(normalizedParams)', 'admin refund audit XLSX API client')
assertContains(adminRefundAuditExportXlsx.text, 'listMockAdminRefundAuditLogExportRows(normalizedParams)', 'admin refund audit XLSX mock client')
assertContains(adminRefundAuditExportXlsx.text, 'buildAdminRefundAuditLogsXlsxBlob', 'admin refund audit XLSX mock builder')
assertContains(adminRefundAuditExportXlsx.text, 'inlineStr', 'admin refund audit XLSX writes string cells')
assertContains(adminRefundAuditExportXlsx.text, 'admin-refund-logs-${dateFrom}-${dateTo}.xlsx', 'admin refund audit XLSX mock file name')
assertContains(adminCheckInAuditExportXlsx.text, 'VITE_ADMIN_CHECK_IN_LOGS_MODE', 'admin check-in audit export mode env')
assertContains(adminCheckInAuditExportXlsx.text, "import.meta.env.VITE_ADMIN_CHECK_IN_LOGS_MODE === 'mock' ? 'mock' : 'api'", 'admin check-in audit export defaults to API')
assertContains(adminCheckInAuditExportXlsx.text, 'adminCheckInAuditLogExportsApi.xlsx(normalizedParams)', 'admin check-in audit XLSX API client')
assertContains(adminCheckInAuditExportXlsx.text, 'listMockAdminCheckInAuditLogExportRows(normalizedParams)', 'admin check-in audit XLSX mock client')
assertContains(adminCheckInAuditExportXlsx.text, 'addMockAdminCheckInAuditLog', 'admin check-in audit mock append helper')
assertContains(adminCheckInAuditExportXlsx.text, 'buildAdminCheckInAuditLogsXlsxBlob', 'admin check-in audit XLSX mock builder')
assertContains(adminCheckInAuditExportXlsx.text, 'inlineStr', 'admin check-in audit XLSX writes string cells')
assertContains(adminCheckInAuditExportXlsx.text, 'admin-check-in-logs-${dateFrom}-${dateTo}.xlsx', 'admin check-in audit XLSX mock file name')
assertContains(adminCheckInAuditExportCsv.text, 'adminCheckInAuditLogExportsApi.csv(normalizedParams)', 'admin check-in audit CSV API client')
assertContains(adminCheckInAuditExportCsv.text, 'listMockAdminCheckInAuditLogExportRows(normalizedParams)', 'admin check-in audit CSV mock client')
assertContains(adminCheckInAuditExportCsv.text, 'buildAdminCheckInAuditCsvText', 'admin check-in audit CSV mock builder')
assertContains(adminCheckInAuditExportCsv.text, 'admin-check-in-logs-${dateFrom}-${dateTo}.csv', 'admin check-in audit CSV mock file name')
assertContains(adminCheckInFailureLogQueries.text, 'VITE_ADMIN_CHECK_IN_FAILURE_LOGS_MODE', 'admin check-in failure audit search mode env')
assertContains(adminCheckInFailureLogQueries.text, "import.meta.env.VITE_ADMIN_CHECK_IN_FAILURE_LOGS_MODE === 'mock' ? 'mock' : 'api'", 'admin check-in failure audit search defaults to API')
assertContains(adminCheckInFailureLogQueries.text, "['admin-check-in-failure-logs', mode, 'list'", 'admin check-in failure audit search query key namespace')
assertContains(adminCheckInFailureLogQueries.text, 'adminCheckInFailureAuditLogsApi.list(normalizedParams)', 'admin check-in failure audit search API client')
assertContains(adminCheckInFailureLogQueries.text, 'listMockAdminCheckInFailureAuditLogSearch(normalizedParams)', 'admin check-in failure audit search mock client')
assertContains(adminCheckInFailureLogQueries.text, 'normalizeAdminCheckInFailureAuditLogExportParams', 'admin check-in failure audit export params normalizer')
assertContains(adminCheckInFailureAuditExportCsv.text, 'adminCheckInFailureAuditLogExportsApi.csv(normalizedParams)', 'admin check-in failure audit CSV API client')
assertContains(adminCheckInFailureAuditExportCsv.text, 'listMockAdminCheckInFailureAuditLogRows(normalizedParams)', 'admin check-in failure audit CSV mock client')
assertContains(adminCheckInFailureAuditExportCsv.text, 'buildAdminCheckInFailureAuditCsvText', 'admin check-in failure audit CSV mock builder')
assertContains(adminCheckInFailureAuditExportCsv.text, 'admin-check-in-failure-logs-${dateFrom}-${dateTo}.csv', 'admin check-in failure audit CSV mock file name')
assertContains(adminCheckInFailureAuditExportXlsx.text, 'adminCheckInFailureAuditLogExportsApi.xlsx(normalizedParams)', 'admin check-in failure audit XLSX API client')
assertContains(adminCheckInFailureAuditExportXlsx.text, 'listMockAdminCheckInFailureAuditLogRows(normalizedParams)', 'admin check-in failure audit XLSX mock client')
assertContains(adminCheckInFailureAuditExportXlsx.text, 'buildAdminCheckInFailureAuditLogsXlsxBlob', 'admin check-in failure audit XLSX mock builder')
assertContains(adminCheckInFailureAuditExportXlsx.text, 'inlineStr', 'admin check-in failure audit XLSX writes string cells')
assertContains(adminCheckInFailureAuditExportXlsx.text, 'admin-check-in-failure-logs-${dateFrom}-${dateTo}.xlsx', 'admin check-in failure audit XLSX mock file name')
assertContains(endpoints.text, 'body: { ticketCode: body.ticketCode.trim() }', 'admin check-in API client rebuilds body at endpoint boundary')
assertContains(endpoints.text, '/api/admin/check-ins/batch', 'admin batch check-in endpoint')
assertContains(endpoints.text, 'body: { ticketCodes: body.ticketCodes.map((ticketCode) => ticketCode.trim()) }', 'admin batch check-in API client trims ticket codes without dropping invalid blanks')
assertContains(endpoints.text, '/api/admin/check-ins/batch/undo', 'admin batch undo check-in endpoint')
assertContains(endpoints.text, 'reason: compactText(body.reason)', 'admin batch undo check-in API client trims optional reason')
assertContains(adminOrderQueries.text, 'adminCheckInsApi.create({ ticketCode: body.ticketCode.trim() })', 'admin check-in query trims ticket code before API call')
assertContains(adminOrderQueries.text, 'adminCheckInsApi.batch(normalizedBody)', 'admin batch check-in query calls API endpoint')
assertContains(adminOrderQueries.text, 'checkInMockAdminTickets(normalizedBody)', 'admin batch check-in query calls mock state machine')
assertContains(adminOrderQueries.text, 'useAdminBatchCheckInMutation', 'admin batch check-in mutation hook')
assertContains(adminOrderQueries.text, 'adminCheckInsApi.batchUndo(normalizedBody)', 'admin batch undo check-in query calls API endpoint')
assertContains(adminOrderQueries.text, "...(body.reason?.trim() ? { reason: body.reason.trim() } : {})", 'admin batch undo check-in query trims optional reason')
assertContains(adminOrderQueries.text, 'undoCheckInMockAdminTickets(normalizedBody)', 'admin batch undo check-in query calls mock state machine')
assertContains(adminOrderQueries.text, 'useAdminBatchUndoCheckInMutation', 'admin batch undo check-in mutation hook')
assertContains(adminOrderQueries.text, 'adminOrdersApi.refund(normalizedOrderNo, body)', 'admin full refund query calls API endpoint')
assertContains(adminOrderQueries.text, 'refundMockAdminOrder(normalizedOrderNo, body)', 'admin full refund query calls mock state machine')
assertContains(adminOrderQueries.text, "queryClient.invalidateQueries({ queryKey: ['admin-refund-logs'] })", 'admin full refund invalidates global audit log search')
assertContains(adminOrderQueries.text, "queryClient.invalidateQueries({ queryKey: ['admin-reports'] })", 'admin full refund invalidates admin reports')
assertContains(adminOrderQueries.text, 'useAdminPartialRefundMutation', 'admin partial refund mutation hook')
assertContains(adminOrderQueries.text, 'adminOrdersApi.partialRefund(normalizedOrderNo, body)', 'admin partial refund query calls API endpoint')
assertContains(adminOrderQueries.text, 'partialRefundMockAdminOrder(normalizedOrderNo, body)', 'admin partial refund query calls mock state machine')
assertContains(adminOrderQueries.text, 'itemNos: itemNos.map((itemNo) => itemNo.trim())', 'admin partial refund query trims item numbers without dropping invalid blanks')
assertContains(adminOrderQueries.text, 'listMockAdminOrders(normalizedParams)', 'admin orders mock list client')
assertContains(adminOrderQueries.text, 'getMockAdminOrderDetail(normalizedOrderNo)', 'admin orders mock detail client')
assertContains(adminOrderQueries.text, 'listMockAdminRefundAuditLogs(normalizedOrderNo)', 'admin refund audit logs mock client')
assertContains(adminOrderQueries.text, "['admin-orders', mode, 'refund-logs'", 'admin refund audit logs query key namespace')
assertContains(adminOrderQueries.text, 'checkInMockAdminTicket(body.ticketCode)', 'admin check-in mock client')
assertContains(adminOrderMockData.text, "import { mockAdminOrderDetails, mockRefundAuditLogsByOrderNo } from './mockOrderSeeds'", 'admin mock data imports seed data module')
assertContains(adminOrderMockSurfaceText, 'buyerPhoneMasked', 'admin mock orders masked phone only')
assertContains(adminOrderMockSurfaceText, 'mockRefundAuditLogsByOrderNo', 'admin mock refund audit logs')
assertContains(adminOrderMockSurfaceText, "refundType: 'PARTIAL'", 'admin mock refund audit log type')
assertContains(adminOrderMockSurfaceText, "operatorUsername: 'admin'", 'admin mock refund audit operator display field')
assertContains(adminOrderMockSurfaceText, "requestId: 'mock-refund-request-260628-003'", 'admin mock refund audit request id')
assertContains(adminOrderMockSurfaceText, "orderNo: 'YT2606280005'", 'admin mock full refund candidate order')
assertContains(adminOrderMockSurfaceText, "orderNo: 'YT2606280006'", 'admin mock partial refund candidate order')
assertContains(adminOrderMockSurfaceText, "orderNo: 'YT2606280007'", 'admin mock batch check-in candidate order')
assertContains(adminOrderMockSurfaceText, "orderNo: 'YT2606280008'", 'admin mock undo-not-allowed candidate order')
assertContains(adminOrderMockData.text, 'refundMockAdminOrder', 'admin mock full refund mutation')
assertContains(adminOrderMockData.text, 'partialRefundMockAdminOrder', 'admin mock partial refund mutation')
assertContains(adminOrderMockData.text, "code: 'ADMIN_ORDER_NOT_FOUND'", 'admin mock full refund missing order error')
assertContains(adminOrderMockData.text, "code: 'ORDER_ALREADY_REFUNDED'", 'admin mock full refund duplicate error')
assertContains(adminOrderMockData.text, "code: 'ORDER_NOT_REFUNDABLE'", 'admin mock full refund state guard error')
assertContains(adminOrderMockData.text, "code: 'VALIDATION_ERROR'", 'admin mock partial refund request validation error')
assertContains(adminOrderMockData.text, "code: 'ORDER_REFUND_ITEMS_INVALID'", 'admin mock partial refund item guard error')
assertContains(adminOrderMockData.text, "code: 'ORDER_NOT_PARTIALLY_REFUNDABLE'", 'admin mock partial refund state guard error')
assertContains(adminOrderMockData.text, "refundType: 'FULL'", 'admin mock full refund audit log type')
assertContains(adminOrderMockData.text, 'addMockAdminRefundAuditLog(log)', 'admin mock full refund appends global audit log')
assertContains(adminOrderMockData.text, 'addMockAdminCheckInAuditLog', 'admin mock check-in appends global check-in audit log')
assertContains(adminOrderMockData.text, 'checkInMockAdminTicket', 'admin mock check-in mutation')
assertContains(adminOrderMockData.text, 'checkInMockAdminTickets', 'admin mock batch check-in mutation')
assertContains(adminOrderMockData.text, 'undoCheckInMockAdminTicket', 'admin mock undo check-in mutation')
assertContains(adminOrderMockData.text, 'undoCheckInMockAdminTickets', 'admin mock batch undo check-in mutation')
assertContains(adminOrderMockData.text, "code: 'TICKET_NOT_FOUND'", 'admin mock check-in ticket not found error')
assertContains(adminOrderMockData.text, "code: 'TICKET_ALREADY_USED'", 'admin mock check-in already used error')
assertContains(adminOrderMockData.text, "code: 'TICKET_NOT_CHECKABLE'", 'admin mock check-in state error')
assertContains(adminOrderMockData.text, "code: 'TICKET_NOT_CHECKED_IN'", 'admin mock undo check-in not checked in error')
assertContains(adminOrderMockData.text, "code: 'TICKET_UNDO_NOT_ALLOWED'", 'admin mock undo check-in state error')
assertContains(adminOrderMockData.text, "item.itemStatus = 'USED'", 'admin mock check-in marks item used')
assertContains(adminOrderMockData.text, "item.itemStatus = 'UNUSED'", 'admin mock undo check-in marks item unused')
assertContains(adminOrderMockData.text, 'normalizeUndoCheckInReason', 'admin mock undo check-in normalizes optional reason')
assertContains(adminOrderMockData.text, 'hasRemainingCheckableTicket(order.items)', 'admin mock check-in completion guard')
assertContains(adminOrderMockData.text, 'ticketCodes.length === 0 || ticketCodes.length > 50', 'admin mock batch check-in validates item count')
assertContains(adminOrderMockData.text, 'uniqueTicketCodes.size !== ticketCodes.length', 'admin mock batch check-in rejects duplicates')
assertContains(adminOrderMockData.text, 'throwBatchUndoCheckInValidationError', 'admin mock batch undo check-in validates request body')
assertNotContains(adminOrderMockSurfaceText, 'buyerPhone:', 'admin mock orders full phone field')
assertNotContains(adminOrderMockSurfaceText, 'idNumber', 'admin mock orders id number field')
assertNotContains(adminOrderMockSurfaceText, 'session', 'admin mock orders session field')
assertNotContains(adminOrderMockSurfaceText, 'csrf', 'admin mock orders csrf field')
assertNotContains(adminOrderMockSurfaceText, 'password', 'admin mock orders password field')
assertNotContains(adminOrderMockSurfaceText, 'hash', 'admin mock orders hash field')
assertNotContains(adminOrderMockSurfaceText, 'updatedAt', 'admin mock orders database audit field')
assertNotContains(adminOrderMockSurfaceText, 'deletedAt', 'admin mock orders database audit field')
assertNotContains(adminOrderMockSurfaceText, 'adminUserId', 'admin mock refund audit internal admin id')

const { normalizeAdminOrderListParams } = loadRuntimeFunctions(adminOrderQueries.sourceFile, ['normalizeAdminOrderListParams'])
assert(
  JSON.stringify(normalizeAdminOrderListParams({ orderNo: ' ORD ', buyerPhone: '   ', page: 2 })) === JSON.stringify({ orderNo: 'ORD', page: 2 }),
  'admin order query params must trim text filters and omit blanks',
)
const {
  __checkInAuditAppends,
  checkInMockAdminTickets,
  getMockAdminOrderDetail,
  listMockAdminRefundAuditLogs,
  partialRefundMockAdminOrder,
  refundMockAdminOrder,
  undoCheckInMockAdminTickets,
} = loadRuntimeFunctions([adminOrderMockSeeds.sourceFile, adminOrderMockData.sourceFile], [
  'withMockPassengerFields',
  'mockAdminOrderDetails',
  'mockRefundAuditLogsByOrderNo',
  'getMockAdminOrderDetail',
  'listMockAdminRefundAuditLogs',
  'appendMockRefundAuditLog',
  'amountSum',
  'normalizeRefundItemNos',
  'hasRemainingCheckableTicket',
  'isCheckInBusinessError',
  'isUndoCheckInBusinessError',
  'checkInMockAdminTicket',
  'throwBatchCheckInValidationError',
  'checkInMockAdminTickets',
  'throwBatchUndoCheckInValidationError',
  'normalizeUndoCheckInReason',
  'undoCheckInMockAdminTicket',
  'undoCheckInMockAdminTickets',
  'throwPartialRefundValidationError',
  'refundMockAdminOrder',
  'partialRefundMockAdminOrder',
])
const batchCheckInResult = checkInMockAdminTickets({
  ticketCodes: [' TK2606280001A ', ' TK-NOT-FOUND '],
})
assert(batchCheckInResult.totalCount === 2, 'admin mock batch check-in must return total count')
assert(batchCheckInResult.successCount === 1, 'admin mock batch check-in must count successes')
assert(batchCheckInResult.failureCount === 1, 'admin mock batch check-in must count business failures')
assert(
  batchCheckInResult.results[0].success && batchCheckInResult.results[0].checkIn?.ticketCode === 'TK2606280001A',
  'admin mock batch check-in must return success DTO per ticket',
)
assert(batchCheckInResult.results[1].code === 'TICKET_NOT_FOUND', 'admin mock batch check-in must keep business failure per ticket')
try {
  checkInMockAdminTickets({ ticketCodes: ['TK2606280001B', ' TK2606280001B '] })
  assert(false, 'admin mock batch check-in must reject duplicate ticket codes')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock batch check-in duplicate guard must mirror API validation error code')
}
try {
  checkInMockAdminTickets({ ticketCodes: [''] })
  assert(false, 'admin mock batch check-in must reject blank ticket codes')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock batch check-in blank guard must mirror API validation error code')
}
try {
  checkInMockAdminTickets({ ticketCodes: Array.from({ length: 51 }, (_, index) => `TK-BATCH-${index}`) })
  assert(false, 'admin mock batch check-in must reject more than fifty ticket codes')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock batch check-in count guard must mirror API validation error code')
}
const batchUndoCheckInResult = undoCheckInMockAdminTickets({
  ticketCodes: [' TK2606280001A ', ' TK-UNDO-NOT-FOUND '],
  reason: ' 现场误核销 ',
})
assert(batchUndoCheckInResult.totalCount === 2, 'admin mock batch undo check-in must return total count')
assert(batchUndoCheckInResult.successCount === 1, 'admin mock batch undo check-in must count successes')
assert(batchUndoCheckInResult.failureCount === 1, 'admin mock batch undo check-in must count business failures')
assert(
  batchUndoCheckInResult.results[0].success &&
    batchUndoCheckInResult.results[0].undoCheckIn.ticketCode === 'TK2606280001A' &&
    batchUndoCheckInResult.results[0].undoCheckIn.itemStatus === 'UNUSED',
  'admin mock batch undo check-in must return success DTO per ticket',
)
assert(batchUndoCheckInResult.results[1].code === 'TICKET_NOT_FOUND', 'admin mock batch undo check-in must keep business failure per ticket')
assert(
  __checkInAuditAppends.some((log) =>
    log.action === 'UNDO_CHECK_IN' &&
    log.ticketCode === 'TK2606280001A' &&
    log.reason === '现场误核销'
  ),
  'admin mock batch undo check-in must append successful undo reason to check-in audit log',
)
assert(
  !__checkInAuditAppends.some((log) => log.ticketCode === 'TK-UNDO-NOT-FOUND'),
  'admin mock batch undo check-in must not append check-in audit log for failed tickets',
)
try {
  undoCheckInMockAdminTickets({ ticketCodes: ['TK2606280001B'], reason: '   ' })
  assert(false, 'admin mock batch undo check-in must reject blank reason when provided')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock batch undo check-in blank reason must mirror API validation error code')
}
try {
  undoCheckInMockAdminTickets({ ticketCodes: ['TK2606280001B'], reason: 'x'.repeat(101) })
  assert(false, 'admin mock batch undo check-in must reject overlong reason')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock batch undo check-in reason length guard must mirror API validation error code')
}
const batchUndoNotCheckedInResult = undoCheckInMockAdminTickets({ ticketCodes: ['TK2606280001A'] })
assert(
  batchUndoNotCheckedInResult.results[0].success === false &&
    batchUndoNotCheckedInResult.results[0].code === 'TICKET_NOT_CHECKED_IN',
  'admin mock batch undo check-in not-checked-in guard must return per-ticket API error code',
)
const batchUndoNotAllowedResult = undoCheckInMockAdminTickets({ ticketCodes: ['TK2606280008A'] })
assert(
  batchUndoNotAllowedResult.results[0].success === false &&
    batchUndoNotAllowedResult.results[0].code === 'TICKET_UNDO_NOT_ALLOWED',
  'admin mock batch undo check-in state guard must return per-ticket API error code',
)
try {
  undoCheckInMockAdminTickets({ ticketCodes: ['TK2606280001B', ' TK2606280001B '] })
  assert(false, 'admin mock batch undo check-in must reject duplicate ticket codes')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock batch undo check-in duplicate guard must mirror API validation error code')
}
try {
  undoCheckInMockAdminTickets({ ticketCodes: [''] })
  assert(false, 'admin mock batch undo check-in must reject blank ticket codes')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock batch undo check-in blank guard must mirror API validation error code')
}
try {
  undoCheckInMockAdminTickets({ ticketCodes: Array.from({ length: 51 }, (_, index) => `TK-UNDO-BATCH-${index}`) })
  assert(false, 'admin mock batch undo check-in must reject more than fifty ticket codes')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock batch undo check-in count guard must mirror API validation error code')
}
const existingPartialRefundDetail = getMockAdminOrderDetail('YT2606280003')
assert(existingPartialRefundDetail.orderStatus === 'PAID', 'admin mock partial refund seed must keep order paid')
assert(existingPartialRefundDetail.paymentStatus === 'PARTIAL_REFUND', 'admin mock partial refund seed must mark payment partial refund')
assert(existingPartialRefundDetail.payableAmount === '128.00', 'admin mock partial refund seed must keep only remaining active amount payable')
assert(
  existingPartialRefundDetail.items.find((item) => item.itemNo === 'ITEM-260628-003-A')?.itemStatus === 'REFUNDED',
  'admin mock partial refund seed must mark refunded item as refunded',
)
const partialRefundLogs = listMockAdminRefundAuditLogs('YT2606280003')
assert(partialRefundLogs.length === 1, 'admin mock refund audit logs must include partial refund order')
assert(partialRefundLogs[0].refundType === 'PARTIAL', 'admin mock refund audit log must mark partial refund type')
assert(partialRefundLogs[0].requestId === 'mock-refund-request-260628-003', 'admin mock refund audit log must expose request id')
assert(listMockAdminRefundAuditLogs('YT2606280001').length === 0, 'admin mock refund audit logs must return empty array for orders without logs')
assert(
  !JSON.stringify(partialRefundLogs).match(/adminUserId|idNumber|session|csrf|password|hash|SQL|13711115555/),
  'admin mock refund audit logs must not expose sensitive fields',
)
const fullRefundResult = refundMockAdminOrder('YT2606280005', { reason: ' 游客行程取消 ' })
const fullRefundLogs = listMockAdminRefundAuditLogs('YT2606280005')
assert(fullRefundResult.orderStatus === 'REFUNDED', 'admin mock full refund must mark order refunded')
assert(fullRefundResult.paymentStatus === 'REFUNDED', 'admin mock full refund must mark payment refunded')
assert(fullRefundResult.refundedAmount === '128.00', 'admin mock full refund must return backend-computed refund amount')
assert(fullRefundResult.refundedItemCount === 1, 'admin mock full refund must return refunded item count')
assert(fullRefundLogs[0].refundType === 'FULL', 'admin mock full refund must append full audit log')
assert(fullRefundLogs[0].reason === '游客行程取消', 'admin mock full refund must trim reason before audit log')
assert(fullRefundLogs[0].requestId === 'mock-refund-request-260628-005', 'admin mock full refund must expose request id')
try {
  refundMockAdminOrder('YT2606280005')
  assert(false, 'admin mock full refund must reject duplicate refund')
} catch (error) {
  assert(error.code === 'ORDER_ALREADY_REFUNDED', 'admin mock full refund duplicate must mirror API error code')
}
try {
  refundMockAdminOrder('YT2606280003')
  assert(false, 'admin mock full refund must reject non-refundable orders')
} catch (error) {
  assert(error.code === 'ORDER_NOT_REFUNDABLE', 'admin mock full refund state guard must mirror API error code')
}
try {
  refundMockAdminOrder('YT2606289999')
  assert(false, 'admin mock full refund must reject missing orders')
} catch (error) {
  assert(error.code === 'ADMIN_ORDER_NOT_FOUND', 'admin mock full refund missing order must mirror API error code')
}
const partialRefundResult = partialRefundMockAdminOrder('YT2606280006', {
  itemNos: [' ITEM-260628-006-A '],
  reason: ' 只退成人票 ',
})
const partialRefundLogsAfterMutation = listMockAdminRefundAuditLogs('YT2606280006')
assert(partialRefundResult.orderStatus === 'PAID', 'admin mock partial refund must keep order paid when items remain')
assert(partialRefundResult.paymentStatus === 'PARTIAL_REFUND', 'admin mock partial refund must mark payment partial refund')
assert(partialRefundResult.refundedAmount === '128.00', 'admin mock partial refund must compute amount from selected items')
assert(partialRefundResult.refundedItemCount === 1, 'admin mock partial refund must return selected item count')
assert(
  JSON.stringify(partialRefundResult.refundedItemNos) === JSON.stringify(['ITEM-260628-006-A']),
  'admin mock partial refund must trim and return selected item numbers',
)
assert(partialRefundLogsAfterMutation[0].refundType === 'PARTIAL', 'admin mock partial refund must append partial audit log')
assert(partialRefundLogsAfterMutation[0].reason === '只退成人票', 'admin mock partial refund must trim reason before audit log')
assert(
  partialRefundLogsAfterMutation[0].requestId === 'mock-partial-refund-request-260628-006',
  'admin mock partial refund must expose request id',
)
try {
  partialRefundMockAdminOrder('YT2606280006', { itemNos: ['ITEM-260628-006-B', ' '] })
  assert(false, 'admin mock partial refund must reject mixed blank item numbers')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock partial refund blank item guard must mirror API validation error code')
}
try {
  partialRefundMockAdminOrder('YT2606280006', {
    itemNos: Array.from({ length: 21 }, (_, index) => `ITEM-260628-006-B-${index}`),
  })
  assert(false, 'admin mock partial refund must reject more than twenty item numbers')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock partial refund item count guard must mirror API validation error code')
}
try {
  partialRefundMockAdminOrder('YT2606280006', {
    itemNos: ['ITEM-260628-006-B'],
    reason: '超'.repeat(101),
  })
  assert(false, 'admin mock partial refund must reject overlong reasons')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock partial refund reason length guard must mirror API validation error code')
}
try {
  partialRefundMockAdminOrder('YT2606280006', { itemNos: ['ITEM-260628-006-A'] })
  assert(false, 'admin mock partial refund must reject already refunded selected item')
} catch (error) {
  assert(error.code === 'ORDER_NOT_PARTIALLY_REFUNDABLE', 'admin mock partial refund selected item guard must mirror API error code')
}
try {
  partialRefundMockAdminOrder('YT2606280006', { itemNos: ['ITEM-260628-006-B', 'ITEM-260628-006-B'] })
  assert(false, 'admin mock partial refund must reject duplicate item numbers')
} catch (error) {
  assert(error.code === 'VALIDATION_ERROR', 'admin mock partial refund duplicate item guard must mirror API validation error code')
}
try {
  partialRefundMockAdminOrder('YT2606280006', { itemNos: ['ITEM-OUTSIDE'] })
  assert(false, 'admin mock partial refund must reject items outside the order')
} catch (error) {
  assert(error.code === 'ORDER_REFUND_ITEMS_INVALID', 'admin mock partial refund outside item guard must mirror API error code')
}
const finalPartialRefundResult = partialRefundMockAdminOrder('YT2606280006', {
  itemNos: ['ITEM-260628-006-B'],
  reason: '退剩余儿童票',
})
const finalPartialRefundLogs = listMockAdminRefundAuditLogs('YT2606280006')
assert(finalPartialRefundResult.orderStatus === 'REFUNDED', 'admin mock partial refund must mark order refunded after last active item')
assert(finalPartialRefundResult.paymentStatus === 'REFUNDED', 'admin mock partial refund must mark payment refunded after last active item')
assert(finalPartialRefundResult.refundedAmount === '68.00', 'admin mock partial refund must compute final item amount')
assert(finalPartialRefundLogs[0].reason === '退剩余儿童票', 'admin mock partial refund must append final partial audit log')
try {
  partialRefundMockAdminOrder('YT2606280006', { itemNos: ['ITEM-260628-006-B'] })
  assert(false, 'admin mock partial refund must reject fully refunded orders')
} catch (error) {
  assert(error.code === 'ORDER_ALREADY_REFUNDED', 'admin mock partial refund fully refunded guard must mirror API error code')
}
try {
  partialRefundMockAdminOrder('YT2606280002', { itemNos: ['ITEM-260628-002-A'] })
  assert(false, 'admin mock partial refund must reject unpaid orders')
} catch (error) {
  assert(error.code === 'ORDER_NOT_PARTIALLY_REFUNDABLE', 'admin mock partial refund state guard must mirror API error code')
}
const { normalizeAdminRefundAuditLogParams } = loadRuntimeFunctions(adminRefundLogQueries.sourceFile, ['normalizeAdminRefundAuditLogParams'])
assert(
  JSON.stringify(normalizeAdminRefundAuditLogParams({ orderNo: ' YT2606280003 ', operatorUsername: ' ', page: 1 })) ===
    JSON.stringify({ orderNo: 'YT2606280003', page: 1 }),
  'admin refund audit search params must trim text filters and omit blanks',
)
const {
  normalizeAdminCheckInFailureAuditLogExportParams,
  normalizeAdminCheckInFailureAuditLogParams,
} = loadRuntimeFunctions(adminCheckInFailureLogQueries.sourceFile, [
  'compactText',
  'normalizeAdminCheckInFailureAuditLogExportParams',
  'normalizeAdminCheckInFailureAuditLogParams',
])
assert(
  JSON.stringify(normalizeAdminCheckInFailureAuditLogParams({ ticketCode: ' TK-MISSING ', operatorUsername: ' ', page: 1 })) ===
    JSON.stringify({ ticketCode: 'TK-MISSING', page: 1 }),
  'admin check-in failure audit search params must trim text filters and omit blanks',
)
assert(
  JSON.stringify(normalizeAdminCheckInFailureAuditLogExportParams({
    failureCode: 'TICKET_UNDO_NOT_ALLOWED',
    ticketCode: ' TK2606280010U ',
    operatorUsername: ' ops_lina ',
    dateFrom: ' ',
    dateTo: '2026-06-30',
    page: 2,
  })) === JSON.stringify({
    ticketCode: 'TK2606280010U',
    failureCode: 'TICKET_UNDO_NOT_ALLOWED',
    operatorUsername: 'ops_lina',
    dateTo: '2026-06-30',
  }),
  'admin check-in failure audit export params must trim text filters and omit pagination',
)
const {
  listMockAdminCheckInFailureAuditLogRows,
  listMockAdminCheckInFailureAuditLogSearch,
} = loadRuntimeFunctions(adminCheckInFailureLogMockData.sourceFile, [
  'allowedFailureCodes',
  'mockAdminCheckInFailureAuditLogs',
  'textIncludes',
  'datePart',
  'assertValidFilters',
  'inDateRange',
  'listMockAdminCheckInFailureAuditLogRows',
  'listMockAdminCheckInFailureAuditLogSearch',
])
const checkInFailureSearchResult = listMockAdminCheckInFailureAuditLogSearch({
  failureCode: 'TICKET_NOT_FOUND',
  ticketCode: 'MISSING',
  operatorUsername: 'admin',
  dateFrom: '2026-07-01',
  dateTo: '2026-07-01',
})
assert(checkInFailureSearchResult.total === 1, 'admin check-in failure audit search mock must filter failure code, ticket, operator, and date range')
assert(checkInFailureSearchResult.items[0].requestId === 'mock-check-in-failure-260701-001', 'admin check-in failure audit search mock must expose request id')
assert(
  listMockAdminCheckInFailureAuditLogSearch({ failureCode: 'TICKET_ALREADY_USED' }).items[0].failureCode === 'TICKET_ALREADY_USED',
  'admin check-in failure audit search mock must include already-used rows',
)
assert(
  listMockAdminCheckInFailureAuditLogSearch({ failureCode: 'TICKET_NOT_CHECKED_IN' }).items[0].action === 'UNDO_CHECK_IN',
  'admin check-in failure audit search mock must include undo rows for not-checked-in failures',
)
assert(
  listMockAdminCheckInFailureAuditLogSearch({ failureCode: 'TICKET_UNDO_NOT_ALLOWED' }).items[0].failureCode === 'TICKET_UNDO_NOT_ALLOWED',
  'admin check-in failure audit search mock must include undo-not-allowed rows',
)
assert(listMockAdminCheckInFailureAuditLogRows({ dateFrom: '2026-07-02' }).length === 0, 'admin check-in failure audit search mock must honor date range')
try {
  listMockAdminCheckInFailureAuditLogSearch({ failureCode: 'SYSTEM_ERROR' })
  assert(false, 'admin check-in failure audit search mock must reject unsupported failure code')
} catch (error) {
  assert(error.code === 'ADMIN_CHECK_IN_FAILURE_CODE_INVALID', 'admin check-in failure audit search mock must mirror API invalid failure code')
}
try {
  listMockAdminCheckInFailureAuditLogSearch({ dateFrom: '2026-07-02', dateTo: '2026-07-01' })
  assert(false, 'admin check-in failure audit search mock must reject inverted date range')
} catch (error) {
  assert(error.code === 'ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID', 'admin check-in failure audit search mock must mirror API date range error code')
}
assert(
  !JSON.stringify(listMockAdminCheckInFailureAuditLogSearch()).match(/adminUserId|orderId|buyerPhone|idNumber|session|csrf|password|hash|SQL|13911112222/),
  'admin check-in failure audit search mock must not expose sensitive fields',
)
const {
  buildAdminCheckInFailureAuditCsvText,
  escapeCheckInFailureAuditCsvCell,
  neutralizeCheckInFailureAuditCsvFormulaText,
} = loadRuntimeFunctions(adminCheckInFailureAuditExportCsv.sourceFile, [
  'adminCheckInFailureLogCsvHeaders',
  'sanitizeCsvText',
  'neutralizeCheckInFailureAuditCsvFormulaText',
  'escapeCheckInFailureAuditCsvCell',
  'buildAdminCheckInFailureAuditCsvText',
])
assert(neutralizeCheckInFailureAuditCsvFormulaText('=1+1') === "'=1+1", 'admin check-in failure audit CSV must neutralize formulas')
assert(escapeCheckInFailureAuditCsvCell('hello,world') === '"hello,world"', 'admin check-in failure audit CSV must quote comma cells')
const failureAuditCsvText = buildAdminCheckInFailureAuditCsvText([
  {
    ticketCode: '=BAD',
    action: 'UNDO_CHECK_IN',
    failureCode: 'TICKET_NOT_CHECKED_IN',
    failureMessage: '+bad',
    operatorUsername: '@ops',
    operatorDisplayName: '运营',
    requestId: '\tREQ',
    createdAt: '2026-07-01T10:04:00+08:00',
  },
])
assert(failureAuditCsvText.startsWith('\ufeffticketCode,action,failureCode,failureMessage,operatorUsername,operatorDisplayName,requestId,createdAt'), 'admin check-in failure audit CSV must use fixed safe columns')
assertContains(failureAuditCsvText, "'=BAD", 'admin check-in failure audit CSV must neutralize ticket formulas')
assertContains(failureAuditCsvText, "'+bad", 'admin check-in failure audit CSV must neutralize message formulas')
assertContains(failureAuditCsvText, "'@ops", 'admin check-in failure audit CSV must neutralize operator formulas')
assertContains(failureAuditCsvText, "\"'\tREQ\"", 'admin check-in failure audit CSV must quote and neutralize tab formulas')
assert(
  !failureAuditCsvText.match(/adminUserId|orderId|buyerPhone|idNumber|session|csrf|password|hash|SQL|13911112222/),
  'admin check-in failure audit CSV mock text must not expose sensitive fields',
)
const {
  buildAdminCheckInFailureAuditLogsXlsxBlob,
  neutralizeCheckInFailureAuditSpreadsheetText,
} = loadRuntimeFunctions(adminCheckInFailureAuditExportXlsx.sourceFile, [
  'adminCheckInFailureLogHeaders',
  'adminCheckInFailureLogXlsxContentType',
  'textEncoder',
  'crc32Table',
  'neutralizeCheckInFailureAuditSpreadsheetText',
  'sanitizeXmlText',
  'escapeXmlText',
  'columnName',
  'buildWorksheetXml',
  'makeCrc32Table',
  'crc32',
  'writeUint16',
  'writeUint32',
  'appendBytes',
  'buildStoreZip',
  'buildAdminCheckInFailureAuditLogsXlsxBlob',
])
assert(neutralizeCheckInFailureAuditSpreadsheetText('=1+1') === "'=1+1", 'admin check-in failure audit XLSX must neutralize formulas')
assert(neutralizeCheckInFailureAuditSpreadsheetText(' +cmd') === "' +cmd", 'admin check-in failure audit XLSX must neutralize formulas after leading spaces')
const failureAuditXlsxBlob = buildAdminCheckInFailureAuditLogsXlsxBlob([
  {
    ticketCode: '\u0001=BAD',
    action: 'UNDO_CHECK_IN',
    failureCode: 'TICKET_NOT_CHECKED_IN',
    failureMessage: 'bad\u0001<message>&',
    operatorUsername: '@ops',
    operatorDisplayName: '运营',
    requestId: '\tREQ',
    createdAt: '2026-07-01T10:04:00+08:00',
  },
])
const failureAuditXlsxBytes = new Uint8Array(await failureAuditXlsxBlob.arrayBuffer())
const failureAuditWorksheetXml = readStoreZipEntryText(failureAuditXlsxBytes, 'xl/worksheets/sheet1.xml')
assert(
  failureAuditXlsxBlob.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'admin check-in failure audit mock XLSX blob must use XLSX content type',
)
assert(failureAuditXlsxBytes[0] === 0x50 && failureAuditXlsxBytes[1] === 0x4B, 'admin check-in failure audit mock XLSX must be a ZIP payload')
assertContains(failureAuditWorksheetXml, 'ticketCode', 'admin check-in failure audit mock XLSX must include fixed headers')
assertContains(failureAuditWorksheetXml, '&apos;=BAD', 'admin check-in failure audit mock XLSX formula-like ticket text must be neutralized')
assertContains(failureAuditWorksheetXml, 'bad&lt;message&gt;&amp;', 'admin check-in failure audit mock XLSX XML text must be escaped')
assertContains(failureAuditWorksheetXml, '&apos;@ops', 'admin check-in failure audit mock XLSX operator text must be neutralized')
assertContains(failureAuditWorksheetXml, '&apos;\tREQ', 'admin check-in failure audit mock XLSX tab-prefixed request text must be neutralized')
assert(!failureAuditWorksheetXml.includes('<f'), 'admin check-in failure audit mock XLSX must not generate formula nodes')
assert(!failureAuditWorksheetXml.includes('<t>=BAD</t>'), 'admin check-in failure audit mock XLSX must neutralize values after XML control character cleanup')
assert(!failureAuditWorksheetXml.includes('\u0001'), 'admin check-in failure audit mock XLSX XML text must remove disallowed control characters')
const {
  listMockAdminRefundAuditLogExportRows,
  listMockAdminRefundAuditLogSearch,
} = loadRuntimeFunctions(adminRefundLogMockData.sourceFile, [
  'mockRefundAuditLogs',
  'textIncludes',
  'datePart',
  'inDateRange',
  'assertValidRefundAuditExportFilters',
  'listMockAdminRefundAuditLogExportRows',
  'listMockAdminRefundAuditLogSearch',
])
const refundAuditSearchResult = listMockAdminRefundAuditLogSearch({ refundType: 'PARTIAL', orderNo: '2606280003', operatorUsername: 'admin' })
assert(refundAuditSearchResult.total === 1, 'admin refund audit search mock must filter partial refund by order and operator')
assert(refundAuditSearchResult.items[0].requestId === 'mock-refund-request-260628-003', 'admin refund audit search mock must expose request id')
assert(listMockAdminRefundAuditLogSearch({ refundType: 'FULL' }).items[0].refundType === 'FULL', 'admin refund audit search mock must include full refund rows')
assert(listMockAdminRefundAuditLogSearch({ dateFrom: '2026-06-29' }).total === 0, 'admin refund audit search mock must honor date range')
try {
  listMockAdminRefundAuditLogSearch({ dateFrom: '2026-06-29', dateTo: '2026-06-28' })
  assert(false, 'admin refund audit search mock must reject inverted date range')
} catch (error) {
  assert(error.code === 'ADMIN_REFUND_LOG_DATE_RANGE_INVALID', 'admin refund audit search mock must mirror API date range error code')
}
assert(
  !JSON.stringify(listMockAdminRefundAuditLogSearch()).match(/adminUserId|idNumber|session|csrf|password|hash|SQL|13711115555|13911112222/),
  'admin refund audit search mock must not expose sensitive fields',
)
const refundAuditExportRows = listMockAdminRefundAuditLogExportRows({
  refundType: 'PARTIAL',
  orderNo: '2606280003',
  operatorUsername: 'admin',
  dateFrom: '2026-06-28',
  dateTo: '2026-06-28',
})
assert(refundAuditExportRows.length === 1, 'admin refund audit export mock must filter by type, order, operator, and date range')
assert(refundAuditExportRows[0].refundedItemNos[0] === 'ITEM-260628-003-A', 'admin refund audit export mock must include refunded item numbers')
assert(
  !JSON.stringify(listMockAdminRefundAuditLogExportRows()).match(/adminUserId|idNumber|session|csrf|password|hash|SQL|13711115555|13911112222/),
  'admin refund audit export mock must not expose sensitive fields',
)
try {
  listMockAdminRefundAuditLogExportRows({ dateFrom: '2026-06-29', dateTo: '2026-06-28' })
  assert(false, 'admin refund audit export mock must reject inverted date range')
} catch (error) {
  assert(error.code === 'ADMIN_REFUND_LOG_DATE_RANGE_INVALID', 'admin refund audit export mock must mirror API date range error code')
}
const {
  buildAdminRefundAuditCsvText,
  escapeRefundAuditCsvCell,
  neutralizeRefundAuditCsvFormulaText,
} = loadRuntimeFunctions(adminRefundAuditExportCsv.sourceFile, [
  'adminRefundLogCsvHeaders',
  'sanitizeCsvText',
  'neutralizeRefundAuditCsvFormulaText',
  'escapeRefundAuditCsvCell',
  'buildAdminRefundAuditCsvText',
])
assert(neutralizeRefundAuditCsvFormulaText('=cmd') === "'=cmd", 'admin refund audit CSV text starting with = must be neutralized')
assert(neutralizeRefundAuditCsvFormulaText(' +cmd') === "' +cmd", 'admin refund audit CSV text with leading spaces before + must be neutralized')
assert(neutralizeRefundAuditCsvFormulaText('\u0001\u007F=cmd') === "'=cmd", 'admin refund audit CSV text must sanitize control chars before formula checks')
assert(escapeRefundAuditCsvCell('bad,"cell"') === '"bad,""cell"""', 'admin refund audit CSV text must escape quoted cells')
const refundAuditCsvText = buildAdminRefundAuditCsvText([
  {
    orderNo: '\u0001\u007F=1+1',
    refundType: 'PARTIAL',
    refundedAmount: '68.00',
    refundedItemCount: 2,
    refundedItemNos: 'ITEM-1;ITEM-2',
    reason: 'bad,"reason"',
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: null,
    createdAt: '2026-06-30T10:00:00+08:00',
  },
])
assert(refundAuditCsvText.startsWith('\ufefforderNo,refundType,refundedAmount'), 'admin refund audit CSV mock must include BOM and fixed header row')
assertContains(refundAuditCsvText, "'=1+1", 'admin refund audit CSV formula-like text must be neutralized after control cleanup')
assertContains(refundAuditCsvText, 'ITEM-1;ITEM-2', 'admin refund audit CSV item numbers must be joined')
assertContains(refundAuditCsvText, '"bad,""reason"""', 'admin refund audit CSV text must escape commas and quotes')
assert(!refundAuditCsvText.includes('\u0001'), 'admin refund audit CSV text must remove disallowed control characters')
assert(!refundAuditCsvText.includes('\u007F'), 'admin refund audit CSV text must remove DEL control characters')
const {
  buildAdminRefundAuditLogsXlsxBlob,
  neutralizeRefundAuditSpreadsheetText,
  normalizeAdminRefundAuditLogExportParams,
} = loadRuntimeFunctions(adminRefundAuditExportXlsx.sourceFile, [
  'adminRefundLogHeaders',
  'adminRefundLogXlsxContentType',
  'textEncoder',
  'crc32Table',
  'compactText',
  'normalizeAdminRefundAuditLogExportParams',
  'neutralizeRefundAuditSpreadsheetText',
  'sanitizeXmlText',
  'escapeXmlText',
  'columnName',
  'refundAuditCellValue',
  'buildWorksheetXml',
  'makeCrc32Table',
  'crc32',
  'writeUint16',
  'writeUint32',
  'appendBytes',
  'buildStoreZip',
  'buildAdminRefundAuditLogsXlsxBlob',
])
assert(
  JSON.stringify(normalizeAdminRefundAuditLogExportParams({ refundType: 'FULL', orderNo: ' YT2606280004 ', operatorUsername: '' })) ===
    JSON.stringify({ refundType: 'FULL', orderNo: 'YT2606280004' }),
  'admin refund audit export params must trim text filters and omit blanks',
)
assert(neutralizeRefundAuditSpreadsheetText('=cmd') === "'=cmd", 'admin refund audit XLSX text starting with = must be neutralized')
assert(neutralizeRefundAuditSpreadsheetText(' +cmd') === "' +cmd", 'admin refund audit XLSX text with leading spaces before + must be neutralized')

const refundAuditXlsxBlob = buildAdminRefundAuditLogsXlsxBlob([
  {
    orderNo: '\u0001=1+1',
    refundType: 'PARTIAL',
    refundedAmount: '68.00',
    refundedItemCount: 2,
    refundedItemNos: ['bad\u0001<item>&', 'ITEM-2'],
    reason: 'bad\u0001<reason>&',
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'request-1',
    createdAt: '2026-06-30T10:00:00+08:00',
  },
])
const refundAuditXlsxBytes = new Uint8Array(await refundAuditXlsxBlob.arrayBuffer())
const refundAuditWorksheetXml = readStoreZipEntryText(refundAuditXlsxBytes, 'xl/worksheets/sheet1.xml')
assert(
  refundAuditXlsxBlob.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'admin refund audit mock XLSX blob must use XLSX content type',
)
assert(refundAuditXlsxBytes[0] === 0x50 && refundAuditXlsxBytes[1] === 0x4B, 'admin refund audit mock XLSX must be a ZIP payload')
assertContains(refundAuditWorksheetXml, '&apos;=1+1', 'admin refund audit mock XLSX formula-like text must be neutralized')
assert(!refundAuditWorksheetXml.includes('<f'), 'admin refund audit mock XLSX must not generate formula nodes')
assert(!refundAuditWorksheetXml.includes('<t>=1+1</t>'), 'admin refund audit mock XLSX must neutralize values after XML control character cleanup')
assertContains(refundAuditWorksheetXml, 'bad&lt;item&gt;&amp;;ITEM-2', 'admin refund audit mock XLSX item numbers must be joined and XML-escaped')
assertContains(refundAuditWorksheetXml, 'bad&lt;reason&gt;&amp;', 'admin refund audit mock XLSX XML text must be escaped')
assert(!refundAuditWorksheetXml.includes('\u0001'), 'admin refund audit mock XLSX XML text must remove disallowed control characters')
const {
  buildAdminCheckInAuditLogsXlsxBlob,
  listMockAdminCheckInAuditLogExportRows,
  neutralizeSpreadsheetFormulaText: neutralizeCheckInAuditSpreadsheetText,
  normalizeAdminCheckInAuditLogExportParams,
} = loadRuntimeFunctions(adminCheckInAuditExportXlsx.sourceFile, [
  'adminCheckInLogHeaders',
  'adminCheckInLogXlsxContentType',
  'textEncoder',
  'crc32Table',
  'mockAdminCheckInAuditLogs',
  'compactText',
  'normalizeAdminCheckInAuditLogExportParams',
  'textIncludes',
  'isInExportDateRange',
  'assertValidExportDateRange',
  'listMockAdminCheckInAuditLogExportRows',
  'neutralizeSpreadsheetFormulaText',
  'sanitizeXmlText',
  'escapeXmlText',
  'columnName',
  'buildWorksheetXml',
  'makeCrc32Table',
  'crc32',
  'writeUint16',
  'writeUint32',
  'appendBytes',
  'buildStoreZip',
  'buildAdminCheckInAuditLogsXlsxBlob',
])
assert(
  JSON.stringify(normalizeAdminCheckInAuditLogExportParams({ ticketCode: ' TK ', orderNo: '', operatorUsername: ' admin ', reason: ' 误核 ' })) ===
    JSON.stringify({ ticketCode: 'TK', operatorUsername: 'admin', reason: '误核' }),
  'admin check-in audit export params must trim text filters and omit blanks',
)
const checkInAuditRows = listMockAdminCheckInAuditLogExportRows({ ticketCode: '2606280001A', dateFrom: '2026-06-28', dateTo: '2026-06-28' })
assert(checkInAuditRows.length === 2, 'admin check-in audit export mock must filter ticket and date range')
assert(checkInAuditRows.some((row) => row.action === 'UNDO_CHECK_IN'), 'admin check-in audit export mock must include undo action rows')
assert(checkInAuditRows.some((row) => row.reason === '现场误核销'), 'admin check-in audit export mock must include undo reason')
const checkInAuditReasonRows = listMockAdminCheckInAuditLogExportRows({ ticketCode: '2606280001A', reason: ' 误核 ' })
assert(checkInAuditReasonRows.length === 1, 'admin check-in audit export mock must narrow rows by reason')
assert(checkInAuditReasonRows[0]?.reason === '现场误核销', 'admin check-in audit export mock reason filter must keep matching undo reason')
assert(
  !JSON.stringify(listMockAdminCheckInAuditLogExportRows()).match(/adminUserId|buyerPhone|idNumber|session|csrf|password|hash|SQL|13911112222/),
  'admin check-in audit export mock must not expose sensitive fields',
)
try {
  listMockAdminCheckInAuditLogExportRows({ dateFrom: '2026-06-29', dateTo: '2026-06-28' })
  assert(false, 'admin check-in audit export mock must reject inverted date range')
} catch (error) {
  assert(error.code === 'ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID', 'admin check-in audit export mock must mirror API date range error code')
}
const {
  buildAdminCheckInAuditCsvText,
  escapeCheckInAuditCsvCell,
  neutralizeCheckInAuditCsvFormulaText,
} = loadRuntimeFunctions(adminCheckInAuditExportCsv.sourceFile, [
  'adminCheckInLogCsvHeaders',
  'sanitizeCsvText',
  'neutralizeCheckInAuditCsvFormulaText',
  'escapeCheckInAuditCsvCell',
  'buildAdminCheckInAuditCsvText',
])
assert(neutralizeCheckInAuditCsvFormulaText('=cmd') === "'=cmd", 'admin check-in audit CSV text starting with = must be neutralized')
assert(neutralizeCheckInAuditCsvFormulaText(' +cmd') === "' +cmd", 'admin check-in audit CSV text with leading spaces before + must be neutralized')
assert(neutralizeCheckInAuditCsvFormulaText('\u0001\u007F=cmd') === "'=cmd", 'admin check-in audit CSV text must sanitize control chars before formula checks')
assert(escapeCheckInAuditCsvCell('bad,"cell"') === '"bad,""cell"""', 'admin check-in audit CSV text must escape quoted cells')
const checkInAuditCsvText = buildAdminCheckInAuditCsvText([
  {
    orderNo: '\u0001\u007F=1+1',
    itemNo: 'bad,item',
    ticketCode: 'TK-1',
    action: 'CHECK_IN',
    reason: '=误核销',
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'bad,"request"',
    createdAt: '2026-06-30T10:00:00+08:00',
  },
])
assert(checkInAuditCsvText.startsWith('\ufefforderNo,itemNo,ticketCode,action,reason'), 'admin check-in audit CSV mock must include BOM and reason column')
assertContains(checkInAuditCsvText, "'=1+1", 'admin check-in audit CSV formula-like text must be neutralized after control cleanup')
assertContains(checkInAuditCsvText, "'=误核销", 'admin check-in audit CSV reason formulas must be neutralized')
assertContains(checkInAuditCsvText, '"bad,item"', 'admin check-in audit CSV text must quote comma cells')
assertContains(checkInAuditCsvText, '"bad,""request"""', 'admin check-in audit CSV text must escape quoted cells')
assert(!checkInAuditCsvText.includes('\u0001'), 'admin check-in audit CSV text must remove disallowed control characters')
assert(!checkInAuditCsvText.includes('\u007F'), 'admin check-in audit CSV text must remove DEL control characters')
assert(neutralizeCheckInAuditSpreadsheetText('=cmd') === "'=cmd", 'admin check-in audit XLSX text starting with = must be neutralized')
assert(neutralizeCheckInAuditSpreadsheetText(' +cmd') === "' +cmd", 'admin check-in audit XLSX text with leading spaces before + must be neutralized')

const checkInAuditXlsxBlob = buildAdminCheckInAuditLogsXlsxBlob([
  {
    orderNo: '\u0001=1+1',
    itemNo: 'bad\u0001<item>&',
    ticketCode: 'TK-1',
    action: 'CHECK_IN',
    reason: '+reason',
    operatorUsername: 'admin',
    operatorDisplayName: '运营管理员',
    requestId: 'request-1',
    createdAt: '2026-06-30T10:00:00+08:00',
  },
])
const checkInAuditXlsxBytes = new Uint8Array(await checkInAuditXlsxBlob.arrayBuffer())
const checkInAuditWorksheetXml = readStoreZipEntryText(checkInAuditXlsxBytes, 'xl/worksheets/sheet1.xml')
assert(
  checkInAuditXlsxBlob.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'admin check-in audit mock XLSX blob must use XLSX content type',
)
assert(checkInAuditXlsxBytes[0] === 0x50 && checkInAuditXlsxBytes[1] === 0x4B, 'admin check-in audit mock XLSX must be a ZIP payload')
assertContains(checkInAuditWorksheetXml, '&apos;=1+1', 'admin check-in audit mock XLSX formula-like text must be neutralized')
assertContains(checkInAuditWorksheetXml, '&apos;+reason', 'admin check-in audit mock XLSX reason formulas must be neutralized')
assert(!checkInAuditWorksheetXml.includes('<t>=1+1</t>'), 'admin check-in audit mock XLSX must neutralize values after XML control character cleanup')
assertContains(checkInAuditWorksheetXml, 'bad&lt;item&gt;&amp;', 'admin check-in audit mock XLSX XML text must be escaped')
assert(!checkInAuditWorksheetXml.includes('\u0001'), 'admin check-in audit mock XLSX XML text must remove disallowed control characters')
assertContains(adminOrderQueries.text, 'const normalizedOrderNo = orderNo?.trim() ??', 'admin order detail trims order number')
assertContains(adminOrderQueries.text, 'adminOrderQueryKeys.detail(normalizedOrderNo)', 'admin order detail key uses trimmed order number')
assertContains(adminOrderQueries.text, 'adminOrdersApi.detail(normalizedOrderNo)', 'admin order detail API uses trimmed order number')
assertContains(adminWorkbench.text, 'className="page-heading admin-heading"', 'admin page heading visual boundary class')
assertContains(adminWorkbench.text, 'export function AdminLoginGate', 'admin login gate must be a standalone render path')
assertContains(adminWorkbench.text, 'className="admin-login-gate"', 'admin login gate visual class')
assertContains(adminWorkbench.text, 'className="admin-workbench-grid is-authenticated"', 'admin workbench only renders after authentication')
assertContains(adminWorkbench.text, 'xl={24}', 'admin authenticated panels use full width')
assertContains(adminWorkbench.text, 'admin-access-card', 'admin access panel visual class')
assertContains(adminWorkbench.text, 'className="admin-access-summary"', 'admin authenticated access summary visual class')
assertContains(adminWorkbench.text, 'AdminOperationsWorkflowStrip', 'admin workbench exposes operations workflow strip')
assertContains(adminWorkbench.text, '先读数据，再管理票种，最后执行状态变更并回到审计证据', 'admin workbench operation workflow heading')
assertContains(adminWorkbench.text, '1. 看报表', 'admin workbench workflow starts from reports')
assertContains(adminWorkbench.text, '2. 管票种', 'admin workbench workflow includes ticket management')
assertContains(adminWorkbench.text, '3. 查订单', 'admin workbench workflow includes order read-model')
assertContains(adminWorkbench.text, '4. 做变更', 'admin workbench workflow includes guarded mutations')
assertContains(adminWorkbench.text, '5. 留证据', 'admin workbench workflow ends with audit evidence')
assertContains(adminWorkbench.text, 'AdminOperationsBoundaryStrip', 'admin workbench exposes operations boundary strip')
assertContains(adminWorkbench.text, '后台操作按只读视图、状态变更、审计导出分区推进', 'admin workbench operation boundary heading')
assertContains(adminWorkbench.text, '不展示完整手机号或证件号', 'admin workbench report boundary sensitive copy')
assertContains(adminWorkbench.text, '由后端计算状态、金额和库存', 'admin workbench backend-computed mutation boundary copy')
assertContains(adminWorkbench.text, '错误态保留错误码和请求编号', 'admin workbench audit export error handling copy')
assertContains(adminWorkbench.text, 'function AdminPageContent', 'admin workbench must split admin sections by active page')
assertContains(adminWorkbench.text, "activePage === 'reports'", 'admin workbench must render reports as an admin subpage')
assertContains(adminWorkbench.text, "activePage === 'orders'", 'admin workbench must render orders as an admin subpage')
assertContains(adminWorkbench.text, "activePage === 'audit'", 'admin workbench must render audit as an admin subpage')
assertContains(adminWorkbench.text, 'AdminOverviewPage', 'admin workbench must keep overview as a navigation hub')
assertContains(adminWorkbench.text, 'admin-page-entry-card', 'admin overview must expose page entry cards instead of all feature panels')
assertContains(adminWorkbench.text, '<AdminReportsPanel onOpenProfile={onOpenProfile} />', 'admin workbench composes reports subpage')
assertContains(adminWorkbench.text, '<AdminOrdersPanel onOpenProfile={onOpenProfile} />', 'admin workbench composes orders subpage')
assertContains(adminWorkbench.text, '<AdminAuditPanel onOpenProfile={onOpenProfile} />', 'admin workbench composes audit subpage')
assertContains(adminReportsPanel.text, 'className="admin-report-page"', 'admin report workspace visual class')
assertContains(adminOrdersPanel.text, 'className="admin-order-page"', 'admin orders workspace visual class')
assertContains(adminAuditPanel.text, 'className="admin-audit-page"', 'admin audit workspace visual class')
assertContains(adminExportJobsPanel.text, '异步导出任务', 'admin export jobs panel heading')
assertContains(adminExportJobsPanel.text, '创建任务必须走管理员会话和防伪校验', 'admin export jobs create CSRF boundary copy')
assertContains(adminExportJobsPanel.text, '不提交管理员内部编号、任务状态、文件名、存储位置或下载链接', 'admin export jobs internal field boundary copy')
assertContains(adminExportJobsPanel.text, 'exportType', 'admin export jobs panel exposes exportType selection')
assertContains(adminExportJobsPanel.text, 'fileFormat', 'admin export jobs panel exposes fileFormat selection')
assertContains(adminExportJobsPanel.text, 'downloadAdminExportJobFile', 'admin export jobs panel uses download boundary helper')
assertContains(adminExportJobsPanel.text, '<AdminExportJobCreateToolbar', 'admin export jobs panel composes extracted create toolbar')
assertContains(adminExportJobsPanel.text, '<AdminExportJobTable', 'admin export jobs panel composes extracted table')
assertContains(adminExportJobDisplay.text, 'buildAdminExportJobFilters', 'admin export job display owns filter whitelist builder')
assertContains(adminExportJobDisplay.text, "{ label: '支付对账', value: 'PAYMENT_RECONCILIATION' }", 'admin export jobs type options include payment reconciliation')
assertContains(adminExportJobDisplay.text, "exportType === 'CHECK_IN_FAILURE_AUDIT' && failureCode", 'admin export job filters gate failure code by export type')
assertContains(adminExportJobDisplay.text, "exportType === 'REFUND_AUDIT' && refundType", 'admin export job filters gate refund type by export type')
assertContains(adminExportJobCreateToolbar.text, 'AdminExportJobCreateToolbar', 'admin export job create toolbar extracted')
assertContains(adminExportJobCreateToolbar.text, 'supportsTicketCode(createExportType)', 'admin export job create toolbar gates ticket filters')
assertContains(adminExportJobTable.text, 'AdminExportJobTable', 'admin export job table extracted')
assertContains(adminExportJobTable.text, "disabled={job.status !== 'SUCCEEDED' || !job.fileName}", 'admin export job table keeps download boundary')
assertContains(adminExportJobQueries.text, 'VITE_ADMIN_EXPORT_JOBS_MODE', 'admin export jobs mode toggle')
assertContains(adminExportJobQueries.text, "import.meta.env.VITE_ADMIN_EXPORT_JOBS_MODE === 'mock' ? 'mock' : 'api'", 'admin export jobs default to API')
assertContains(adminExportJobQueries.text, "['admin-export-jobs', mode, 'list'", 'admin export jobs query key includes mode')
assertContains(adminExportJobQueries.text, 'normalizeAdminExportJobCreateRequest', 'admin export jobs create request normalization')
assertContains(adminExportJobQueries.text, 'params.fileFormat', 'admin export jobs list normalization keeps fileFormat filter')
assertContains(adminExportJobQueries.text, 'adminExportJobsApi.create(normalizedBody)', 'admin export jobs API create path')
assertContains(adminExportJobQueries.text, 'createMockAdminExportJob(normalizedBody)', 'admin export jobs mock create path')
assertContains(adminExportJobMockData.text, 'mock-export-job-order-csv-260701', 'admin export jobs mock succeeded row')
assertContains(adminExportJobMockData.text, 'mock-export-job-failure-csv-260701', 'admin export jobs mock failed row')
assertContains(adminExportJobMockData.text, 'params.fileFormat && job.fileFormat !== params.fileFormat', 'admin export jobs mock list honors fileFormat filter')
assertContains(adminExportJobMockData.text, "status: 'PENDING'", 'admin export jobs mock create returns pending task')
assert(!adminExportJobsPanel.text.includes('adminUserId:'), 'admin export jobs panel must not submit adminUserId')
assert(!adminExportJobsPanel.text.includes('storageKey:'), 'admin export jobs panel must not submit storageKey')
assertContains(appCss.text, "@import './features/admin/admin.css';", 'app css must compose admin domain styles')
assertContains(appCss.text, "@import './features/admin/adminReports.css';", 'app css must compose admin report domain styles')
assert(
  appCss.text.indexOf("@import './features/admin/admin.css';") <
    appCss.text.indexOf("@import './features/admin/adminReports.css';"),
  'app css must load admin report domain styles after shared admin styles so report grid overrides remain stable',
)
assertContains(adminAppShell.text, 'adminNavItems', 'admin shell must define admin page navigation')
assertContains(adminAppShell.text, "page: 'tickets'", 'admin shell navigation includes tickets page')
assertContains(adminAppShell.text, "page: 'reports'", 'admin shell navigation includes reports page')
assertContains(adminAppShell.text, "page: 'orders'", 'admin shell navigation includes orders page')
assertContains(adminAppShell.text, "page: 'audit'", 'admin shell navigation includes audit page')
assertContains(adminAppShell.text, 'onPageChange(item.page)', 'admin mobile navigation must switch admin subpages')
assertContains(adminAppShell.text, 'className="admin-mobile-tabbar"', 'admin shell must render mobile tabbar')
assertContains(adminWorkbench.text, "page: 'reports' as const", 'admin overview exposes report entry')
assertContains(adminWorkbench.text, "page: 'tickets' as const", 'admin overview exposes tickets entry')
assertContains(adminWorkbench.text, "page: 'orders' as const", 'admin overview exposes order entry')
assertContains(adminWorkbench.text, "page: 'audit' as const", 'admin overview exposes audit entry')
assertContains(adminBatchCheckInPanel.text, 'id="admin-mutations"', 'admin workbench exposes mutation anchor')
assertContains(appLayoutCss.text, '.admin-mobile-tabbar', 'app layout css must style admin mobile tabbar')
assertContains(appLayoutCss.text, '.admin-mobile-tabbar button.is-active', 'admin mobile tabbar must highlight active subpage')
assertContains(adminCss.text, '.admin-heading', 'admin css must include page-specific heading rules')
assertContains(adminCss.text, '.admin-workbench-grid.is-authenticated', 'admin css must include authenticated workbench layout rules')
assertContains(adminCss.text, '.admin-access-summary', 'admin css must include compact authenticated access summary')
assertContains(adminCss.text, '@media (max-width: 1200px)', 'admin authenticated access summary must collapse before medium desktop widths overflow')
assertContains(adminCss.text, '.admin-operations-workflow-strip', 'admin operations workflow strip styling')
assertContains(adminCss.text, '.admin-operations-workflow-grid', 'admin operations workflow responsive grid')
assertContains(adminCss.text, '.admin-operations-boundary-strip', 'admin operations boundary strip styling')
assertContains(adminCss.text, '.admin-operations-boundary-grid', 'admin operations boundary responsive grid')
assertContains(adminCss.text, '.admin-page-entry-grid', 'admin overview page entry grid styling')
assertContains(adminCss.text, '.admin-export-jobs-panel', 'admin export jobs panel styling')
assertContains(adminCss.text, '.admin-export-job-table .ant-table-content', 'admin export jobs table must scroll internally')
assertContains(adminCss.text, '.admin-export-job-create-action', 'admin export jobs mobile action sizing')
assertContains(adminCss.text, '.admin-operation-card .ant-card-body', 'admin operation card density rules')
assertContains(adminCss.text, '.admin-check-in-log-export-control', 'admin css must size check-in audit export filters')
assertContains(adminCss.text, '.admin-check-in-failure-log-control', 'admin css must size check-in failure audit filters')
assertContains(adminReportCss.text, '.admin-report-toolbar', 'admin report css must own report filter layout')
assertContains(adminReportCss.text, '.admin-report-chart-grid', 'admin report css must own report chart grid layout')
assertContains(adminReportsPanel.text, 'admin-report-chart-grid', 'admin reports panel must group revenue, sales and payment charts')
assertContains(adminReportsPanel.text, 'admin-report-metrics', 'admin reports panel must keep summary metrics grouped')
assertContains(adminReportCss.text, '.admin-report-payment-card', 'admin report css must own payment reconciliation layout')
assertContains(adminReportCss.text, '.admin-report-summary-table', 'admin report css must keep report summaries structured')
assertContains(adminReportCss.text, '@media (max-width: 991px)', 'admin report css must keep report tablet collapse rules')
assertContains(adminReportCss.text, '@media (max-width: 560px)', 'admin report css must keep report mobile collapse rules')
assertContains(adminOrdersPanel.text, 'useAdminOrderDetailQuery(selectedOrderNo)', 'admin orders panel detail read-model query')
assertContains(adminOrdersPanel.text, 'useAdminOrdersQuery(queryParams)', 'admin orders panel list read-model query')
assertContains(adminOrdersPanel.text, "placeholder=\"搜索订单号\"", 'admin orders panel order number filter')
assertContains(adminOrdersPanel.text, 'orderStatusOptions.map', 'admin orders panel status filter')
assertContains(adminOrdersPanel.text, 'pageSize = 10', 'admin orders panel keeps bounded page size')
assertContains(adminOrdersPanel.text, 'useAdminCheckInMutation()', 'admin orders panel check-in mutation')
assertContains(adminOrdersPanel.text, 'useAdminFullRefundMutation()', 'admin orders panel full refund mutation')
assertContains(adminOrdersPanel.text, 'checkInMutation.mutate({ ticketCode: item.ticketCode })', 'admin order detail check-in submits ticket code only')
assertContains(adminOrdersPanel.text, "fullRefundMutation.mutate({ orderNo: selectedDetail.orderNo, reason: '后台发起整单退款' })", 'admin order detail full refund submits order number and reason only')
assertContains(adminOrdersPanel.text, 'className="admin-order-detail-card"', 'admin orders panel renders inline detail card')
assertContains(adminOrdersPanel.text, 'buyerPhoneMasked', 'admin orders panel masked phone display')
assertContains(adminOrderDisplay.text, 'export function canCheckInItem', 'admin order display helper exposes check-in state guard')
assertContains(adminOrderDisplay.text, 'export function canFullRefundOrder', 'admin order display helper exposes full refund state guard')
assertContains(adminOrderDisplay.text, 'export function canPartialRefundOrder', 'admin order display helper exposes partial refund state guard')
assertContains(adminOrderDisplay.text, 'export function canPartialRefundItem', 'admin order display helper exposes partial refund item guard')
assertContains(adminOrderDetailDrawer.text, '<AdminOrderDetailSummary detail={detail} />', 'admin order detail drawer composes summary component')
assertContains(adminOrderDetailDrawer.text, '<AdminOrderItemsTable', 'admin order detail drawer composes items table component')
assertContains(adminOrderDetailDrawer.text, '<AdminOrderRefundPanels', 'admin order detail drawer composes refund panels component')
assertContains(adminOrderDetailDrawer.text, '<AdminRefundAuditPanel', 'admin order detail drawer composes refund audit component')
assertContains(adminOrderDetailSummary.text, 'admin-order-state-card', 'admin order detail summary must expose mutation-oriented state card')
assertContains(adminOrderDetailSummary.text, 'canCheckInItem(detail, item)', 'admin order detail summary must derive checkable count from state machine')
assertContains(adminOrderItemsTable.text, 'canCheckInItem(detail, item)', 'admin order items table applies check-in state guard')
assertContains(adminOrderRefundPanels.text, 'canFullRefundOrder(detail)', 'admin order refund panels apply full refund state guard')
assertContains(adminOrderRefundPanels.text, 'canPartialRefundOrder(detail)', 'admin order refund panels apply partial refund state guard')
assertContains(adminOrderRefundPanels.text, 'canPartialRefundItem(detail, item)', 'admin order refund panels apply partial refund item guard')
assertContains(adminOrderRefundPanels.text, 'canSubmitPartialRefundItems(detail, partialRefundItemNos)', 'admin order refund panels validate selected partial refund items before submit')
assertContains(adminOrderRefundPanels.text, 'admin-refund-state-path', 'admin order refund panels must show refund state-machine path')
assertContains(adminOrderRefundPanels.text, '已支付订单', 'admin full refund path must include paid-order rule')
assertContains(adminOrderRefundPanels.text, '全部未使用', 'admin full refund path must include unused-item rule')
assertContains(adminOrderRefundPanels.text, '符合退款规则', 'admin full refund path must include eligibility rule')
assertContains(adminOrderItemsTable.text, 'className="admin-check-in-action"', 'admin order detail check-in action')
assertContains(adminBatchCheckInPanel.text, '批量票码核验', 'admin batch check-in panel title')
assertContains(adminBatchCheckInPanel.text, '状态变更只提交待核验票码', 'admin batch check-in mutation boundary copy')
assertContains(adminBatchCheckInPanel.text, '逐票业务失败不阻断同批其他票码', 'admin batch check-in partial failure boundary copy')
assertContains(adminBatchCheckInPanel.text, 'className="admin-batch-check-in-action"', 'admin batch check-in action class')
assertContains(adminBatchCheckInPanel.text, '最多 50 个', 'admin batch check-in count boundary copy')
assertContains(adminBatchCheckInPanel.text, 'parseTicketCodes(ticketCodeText)', 'admin batch check-in parses user input')
assertContains(adminBatchCheckInPanel.text, 'ApiErrorDetails', 'admin batch check-in fixed error details')
assertNotContains(adminBatchCheckInPanel.text, 'adminUserId', 'admin batch check-in panel internal admin id')
assertNotContains(adminBatchCheckInPanel.text, 'orderId', 'admin batch check-in panel internal order id')
assertNotContains(adminBatchCheckInPanel.text, 'session', 'admin batch check-in panel session field')
assertNotContains(adminBatchCheckInPanel.text, 'csrf', 'admin batch check-in panel csrf field')
assertNotContains(adminBatchCheckInPanel.text, 'password', 'admin batch check-in panel password field')
assertNotContains(adminBatchCheckInPanel.text, 'hash', 'admin batch check-in panel hash field')
assertNotContains(adminBatchCheckInPanel.text, 'SQL', 'admin batch check-in panel SQL text')
assertContains(adminBatchUndoCheckInPanel.text, '批量撤销核验', 'admin batch undo check-in panel title')
assertContains(adminBatchUndoCheckInPanel.text, '状态变更只提交待撤销票码和可选原因', 'admin batch undo check-in mutation boundary copy')
assertContains(adminBatchUndoCheckInPanel.text, '逐票业务失败不阻断同批其他票码', 'admin batch undo check-in partial failure boundary copy')
assertContains(adminBatchUndoCheckInPanel.text, 'className="admin-batch-undo-check-in-action"', 'admin batch undo check-in action class')
assertContains(adminBatchUndoCheckInPanel.text, 'className="admin-batch-undo-check-in-reason-input"', 'admin batch undo check-in reason input class')
assertContains(adminBatchUndoCheckInPanel.text, 'aria-label="批量撤销核验原因输入"', 'admin batch undo check-in reason input accessible name')
assertContains(adminBatchUndoCheckInPanel.text, 'maxLength={100}', 'admin batch undo check-in reason max length')
assertContains(adminBatchUndoCheckInPanel.text, '本次原因', 'admin batch undo check-in result confirms reason')
assertContains(adminBatchUndoCheckInPanel.text, '最多 50 个', 'admin batch undo check-in count boundary copy')
assertContains(adminBatchUndoCheckInPanel.text, 'parseTicketCodes(ticketCodeText)', 'admin batch undo check-in parses user input')
assertContains(adminBatchUndoCheckInPanel.text, 'ApiErrorDetails', 'admin batch undo check-in fixed error details')
assertNotContains(adminBatchUndoCheckInPanel.text, 'adminUserId', 'admin batch undo check-in panel internal admin id')
assertNotContains(adminBatchUndoCheckInPanel.text, 'orderId', 'admin batch undo check-in panel internal order id')
assertNotContains(adminBatchUndoCheckInPanel.text, 'session', 'admin batch undo check-in panel session field')
assertNotContains(adminBatchUndoCheckInPanel.text, 'csrf', 'admin batch undo check-in panel csrf field')
assertNotContains(adminBatchUndoCheckInPanel.text, 'password', 'admin batch undo check-in panel password field')
assertNotContains(adminBatchUndoCheckInPanel.text, 'hash', 'admin batch undo check-in panel hash field')
assertNotContains(adminBatchUndoCheckInPanel.text, 'SQL', 'admin batch undo check-in panel SQL text')
assertContains(adminOrderRefundPanels.text, 'className="admin-full-refund-action"', 'admin order detail full refund action')
assertContains(adminOrderRefundPanels.text, 'className="admin-partial-refund-action"', 'admin order detail partial refund action')
assertContains(adminOrderDetailDrawer.text, '票码核验成功', 'admin order detail check-in success message')
assertContains(adminOrderDetailDrawer.text, '整单退款成功', 'admin order detail full refund success message')
assertContains(adminOrderDetailDrawer.text, '部分退款成功', 'admin order detail partial refund success message')
assertContains(adminOrderDetailDrawer.text, 'AdminCheckInErrorDetails', 'admin order detail check-in fixed error message')
assertContains(adminOrderDetailErrorDetails.text, '当前票码暂时无法核验', 'admin order detail check-in fixed error message copy')
assertContains(adminOrderDetailDrawer.text, 'AdminRefundErrorDetails', 'admin order detail full refund fixed error message')
assertContains(adminOrderDetailErrorDetails.text, '当前订单暂时无法退款', 'admin order detail full refund fixed error message copy')
assertContains(adminOrderDetailDrawer.text, 'AdminPartialRefundErrorDetails', 'admin order detail partial refund fixed error message')
assertContains(adminOrderDetailErrorDetails.text, '当前票项暂时无法部分退款', 'admin order detail partial refund fixed error message copy')
assertContains(adminRefundAuditPanel.text, 'AdminRefundAuditErrorDetails', 'admin order detail refund audit fixed error message')
assertContains(adminOrderDetailErrorDetails.text, '退款审计日志暂时无法读取', 'admin order detail refund audit fixed error message copy')
assertContains(adminOrderDetailErrorDetails.text, 'apiError.requestId', 'admin order detail operation errors preserve request id')
assertContains(adminRefundAuditPanel.text, '退款审计日志', 'admin order detail refund audit panel')
assertContains(adminOrderRefundPanels.text, '状态变更只提交退款原因', 'admin full refund mutation boundary')
assertContains(adminOrderRefundPanels.text, '退款金额、票项和库存回补由后端计算', 'admin full refund backend-computed boundary')
assertContains(adminOrderRefundPanels.text, '状态变更只提交选中的票项和退款原因', 'admin partial refund mutation boundary')
assertContains(adminOrderRefundPanels.text, '金额、状态和库存由后端计算', 'admin partial refund backend-computed boundary')
assertContains(adminRefundAuditPanel.text, '只读查看，不提交操作人、金额或状态。', 'admin refund audit read-only boundary')
assertContains(adminRefundAuditPanel.text, 'operatorDisplayName', 'admin refund audit operator display field')
assertContains(adminRefundAuditPanel.text, 'requestId', 'admin refund audit request id display')
assertContains(adminRefundAuditPanel.text, '暂无退款审计记录', 'admin refund audit empty state')
assertContains(adminRefundAuditPanel.text, 'log.requestId ?? log.refundedItemNos.join', 'admin refund audit row key collision guard')
assertContains(adminOrderRefundPanels.text, 'className="admin-detail-disabled-action"', 'admin order detail disabled actions')
assertContains(adminOrderRefundPanels.text, '退款不可用', 'admin order detail refund disabled action')
assertNotContains(adminOrderDetailSurfaceText, 'adminUserId', 'admin order detail surface internal admin id')
assertNotContains(adminOrderDetailSurfaceText, 'idNumber', 'admin order detail surface id number field')
assertNotContains(adminOrderDetailSurfaceText, 'password', 'admin order detail surface password field')
assertNotContains(adminOrderDetailSurfaceText, 'hash', 'admin order detail surface hash field')
assertNotContains(adminOrderDetailSurfaceText, 'SQL', 'admin order detail surface SQL text')
assertContains(adminRefundLogPanel.text, 'useAdminRefundAuditLogSearchQuery(queryParams)', 'admin refund audit search panel query')
assertContains(adminRefundLogPanel.text, '退款审计检索', 'admin refund audit search panel title')
assertContains(adminRefundLogPanel.text, '跨订单只读检索', 'admin refund audit search read-only boundary')
assertContains(adminRefundLogPanel.text, 'downloadAdminRefundAuditLogsCsv(exportParams)', 'admin refund audit CSV export action')
assertContains(adminRefundLogPanel.text, 'className="admin-refund-log-csv-export-action"', 'admin refund audit CSV export button class')
assertContains(adminRefundLogPanel.text, '导出退款 CSV', 'admin refund audit CSV export button copy')
assertContains(adminRefundLogPanel.text, 'downloadAdminRefundAuditLogsXlsx(exportParams)', 'admin refund audit XLSX export action')
assertContains(adminRefundLogPanel.text, 'className="admin-refund-log-xlsx-export-action"', 'admin refund audit XLSX export button class')
assertContains(adminRefundLogPanel.text, '导出退款 XLSX', 'admin refund audit XLSX export button copy')
assertContains(adminRefundLogPanel.text, '不提交分页参数', 'admin refund audit XLSX export pagination boundary copy')
assertContains(adminRefundLogPanel.text, "import { AdminRefundAuditToolbar } from './components/AdminRefundAuditToolbar'", 'admin refund audit search panel composes toolbar')
assertContains(adminRefundLogPanel.text, "import { AdminRefundAuditTable } from './components/AdminRefundAuditTable'", 'admin refund audit search panel composes table')
assertContains(adminRefundAuditToolbar.text, "placeholder=\"搜索审计订单号\"", 'admin refund audit search order filter')
assertContains(adminRefundAuditToolbar.text, "placeholder=\"操作人用户名\"", 'admin refund audit search operator filter')
assertContains(adminRefundAuditToolbar.text, "placeholder=\"开始日期\"", 'admin refund audit search dateFrom filter')
assertContains(adminRefundAuditToolbar.text, "placeholder=\"结束日期\"", 'admin refund audit search dateTo filter')
assertContains(adminRefundAuditToolbar.text, 'className="admin-refund-log-type-select admin-refund-log-control"', 'admin refund audit search type filter class')
assertContains(adminRefundAuditTable.text, 'pagination={{', 'admin refund audit search table pagination')
assertContains(adminRefundLogPanel.text, 'setPage(1)', 'admin refund audit search filters reset to first page')
assertContains(adminRefundAuditToolbar.text, 'admin-refund-log-reset-action', 'admin refund audit search reset action class')
assertContains(adminRefundAuditToolbar.text, '重置审计筛选', 'admin refund audit search reset action')
assertContains(adminRefundAuditDisplay.text, 'export function refundTypeTag', 'admin refund audit display helper owns refund type tag')
assertContains(adminRefundAuditDisplay.text, 'export function amountLabel', 'admin refund audit display helper owns amount label')
assertContains(adminRefundAuditErrorDetails.text, '退款审计日志暂时无法检索', 'admin refund audit fixed error message')
assertContains(adminRefundAuditCsvErrorDetails.text, '退款审计 CSV 暂时无法导出', 'admin refund audit CSV export fixed error message')
assertContains(adminRefundAuditCsvErrorDetails.text, 'AdminExportErrorDetails', 'admin refund audit CSV export uses shared export error details')
assertContains(adminRefundAuditXlsxErrorDetails.text, '退款审计 XLSX 暂时无法导出', 'admin refund audit export fixed error message')
assertContains(adminRefundAuditXlsxErrorDetails.text, 'AdminExportErrorDetails', 'admin refund audit XLSX export uses shared export error details')
assertContains(adminCheckInAuditExportPanel.text, '核验审计导出', 'admin check-in audit export panel title')
assertContains(adminCheckInAuditExportPanel.text, 'downloadAdminCheckInAuditLogsCsv(exportParams)', 'admin check-in audit CSV export action')
assertContains(adminCheckInAuditExportPanel.text, 'className="admin-check-in-log-csv-export-action"', 'admin check-in audit CSV export button class')
assertContains(adminCheckInAuditExportPanel.text, '导出核验 CSV', 'admin check-in audit CSV export button copy')
assertContains(adminCheckInAuditExportPanel.text, 'downloadAdminCheckInAuditLogsXlsx(exportParams)', 'admin check-in audit export action')
assertContains(adminCheckInAuditExportPanel.text, 'className="admin-check-in-log-xlsx-export-action"', 'admin check-in audit XLSX export button class')
assertContains(adminCheckInAuditExportPanel.text, '导出核验 XLSX', 'admin check-in audit XLSX export button copy')
assertContains(adminCheckInAuditExportPanel.text, 'CSV/XLSX', 'admin check-in audit export read-only copy mentions both formats')
assertContains(adminCheckInAuditExportPanel.text, '只读导出', 'admin check-in audit export read-only boundary')
assertContains(adminCheckInAuditExportPanel.text, 'placeholder="票码"', 'admin check-in audit ticket filter')
assertContains(adminCheckInAuditExportPanel.text, 'placeholder="订单号"', 'admin check-in audit order filter')
assertContains(adminCheckInAuditExportPanel.text, 'placeholder="操作人账号"', 'admin check-in audit operator filter')
assertContains(adminCheckInAuditCsvExportErrorDetails.text, '核验审计 CSV 暂时无法导出', 'admin check-in audit CSV export fixed error message')
assertContains(adminCheckInAuditCsvExportErrorDetails.text, 'AdminExportErrorDetails', 'admin check-in audit CSV export uses shared export error details')
assertContains(adminCheckInAuditExportErrorDetails.text, '核验审计 XLSX 暂时无法导出', 'admin check-in audit export fixed error message')
assertContains(adminCheckInAuditExportErrorDetails.text, 'AdminExportErrorDetails', 'admin check-in audit XLSX export uses shared export error details')
assertContains(adminCheckInFailureLogPanel.text, 'useAdminCheckInFailureAuditLogSearchQuery(queryParams)', 'admin check-in failure audit search panel query')
assertContains(adminCheckInFailureLogPanel.text, '核验失败审计', 'admin check-in failure audit search panel title')
assertContains(adminCheckInFailureLogPanel.text, '只读检索', 'admin check-in failure audit search read-only boundary')
assertContains(adminCheckInFailureLogPanel.text, '失败码、票码、操作人和日期', 'admin check-in failure audit search filter copy')
assertContains(adminCheckInFailureLogPanel.text, 'downloadAdminCheckInFailureAuditLogsCsv(exportParams)', 'admin check-in failure audit CSV export action')
assertContains(adminCheckInFailureLogPanel.text, 'className="admin-check-in-failure-log-csv-export-action"', 'admin check-in failure audit CSV export button class')
assertContains(adminCheckInFailureLogPanel.text, '导出失败 CSV', 'admin check-in failure audit CSV export button copy')
assertContains(adminCheckInFailureLogPanel.text, 'downloadAdminCheckInFailureAuditLogsXlsx(exportParams)', 'admin check-in failure audit XLSX export action')
assertContains(adminCheckInFailureLogPanel.text, 'className="admin-check-in-failure-log-xlsx-export-action"', 'admin check-in failure audit XLSX export button class')
assertContains(adminCheckInFailureLogPanel.text, '导出失败 XLSX', 'admin check-in failure audit XLSX export button copy')
assertContains(adminCheckInFailureLogPanel.text, 'CSV/XLSX', 'admin check-in failure audit export copy mentions both formats')
assertContains(adminCheckInFailureLogPanel.text, '不展示订单内部 id、手机号、证件号或查询语句', 'admin check-in failure audit sensitive field boundary copy')
assertContains(adminCheckInFailureAuditCsvErrorDetails.text, '核验失败审计 CSV 暂时无法导出', 'admin check-in failure audit CSV export fixed error message')
assertContains(adminCheckInFailureAuditCsvErrorDetails.text, 'AdminExportErrorDetails', 'admin check-in failure audit CSV export uses shared export error details')
assertContains(adminCheckInFailureAuditXlsxErrorDetails.text, '核验失败审计 XLSX 暂时无法导出', 'admin check-in failure audit XLSX export fixed error message')
assertContains(adminCheckInFailureAuditXlsxErrorDetails.text, 'AdminExportErrorDetails', 'admin check-in failure audit XLSX export uses shared export error details')
assertContains(adminCheckInFailureLogPanel.text, "import { AdminCheckInFailureAuditToolbar } from './components/AdminCheckInFailureAuditToolbar'", 'admin check-in failure audit panel composes toolbar')
assertContains(adminCheckInFailureLogPanel.text, "import { AdminCheckInFailureAuditTable } from './components/AdminCheckInFailureAuditTable'", 'admin check-in failure audit panel composes table')
assertContains(adminCheckInFailureLogPanel.text, 'setPage(1)', 'admin check-in failure audit filters reset to first page')
assertContains(adminCheckInFailureAuditToolbar.text, 'aria-label="核验失败码筛选"', 'admin check-in failure audit failure code filter')
assertContains(adminCheckInFailureAuditToolbar.text, 'aria-label="核验失败票码筛选"', 'admin check-in failure audit ticket input accessible name')
assertContains(adminCheckInFailureAuditToolbar.text, 'aria-label="核验失败操作人筛选"', 'admin check-in failure audit operator input accessible name')
assertContains(adminCheckInFailureAuditToolbar.text, 'aria-label="核验失败开始日期筛选"', 'admin check-in failure audit dateFrom input accessible name')
assertContains(adminCheckInFailureAuditToolbar.text, 'aria-label="核验失败结束日期筛选"', 'admin check-in failure audit dateTo input accessible name')
assertContains(adminCheckInFailureAuditToolbar.text, 'placeholder="失败票码"', 'admin check-in failure audit ticket filter')
assertContains(adminCheckInFailureAuditToolbar.text, 'placeholder="失败操作人用户名"', 'admin check-in failure audit operator filter')
assertContains(adminCheckInFailureAuditToolbar.text, 'placeholder="失败日期从"', 'admin check-in failure audit dateFrom filter')
assertContains(adminCheckInFailureAuditToolbar.text, 'placeholder="失败日期至"', 'admin check-in failure audit dateTo filter')
assertContains(adminCheckInFailureAuditToolbar.text, 'admin-check-in-failure-log-reset-action', 'admin check-in failure audit reset action class')
assertContains(adminCheckInFailureAuditToolbar.text, '重置失败筛选', 'admin check-in failure audit reset action')
assertContains(adminCheckInFailureAuditTable.text, 'pagination={{', 'admin check-in failure audit table pagination')
assertContains(adminCheckInFailureAuditTable.text, 'operatorDisplayName', 'admin check-in failure audit operator display field')
assertContains(adminCheckInFailureAuditTable.text, 'requestId', 'admin check-in failure audit request id display')
assertContains(adminCheckInFailureAuditDisplay.text, 'TICKET_NOT_FOUND', 'admin check-in failure audit display includes missing ticket code')
assertContains(adminCheckInFailureAuditDisplay.text, 'TICKET_ALREADY_USED', 'admin check-in failure audit display includes already-used code')
assertContains(adminCheckInFailureAuditDisplay.text, 'TICKET_NOT_CHECKABLE', 'admin check-in failure audit display includes not-checkable code')
assertContains(adminCheckInFailureAuditDisplay.text, 'TICKET_NOT_CHECKED_IN', 'admin check-in failure audit display includes not-checked-in undo code')
assertContains(adminCheckInFailureAuditDisplay.text, 'TICKET_UNDO_NOT_ALLOWED', 'admin check-in failure audit display includes undo-not-allowed code')
assertContains(adminCheckInFailureAuditErrorDetails.text, '核验失败审计暂时无法检索', 'admin check-in failure audit fixed error message')
assertNotContains(adminCheckInFailureAuditExportCsv.text, 'buyerPhone', 'admin check-in failure audit CSV export phone field')
assertNotContains(adminCheckInFailureAuditExportCsv.text, 'idNumber', 'admin check-in failure audit CSV export id number field')
assertNotContains(adminCheckInFailureAuditExportCsv.text, 'session', 'admin check-in failure audit CSV export session field')
assertNotContains(adminCheckInFailureAuditExportCsv.text, 'csrf', 'admin check-in failure audit CSV export csrf field')
assertNotContains(adminCheckInFailureAuditExportCsv.text, 'password', 'admin check-in failure audit CSV export password field')
assertNotContains(adminCheckInFailureAuditExportCsv.text, 'hash', 'admin check-in failure audit CSV export hash field')
assertNotContains(adminCheckInFailureAuditExportCsv.text, 'adminUserId', 'admin check-in failure audit CSV export internal admin id')
assertNotContains(adminCheckInFailureAuditExportXlsx.text, 'buyerPhone', 'admin check-in failure audit XLSX export phone field')
assertNotContains(adminCheckInFailureAuditExportXlsx.text, 'idNumber', 'admin check-in failure audit XLSX export id number field')
assertNotContains(adminCheckInFailureAuditExportXlsx.text, 'session', 'admin check-in failure audit XLSX export session field')
assertNotContains(adminCheckInFailureAuditExportXlsx.text, 'csrf', 'admin check-in failure audit XLSX export csrf field')
assertNotContains(adminCheckInFailureAuditExportXlsx.text, 'password', 'admin check-in failure audit XLSX export password field')
assertNotContains(adminCheckInFailureAuditExportXlsx.text, 'hash', 'admin check-in failure audit XLSX export hash field')
assertNotContains(adminCheckInFailureAuditExportXlsx.text, 'adminUserId', 'admin check-in failure audit XLSX export internal admin id')
assertNotContains(adminCheckInFailureAuditCsvErrorDetails.text, 'session', 'admin check-in failure audit CSV error details session field')
assertNotContains(adminCheckInFailureAuditCsvErrorDetails.text, 'csrf', 'admin check-in failure audit CSV error details csrf field')
assertNotContains(adminCheckInFailureAuditXlsxErrorDetails.text, 'session', 'admin check-in failure audit XLSX error details session field')
assertNotContains(adminCheckInFailureAuditXlsxErrorDetails.text, 'csrf', 'admin check-in failure audit XLSX error details csrf field')
assertNotContains(adminCheckInAuditExportCsv.text, 'buyerPhone', 'admin check-in audit CSV export phone field')
assertNotContains(adminCheckInAuditExportCsv.text, 'idNumber', 'admin check-in audit CSV export id number field')
assertNotContains(adminCheckInAuditExportCsv.text, 'session', 'admin check-in audit CSV export session field')
assertNotContains(adminCheckInAuditExportCsv.text, 'csrf', 'admin check-in audit CSV export csrf field')
assertNotContains(adminCheckInAuditExportCsv.text, 'password', 'admin check-in audit CSV export password field')
assertNotContains(adminCheckInAuditExportCsv.text, 'hash', 'admin check-in audit CSV export hash field')
assertNotContains(adminCheckInAuditExportCsv.text, 'adminUserId', 'admin check-in audit CSV export internal admin id')
assertNotContains(adminCheckInAuditExportXlsx.text, 'buyerPhone', 'admin check-in audit XLSX export phone field')
assertNotContains(adminCheckInAuditExportXlsx.text, 'idNumber', 'admin check-in audit XLSX export id number field')
assertNotContains(adminCheckInAuditExportXlsx.text, 'session', 'admin check-in audit XLSX export session field')
assertNotContains(adminCheckInAuditExportXlsx.text, 'csrf', 'admin check-in audit XLSX export csrf field')
assertNotContains(adminCheckInAuditExportXlsx.text, 'password', 'admin check-in audit XLSX export password field')
assertNotContains(adminCheckInAuditExportXlsx.text, 'hash', 'admin check-in audit XLSX export hash field')
assertNotContains(adminCheckInAuditExportXlsx.text, 'adminUserId', 'admin check-in audit XLSX export internal admin id')
assertNotContains(adminCheckInFailureLogPanel.text, "dateFrom: '2026-07-01'", 'admin check-in failure audit search panel must not hard-code default dateFrom')
assertNotContains(adminCheckInFailureLogPanel.text, "dateTo: '2026-07-01'", 'admin check-in failure audit search panel must not hard-code default dateTo')
assertNotContains(adminCheckInFailureLogMockData.text, 'buyerPhone', 'admin check-in failure audit mock phone field')
assertNotContains(adminCheckInFailureLogMockData.text, 'idNumber', 'admin check-in failure audit mock id number field')
assertNotContains(adminCheckInFailureLogMockData.text, 'session', 'admin check-in failure audit mock session field')
assertNotContains(adminCheckInFailureLogMockData.text, 'csrf', 'admin check-in failure audit mock csrf field')
assertNotContains(adminCheckInFailureLogMockData.text, 'password', 'admin check-in failure audit mock password field')
assertNotContains(adminCheckInFailureLogMockData.text, 'hash', 'admin check-in failure audit mock hash field')
assertNotContains(adminCheckInFailureLogMockData.text, 'adminUserId', 'admin check-in failure audit mock internal admin id')
assertNotContains(adminRefundAuditExportCsv.text, 'buyerPhone', 'admin refund audit CSV export phone field')
assertNotContains(adminRefundAuditExportCsv.text, 'idNumber', 'admin refund audit CSV export id number field')
assertNotContains(adminRefundAuditExportCsv.text, 'session', 'admin refund audit CSV export session field')
assertNotContains(adminRefundAuditExportCsv.text, 'csrf', 'admin refund audit CSV export csrf field')
assertNotContains(adminRefundAuditExportCsv.text, 'password', 'admin refund audit CSV export password field')
assertNotContains(adminRefundAuditExportCsv.text, 'hash', 'admin refund audit CSV export hash field')
assertNotContains(adminRefundAuditExportCsv.text, 'adminUserId', 'admin refund audit CSV export internal admin id')
assertNotContains(adminRefundAuditExportXlsx.text, 'buyerPhone', 'admin refund audit XLSX export phone field')
assertNotContains(adminRefundAuditExportXlsx.text, 'idNumber', 'admin refund audit XLSX export id number field')
assertNotContains(adminRefundAuditExportXlsx.text, 'session', 'admin refund audit XLSX export session field')
assertNotContains(adminRefundAuditExportXlsx.text, 'csrf', 'admin refund audit XLSX export csrf field')
assertNotContains(adminRefundAuditExportXlsx.text, 'password', 'admin refund audit XLSX export password field')
assertNotContains(adminRefundAuditExportXlsx.text, 'hash', 'admin refund audit XLSX export hash field')
assertNotContains(adminRefundAuditExportXlsx.text, 'adminUserId', 'admin refund audit XLSX export internal admin id')
assertContains(adminRefundAuditTable.text, 'operatorDisplayName', 'admin refund audit search operator display field')
assertContains(adminRefundAuditTable.text, 'requestId', 'admin refund audit search request id display')
assertContains(adminRefundLogPanel.text, '内部管理员 id', 'admin refund audit search internal id boundary copy')
assertNotContains(adminRefundLogPanel.text, "dateFrom: '2026-06-28'", 'admin refund audit search panel must not hard-code default dateFrom')
assertNotContains(adminRefundLogPanel.text, "dateTo: '2026-06-28'", 'admin refund audit search panel must not hard-code default dateTo')
assertNotContains(adminRefundAuditSurfaceText, 'buyerPhone', 'admin refund audit search UI surface phone field')
assertNotContains(adminRefundAuditSurfaceText, 'idNumber', 'admin refund audit search UI surface id number field')
assertNotContains(adminRefundAuditSurfaceText, 'adminUserId', 'admin refund audit search UI surface internal admin id')
assertNotContains(adminRefundAuditSurfaceText, 'SQL', 'admin refund audit search UI surface SQL text')
assertNotContains(adminRefundAuditSurfaceText, 'session', 'admin refund audit search UI surface session field')
assertNotContains(adminRefundAuditSurfaceText, 'CSRF', 'admin refund audit search UI surface CSRF field')
assertNotContains(adminRefundAuditSurfaceText, 'csrf', 'admin refund audit search UI surface csrf field')
assertNotContains(adminRefundAuditSurfaceText, 'password', 'admin refund audit search UI surface password field')
assertNotContains(adminRefundAuditSurfaceText, 'hash', 'admin refund audit search UI surface hash field')
assertNotContains(adminOrdersPanel.text, '{detail.buyerPhone}', 'admin order detail full phone field')
assertNotContains(adminOrderDetailSurfaceText, '{detail.buyerPhone}', 'admin order detail full phone field')
assertNotContains(adminOrderDetailSurfaceText, 'detail.buyerPhone}', 'admin order detail direct buyer phone render')
assertNotContains(adminOrderDetailSurfaceText, "dataIndex: 'buyerPhone'", 'admin order detail buyer phone column')
assertNotContains(adminOrderDisplay.text, 'buyerPhone', 'admin order display helper buyer phone field')
assertNotContains(adminOrdersPanel.text, 'order.buyerPhone}', 'admin order list full phone display')
assertNotContains(adminOrdersPanel.text, "dataIndex: 'buyerPhone'", 'admin order table full phone column')
assertNotContains(adminOrdersPanel.text, 'idNumber', 'admin orders panel id number field')
assertNotContains(adminOrdersPanel.text, '身份证号', 'admin orders panel id number label')
assertNotContains(adminOrderDetailSurfaceText, 'idNumber', 'admin order detail id number field')
assertNotContains(adminOrderDisplay.text, 'idNumber', 'admin order display helper id number field')
assertNotContains(adminOrdersPanel.text, 'adminUserId', 'admin orders panel internal admin id')
assertNotContains(adminOrderDetailSurfaceText, 'adminUserId', 'admin order detail internal admin id')
assertNotContains(adminOrderDisplay.text, 'adminUserId', 'admin order display helper internal admin id')
assertNotContains(adminOrdersPanel.text, 'SQL', 'admin orders panel SQL text')
assertNotContains(adminOrderDetailSurfaceText, 'SQL', 'admin order detail SQL text')
assertNotContains(adminOrderDetailSurfaceText, 'orderId', 'admin order detail internal order id')
assertNotContains(adminOrderDetailSurfaceText, 'session', 'admin order detail session field')
assertNotContains(adminOrderDetailSurfaceText, 'csrf', 'admin order detail csrf field')
assertNotContains(adminOrderDetailSurfaceText, 'password', 'admin order detail password field')
assertNotContains(adminOrderDetailSurfaceText, 'hash', 'admin order detail hash field')
assertNotContains(adminOrderDisplay.text, 'SQL', 'admin order display helper SQL text')
assertContains(adminReportQueries.text, 'VITE_ADMIN_REPORTS_MODE', 'admin reports mode env')
assertContains(adminReportQueries.text, "import.meta.env.VITE_ADMIN_REPORTS_MODE === 'mock' ? 'mock' : 'api'", 'admin reports default to API')
assertContains(adminReportQueries.text, "['admin-reports', mode, 'summary'", 'admin reports summary query key namespace')
assertContains(adminReportQueries.text, "['admin-reports', mode, 'payment-reconciliation'", 'admin reports payment reconciliation query key namespace')
assertContains(adminReportQueries.text, "['admin-reports', mode, 'hourly-trend'", 'admin reports hourly trend query key namespace')
assertContains(adminReportQueries.text, "['admin-reports', mode, 'monthly-trend'", 'admin reports monthly trend query key namespace')
assertContains(adminReportQueries.text, 'normalizeAdminTrendReportParams(params)', 'admin trend reports normalize includeEmpty params')
assertContains(adminReportQueries.text, 'includeEmpty: true', 'admin trend reports keep true includeEmpty in query key')
assertContains(adminReportQueries.text, "if (adminReportsMode === 'api')", 'admin reports API mode branch')
assertContains(adminReportQueries.text, 'adminReportsApi.summary(normalizedParams)', 'admin reports summary API client')
assertContains(adminReportQueries.text, 'adminReportsApi.paymentReconciliation(normalizedParams)', 'admin reports payment reconciliation API client')
assertContains(adminReportQueries.text, 'adminReportsApi.productBreakdown(normalizedParams)', 'admin reports product API client')
assertContains(adminReportQueries.text, 'adminReportsApi.dailyTrend(normalizedParams)', 'admin reports daily trend API client with trend params')
assertContains(adminReportQueries.text, 'adminReportsApi.hourlyTrend(normalizedParams)', 'admin reports hourly trend API client with trend params')
assertContains(adminReportQueries.text, 'adminReportsApi.monthlyTrend(normalizedParams)', 'admin reports monthly trend API client with trend params')
assertContains(adminReportQueries.text, 'getMockAdminReportSummary(normalizedParams)', 'admin reports mock summary client')
assertContains(adminReportQueries.text, 'getMockAdminPaymentReconciliation(normalizedParams)', 'admin reports mock payment reconciliation client')
assertContains(adminReportQueries.text, 'listMockAdminProductBreakdown(normalizedParams)', 'admin reports mock product client')
assertContains(adminReportQueries.text, 'listMockAdminDailyTrend(normalizedParams)', 'admin reports mock daily trend client')
assertContains(adminReportQueries.text, 'listMockAdminHourlyTrend(normalizedParams)', 'admin reports mock hourly trend client')
assertContains(adminReportQueries.text, 'listMockAdminMonthlyTrend(normalizedParams)', 'admin reports mock monthly trend client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.ordersCsv(normalizedParams)', 'admin reports CSV API client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.paymentReconciliationCsv(normalizedParams)', 'admin reports payment reconciliation CSV API client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.paymentReconciliationXlsx(normalizedParams)', 'admin reports payment reconciliation XLSX API client')
assertContains(adminReportExportCsv.text, 'adminReportsApi.productBreakdown(normalizedParams)', 'admin reports product breakdown export must load structured rows for localized file generation')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.ordersXlsx(normalizedParams)', 'admin reports XLSX API client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.dailyTrendCsv', 'admin daily trend CSV API client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.hourlyTrendCsv', 'admin hourly trend CSV API client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.monthlyTrendCsv', 'admin monthly trend CSV API client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.dailyTrendXlsx', 'admin daily trend XLSX API client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.hourlyTrendXlsx', 'admin hourly trend XLSX API client')
assertContains(adminReportExportCsv.text, 'adminReportExportsApi.monthlyTrendXlsx', 'admin monthly trend XLSX API client')
assertContains(adminReportExportCsv.text, 'listMockAdminOrderCsvRows(normalizedParams)', 'admin reports CSV mock client')
assertContains(adminReportExportCsv.text, 'listMockAdminProductBreakdown(normalizedParams)', 'admin reports product breakdown CSV mock client')
assertContains(adminReportExportCsv.text, 'listMockAdminTrendCsvRows(kind, normalizedParams)', 'admin reports trend CSV mock client')
assertContains(adminReportExportCsv.text, 'buildAdminTrendCsvText', 'admin reports trend CSV mock builder')
assertContains(adminReportExportCsv.text, 'buildAdminTrendXlsxBlob', 'admin reports trend XLSX mock builder')
assertContains(adminReportExportCsv.text, "from './xlsxWorkbook'", 'admin reports export module composes shared XLSX workbook builder')
assertContains(adminReportXlsxWorkbook.text, 'buildWorkbookBlob', 'admin reports XLSX workbook builder module')
assertContains(adminReportXlsxWorkbook.text, 'neutralizeSpreadsheetFormulaText', 'admin reports XLSX workbook formula protection')
assertContains(adminReportExportCsv.text, "export type AdminTrendCsvKind = 'daily' | 'hourly' | 'monthly'", 'admin reports trend CSV kind contract')
assertContains(adminReportExportCsv.text, 'normalizeAdminTrendReportParams(params)', 'admin reports trend CSV normalizes includeEmpty params')
assertContains(adminReportExportCsv.text, "'buyerPhoneMasked'", 'admin order CSV masked phone column')
assertContains(adminReportExportCsv.text, "type: 'text/csv;charset=utf-8'", 'admin order CSV mock content type')
assertContains(adminReportExportCsv.text, 'buildAdminOrdersCsvText', 'admin order CSV mock builder')
assertContains(adminReportExportCsv.text, 'buildAdminPaymentReconciliationCsvText', 'admin payment reconciliation CSV mock builder')
assertContains(adminReportExportCsv.text, 'buildAdminPaymentReconciliationXlsxBlob', 'admin payment reconciliation XLSX mock builder')
assertContains(adminReportExportCsv.text, 'buildAdminProductBreakdownCsvText', 'admin product breakdown CSV mock builder')
assertContains(adminReportExportCsv.text, 'buildAdminProductBreakdownXlsxBlob', 'admin product breakdown XLSX mock builder')
assertContains(adminReportExportCsv.text, "'unreconciledAmount'", 'admin payment reconciliation CSV exports unreconciled amount')
assertContains(adminReportExportCsv.text, "'netPaidAmount'", 'admin product breakdown CSV exports net paid amount')
assertContains(adminReportExportCsv.text, 'buildAdminOrdersXlsxBlob', 'admin order XLSX mock builder')
assertContains(adminReportXlsxWorkbook.text, 'inlineStr', 'admin order XLSX writes string cells')
assertContains(adminReportExportCsv.text, 'escapeCsvCell', 'admin order CSV formula protection')
assertContains(adminReportsPanel.text, 'useAdminReportSummaryQuery(reportParams)', 'admin reports panel summary query uses current date filters')
assertContains(adminReportsPanel.text, 'useAdminPaymentReconciliationQuery(reportParams)', 'admin reports panel payment reconciliation query uses current date filters')
assertContains(adminReportsPanel.text, 'useAdminProductBreakdownQuery(reportParams)', 'admin reports panel product query uses current date filters')
assertContains(adminReportsPanel.text, 'useAdminDailyTrendQuery(reportParams)', 'admin reports panel daily trend query uses current date filters')
assertContains(adminReportsPanel.text, 'useAdminReportExports({ reportParams, trendReportParams: reportParams })', 'admin reports panel delegates export state to hook')
assertContains(adminReportsPanel.text, 'reportExports.actions.exportOrdersCsv', 'admin reports panel uses export hook actions')
assertContains(adminReportsPanel.text, 'reportExports.loading.ordersCsv', 'admin reports panel uses export hook loading state')
assertContains(adminReportsPanel.text, 'Object.values(reportExports.errors).find(Boolean)', 'admin reports panel uses export hook error state')
assertNotContains(adminReportsPanel.text, 'downloadAdminOrdersCsv', 'admin reports panel should not own export download calls')
assertContains(adminReportExportsHook.text, 'downloadAdminOrdersCsv(reportParams)', 'admin report exports hook CSV action uses current date filters')
assertContains(adminReportExportsHook.text, 'downloadAdminOrdersXlsx(reportParams)', 'admin report exports hook XLSX action uses current date filters')
assertContains(adminReportExportsHook.text, 'downloadAdminPaymentReconciliationCsv(reportParams)', 'admin report exports hook payment reconciliation CSV action uses current date filters')
assertContains(adminReportExportsHook.text, 'downloadAdminPaymentReconciliationXlsx(reportParams)', 'admin report exports hook payment reconciliation XLSX action uses current date filters')
assertContains(adminReportExportsHook.text, 'downloadAdminProductBreakdownCsv(reportParams)', 'admin report exports hook product breakdown CSV action uses current date filters')
assertContains(adminReportExportsHook.text, 'downloadAdminProductBreakdownXlsx(reportParams)', 'admin report exports hook product breakdown XLSX action uses current date filters')
assertContains(adminReportExportsHook.text, 'downloadAdminTrendCsv(kind, trendReportParams)', 'admin report exports hook trend CSV action uses trend filters')
assertContains(adminReportExportsHook.text, 'downloadAdminTrendXlsx(kind, trendReportParams)', 'admin report exports hook trend XLSX action uses trend filters')
assertContains(adminReportExportsHook.text, 'isTrendExportingRef.current', 'admin report exports hook guards concurrent trend exports')
assertContains(adminReportExportsHook.text, 'isAnyTrendExporting: isTrendCsvExporting !== null || isTrendXlsxExporting !== null', 'admin report exports hook derives trend export mutex state')
assertContains(adminReportsPanel.text, 'aria-label="开始日期"', 'admin reports panel dateFrom accessible input')
assertContains(adminReportsPanel.text, 'aria-label="结束日期"', 'admin reports panel dateTo accessible input')
assertContains(adminReportsPanel.text, 'aria-label="渠道筛选"', 'admin reports panel channel accessible selector')
assertContains(adminReportsPanel.text, 'refetchReports', 'admin reports panel exposes report refresh action')
assertContains(adminReportSummaryMetrics.text, 'reportParams', 'admin reports summary metrics uses current filter fallback')
assertContains(adminReportsPanel.text, 'function RevenueChart', 'admin reports panel owns revenue trend chart')
assertContains(adminReportsPanel.text, 'function SalesChart', 'admin reports panel owns product sales chart')
assertContains(adminReportsPanel.text, 'dailyTrendQuery.refetch()', 'admin reports panel refetches daily trend')
assertContains(adminReportsPanel.text, 'reconciliationQuery.refetch()', 'admin reports panel refetches payment reconciliation')
assertContains(adminReportsPanel.text, '收入趋势', 'admin reports panel renders revenue trend title')
assertContains(adminReportsPanel.text, '票种销量', 'admin reports panel renders sales chart title')
assertContains(adminReportsPanel.text, '支付对账', 'admin reports panel renders payment reconciliation title')
assertContains(adminReportDisplay.text, 'export const defaultReportParams', 'admin reports helper owns default report params')
assertContains(adminReportDisplay.text, 'export function amountLabel', 'admin reports helper owns amount label')
assertContains(adminReportDisplay.text, 'export function metricLabel', 'admin reports helper owns metric label')
assertContains(adminReportDisplay.text, 'export function maxTrendAmount', 'admin reports helper owns trend max calculation')
assertContains(adminReportDisplay.text, 'export type AdminTrendMetricRow = AdminDailyTrend | AdminHourlyTrend | AdminMonthlyTrend', 'admin reports helper accepts daily, hourly or monthly trend rows')
assertContains(adminReportDisplay.text, 'export function trendPeriodLabel', 'admin reports helper owns trend period label')
assertContains(adminReportDisplay.text, "'reportHour' in row", 'admin reports helper detects hourly trend rows')
assertContains(adminReportCsvErrorDetails.text, '后台订单 CSV 暂时无法导出', 'admin reports CSV export fixed error message')
assertContains(adminReportCsvErrorDetails.text, 'fallback =', 'admin reports CSV export supports contextual fallback')
assertContains(adminReportCsvErrorDetails.text, 'AdminExportErrorDetails', 'admin reports CSV export uses shared export error details')
assertContains(adminReportXlsxErrorDetails.text, '后台订单 XLSX 暂时无法导出', 'admin reports XLSX export fixed error message')
assertContains(adminReportXlsxErrorDetails.text, 'AdminExportErrorDetails', 'admin reports XLSX export uses shared export error details')
assertContains(adminExportErrorDetails.text, "apiError?.code === 'ADMIN_EXPORT_TOO_LARGE'", 'admin export error details handles synchronous export row limit')
assertContains(adminExportErrorDetails.text, '导出数据超过同步导出上限，请缩小日期或筛选范围后重试。', 'admin export too large user action copy')
assertContains(adminExportErrorDetails.text, '当前同步导出适合小到中等数据量', 'admin export too large scope copy')
assertContains(adminExportErrorDetails.text, '日期、订单号、票码、失败码或操作人', 'admin export too large filter hint copy')
assertContains(adminExportErrorDetails.text, '错误码：{apiError.code}', 'admin export error details preserves diagnostic code')
assertContains(adminExportErrorDetails.text, '请求编号：{apiError.requestId}', 'admin export error details preserves request id')
assertContains(adminReportSummaryMetrics.text, '净收入', 'admin reports summary metrics component')
assertContains(adminPaymentReconciliationPanel.text, '支付对账', 'admin reports payment reconciliation panel title')
assertContains(adminPaymentReconciliationPanel.text, '支付流水号、渠道交易号、完整手机号', 'admin reports payment reconciliation sensitive-field boundary copy')
assertContains(adminPaymentReconciliationPanel.text, 'admin-payment-reconciliation-csv-export-action', 'admin reports payment reconciliation CSV button class')
assertContains(adminPaymentReconciliationPanel.text, 'admin-payment-reconciliation-xlsx-export-action', 'admin reports payment reconciliation XLSX button class')
assertContains(adminPaymentReconciliationPanel.text, '!reconciliation', 'admin reports payment reconciliation keeps missing data out of variance metrics')
assertContains(adminPaymentReconciliationPanel.text, 'admin-payment-reconciliation-empty', 'admin reports payment reconciliation missing data empty state')
assertContains(adminPaymentReconciliationPanel.text, '暂无支付对账数据', 'admin reports payment reconciliation missing data copy')
assertContains(adminReportExportCsv.text, "params.dateFrom?.trim()?.replaceAll('-', '')", 'admin payment reconciliation CSV file name compacts dateFrom')
assertContains(adminReportExportCsv.text, "params.dateTo?.trim()?.replaceAll('-', '')", 'admin payment reconciliation CSV file name compacts dateTo')
assertContains(adminReportExportCsv.text, "|| 'start'", 'admin payment reconciliation export file names use backend start placeholder')
assertContains(adminReportExportCsv.text, "|| 'end'", 'admin payment reconciliation export file names use backend end placeholder')
assertContains(adminReportTrendPanel.text, 'maxTrendAmount(trendRows)', 'admin reports trend panel uses shared max calculation')
assertContains(adminReportTrendPanel.text, 'trendPeriodLabel(row)', 'admin reports trend panel labels daily or monthly periods')
assertContains(adminReportTrendPanel.text, 'emptyText', 'admin reports trend panel supports custom empty copy')
assertContains(adminReportProductPanel.text, 'Table<AdminProductBreakdown>', 'admin reports product panel table')
assertContains(adminReportProductPanel.text, 'admin-product-breakdown-csv-export-action', 'admin reports product breakdown CSV button class')
assertContains(adminReportProductPanel.text, '导出产品 CSV', 'admin reports product breakdown CSV button copy')
assertContains(adminReportProductPanel.text, 'admin-product-breakdown-xlsx-export-action', 'admin reports product breakdown XLSX button class')
assertContains(adminReportProductPanel.text, '导出产品 XLSX', 'admin reports product breakdown XLSX button copy')
assertContains(adminReportsPanel.text, 'csvMenuItems', 'admin reports panel owns CSV export dropdown items')
assertContains(adminReportsPanel.text, 'xlsxMenuItems', 'admin reports panel owns XLSX export dropdown items')
assertContains(adminReportsPanel.text, 'reportExports.actions.exportPaymentReconciliationCsv()', 'admin reports panel can export payment reconciliation CSV')
assertContains(adminReportsPanel.text, 'reportExports.actions.exportProductBreakdownXlsx()', 'admin reports panel can export product XLSX')
assertContains(adminReportTrendExportBar.text, 'className="admin-report-daily-trend-csv-export-action"', 'admin reports trend export bar daily trend CSV button class')
assertContains(adminReportTrendExportBar.text, 'className="admin-report-hourly-trend-csv-export-action"', 'admin reports trend export bar hourly trend CSV button class')
assertContains(adminReportTrendExportBar.text, 'className="admin-report-monthly-trend-csv-export-action"', 'admin reports trend export bar monthly trend CSV button class')
assertContains(adminReportTrendExportBar.text, 'className="admin-report-daily-trend-xlsx-export-action"', 'admin reports trend export bar daily trend XLSX button class')
assertContains(adminReportTrendExportBar.text, 'className="admin-report-hourly-trend-xlsx-export-action"', 'admin reports trend export bar hourly trend XLSX button class')
assertContains(adminReportTrendExportBar.text, 'className="admin-report-monthly-trend-xlsx-export-action"', 'admin reports trend export bar monthly trend XLSX button class')
assertContains(adminReportTrendExportBar.text, 'disabled={isAnyTrendExporting}', 'admin reports trend export bar disables trend buttons while one export is running')
assertContains(adminReportsPanel.text, '订单明细 CSV', 'admin reports panel CSV export item copy')
assertContains(adminReportsPanel.text, '订单明细 XLSX', 'admin reports panel XLSX export item copy')
assertContains(adminReportsPanel.text, '导出失败，请稍后重试。', 'admin reports panel export error copy')
assertContains(adminReportTrendExportBar.text, '趋势 CSV/XLSX 导出跟随当前日期范围和补零口径', 'admin reports trend export bar scope copy')
assertContains(adminReportsPanel.text, '报表数据暂不可用，当前展示最近一次可视化样例。', 'admin reports panel data fallback copy')
assertNotContains(adminReportMockData.text, 'buyerPhone', 'admin mock reports phone field')
assertNotContains(adminReportMockData.text, 'idNumber', 'admin mock reports id number field')
assertNotContains(adminReportMockData.text, 'session', 'admin mock reports session field')
assertNotContains(adminReportMockData.text, 'csrf', 'admin mock reports csrf field')
assertNotContains(adminReportMockData.text, 'password', 'admin mock reports password field')
assertNotContains(adminReportMockData.text, 'hash', 'admin mock reports hash field')
assertNotContains(adminReportMockData.text, 'adminUserId', 'admin mock reports internal admin id')
assertNotContains(adminReportMockData.text, 'SQL', 'admin mock reports SQL field')
assertNotContains(adminReportExportCsv.text, 'visitorId', 'admin order CSV export internal visitor id')
assertNotContains(adminReportExportCsv.text, 'idNumber', 'admin order CSV export id number field')
assertNotContains(adminReportExportCsv.text, 'session', 'admin order CSV export session field')
assertNotContains(adminReportExportCsv.text, 'csrf', 'admin order CSV export csrf field')
assertNotContains(adminReportExportCsv.text, 'password', 'admin order CSV export password field')
assertNotContains(adminReportExportCsv.text, 'hash', 'admin order CSV export hash field')
assertNotContains(adminReportExportCsv.text, 'createdAt', 'admin order CSV export audit field')
assertNotContains(adminReportExportCsv.text, 'updatedAt', 'admin order CSV export audit field')
assertNotContains(adminReportExportCsv.text, 'deletedAt', 'admin order CSV export audit field')
assertNotContains(adminReportsPanel.text, 'buyerPhone', 'admin reports panel phone field')
assertNotContains(adminReportsPanel.text, 'idNumber', 'admin reports panel id number field')
assertNotContains(adminReportsPanel.text, 'SQL', 'admin reports panel SQL text')
assertNotContains(adminReportsPanel.text, 'session', 'admin reports panel session field')
assertNotContains(adminReportsPanel.text, 'CSRF', 'admin reports panel CSRF field')
assertNotContains(adminReportsPanel.text, 'password', 'admin reports panel password field')
assertNotContains(adminReportsPanel.text, 'hash', 'admin reports panel hash field')
assertNotContains(adminReportsPanel.text, 'adminUserId', 'admin reports panel internal admin id')
assertNotContains(adminReportsPanel.text, 'createdAt', 'admin reports panel audit field')
assertNotContains(adminReportsPanel.text, 'updatedAt', 'admin reports panel audit field')
assertNotContains(adminReportsPanel.text, 'deletedAt', 'admin reports panel audit field')
assertNotContains(adminReportSurfaceText, 'buyerPhone', 'admin reports UI surface phone field')
assertNotContains(adminReportSurfaceText, 'idNumber', 'admin reports UI surface id number field')
assertNotContains(adminReportSurfaceText, 'SQL', 'admin reports UI surface SQL text')
assertNotContains(adminReportSurfaceText, 'session', 'admin reports UI surface session field')
assertNotContains(adminReportSurfaceText, 'CSRF', 'admin reports UI surface CSRF field')
assertNotContains(adminReportSurfaceText, 'csrf', 'admin reports UI surface csrf field')
assertNotContains(adminReportSurfaceText, 'password', 'admin reports UI surface password field')
assertNotContains(adminReportSurfaceText, 'hash', 'admin reports UI surface hash field')
assertNotContains(adminReportSurfaceText, 'adminUserId', 'admin reports UI surface internal admin id')
assertNotContains(adminReportSurfaceText, 'createdAt', 'admin reports UI surface audit field')
assertNotContains(adminReportSurfaceText, 'updatedAt', 'admin reports UI surface audit field')
assertNotContains(adminReportSurfaceText, 'deletedAt', 'admin reports UI surface audit field')

const getCsrfTokenText = findFunction(client.sourceFile, 'getCsrfToken').getText(client.sourceFile)
assertContains(getCsrfTokenText, "apiRequest<CsrfPayload>('/api/auth/csrf'", 'CSRF fetch')
assertContains(getCsrfTokenText, 'skipCsrf: true', 'CSRF fetch')
assertContains(getCsrfTokenText, 'readCookie(CSRF_COOKIE_NAME)', 'CSRF cookie binding')

const apiRequestText = findFunction(client.sourceFile, 'apiRequest').getText(client.sourceFile)
const apiRequestFunction = findFunction(client.sourceFile, 'apiRequest')
assertFetchOptions(apiRequestFunction)
assertHeadersSetInBranch(apiRequestFunction, 'options.idempotencyKey', 'IDEMPOTENCY_HEADER', 'options.idempotencyKey', 'apiRequest idempotency')
assertHeadersSetInBranch(apiRequestFunction, 'isMutatingMethod(method) && !options.skipCsrf', 'csrfHeaderName', 'token', 'apiRequest CSRF')
assertContains(apiRequestText, 'const token = await getCsrfToken()', 'apiRequest CSRF token load')

const adminCheckInRequest = assertEndpoint(requests, {
  method: 'POST',
  path: '/api/admin/check-ins',
  typeArgument: 'AdminCheckIn',
})
assert(!adminCheckInRequest.hasIdempotencyKey && !adminCheckInRequest.skipCsrf, 'admin check-in must stay CSRF-protected without idempotency key')
const adminBatchCheckInRequest = assertEndpoint(requests, {
  method: 'POST',
  path: '/api/admin/check-ins/batch',
  typeArgument: 'AdminBatchCheckIn',
})
assert(!adminBatchCheckInRequest.hasIdempotencyKey && !adminBatchCheckInRequest.skipCsrf, 'admin batch check-in must stay CSRF-protected without idempotency key')
assertNotContains(adminBatchCheckInRequest.text, 'adminUserId', 'admin batch check-in request body')
assertNotContains(adminBatchCheckInRequest.text, 'orderId', 'admin batch check-in request body')
assertNotContains(adminBatchCheckInRequest.text, 'itemStatus', 'admin batch check-in request body')
assertNotContains(adminBatchCheckInRequest.text, 'operator', 'admin batch check-in request body')
assertNotContains(adminBatchCheckInRequest.text, 'quota', 'admin batch check-in request body')
const adminBatchUndoCheckInRequest = assertEndpoint(requests, {
  method: 'POST',
  path: '/api/admin/check-ins/batch/undo',
  typeArgument: 'AdminBatchUndoCheckIn',
})
assert(!adminBatchUndoCheckInRequest.hasIdempotencyKey && !adminBatchUndoCheckInRequest.skipCsrf, 'admin batch undo check-in must stay CSRF-protected without idempotency key')
assertNotContains(adminBatchUndoCheckInRequest.text, 'adminUserId', 'admin batch undo check-in request body')
assertNotContains(adminBatchUndoCheckInRequest.text, 'orderId', 'admin batch undo check-in request body')
assertNotContains(adminBatchUndoCheckInRequest.text, 'itemStatus', 'admin batch undo check-in request body')
assertNotContains(adminBatchUndoCheckInRequest.text, 'operator', 'admin batch undo check-in request body')
assertNotContains(adminBatchUndoCheckInRequest.text, 'quota', 'admin batch undo check-in request body')
assertNotContains(adminBatchUndoCheckInRequest.text, 'undoneAt', 'admin batch undo check-in request body')
const adminRefundAuditLogRequest = assertEndpoint(requests, {
  method: 'GET',
  path: '/api/admin/orders/${}/refund-logs',
  typeArgument: 'AdminRefundAuditLog[]',
})
assert(!adminRefundAuditLogRequest.hasIdempotencyKey && !adminRefundAuditLogRequest.skipCsrf, 'admin refund audit logs must stay read-only GET without mutating headers')

const { hasRemainingCheckableTicket } = loadRuntimeFunctions(adminOrderMockData.sourceFile, ['hasRemainingCheckableTicket'])
assert(
  hasRemainingCheckableTicket([
    { itemStatus: 'USED', ticketCode: 'TK-1' },
    { itemStatus: 'REFUNDED', ticketCode: 'TK-2' },
    { itemStatus: 'CANCELLED', ticketCode: 'TK-3' },
  ]) === false,
  'admin mock check-in completion guard must ignore non-checkable terminal items',
)
assert(
  hasRemainingCheckableTicket([
    { itemStatus: 'USED', ticketCode: 'TK-1' },
    { itemStatus: 'UNUSED', ticketCode: 'TK-2' },
  ]) === true,
  'admin mock check-in completion guard must keep order open for remaining unused tickets',
)

const {
  getMockAdminPaymentReconciliation,
  getMockAdminReportSummary,
  listMockAdminDailyTrend,
  listMockAdminHourlyTrend,
  listMockAdminMonthlyTrend,
} = loadRuntimeFunctions(adminReportMockData.sourceFile, [
  'mockDailyTrend',
  'mockHourlyTrend',
  'inRange',
  'assertValidTrendParams',
  'sumAmount',
  'sumNumber',
  'amount',
  'zeroMetrics',
  'dayCountInclusive',
  'monthCountInclusive',
  'parseDate',
  'formatDate',
  'listDates',
  'listMonths',
  'getMockAdminPaymentReconciliation',
  'getMockAdminReportSummary',
  'listMockAdminDailyTrend',
  'listMockAdminHourlyTrend',
  'listMockAdminMonthlyTrend',
])
assert(
  getMockAdminReportSummary({ dateFrom: '2026-06-26', dateTo: '2026-06-28' }).netPaidAmount === '30220.00',
  'admin report mock summary should aggregate the visible default date range',
)
assert(
  getMockAdminPaymentReconciliation({ dateFrom: '2026-06-26', dateTo: '2026-06-28' }).unreconciledAmount === '16.00',
  'admin payment reconciliation mock should expose the visible default unreconciled amount',
)
assert(
  getMockAdminPaymentReconciliation({ dateFrom: '2026-06-26', dateTo: '2026-06-27' }).reconciled === true,
  'admin payment reconciliation mock should mark clean ranges as reconciled',
)
assert(
  listMockAdminDailyTrend({ dateFrom: '2026-06-28', dateTo: '2026-06-28' })[0]?.reportDate === '2026-06-28',
  'admin report mock daily trend should filter exact dates',
)
assert(
  listMockAdminDailyTrend({ dateFrom: '2026-06-26', dateTo: '2026-06-28', includeEmpty: true }).length === 3,
  'admin report mock daily trend should include each date when zero fill is enabled',
)
assert(
  listMockAdminDailyTrend({ dateFrom: '2026-06-25', dateTo: '2026-06-26', includeEmpty: true })[0]?.orderCount === 0,
  'admin report mock daily trend should zero-fill missing dates',
)
assert(
  listMockAdminHourlyTrend({ dateFrom: '2026-06-28', dateTo: '2026-06-28' }).length === 2,
  'admin report mock hourly trend should filter hours by report date',
)
assert(
  listMockAdminHourlyTrend({ dateFrom: '2026-06-28', dateTo: '2026-06-28' })[0]?.reportHour === '2026-06-28T09:00:00',
  'admin report mock hourly trend should preserve backend reportHour format',
)
assert(
  listMockAdminHourlyTrend({ dateFrom: '2026-07-01' }).length === 0,
  'admin report mock hourly trend should exclude hours before the filter range',
)
assert(
  listMockAdminHourlyTrend({ dateFrom: '2026-06-28', dateTo: '2026-06-28', includeEmpty: true }).length === 24,
  'admin report mock hourly trend should include every hour when zero fill is enabled',
)
assert(
  listMockAdminHourlyTrend({ dateFrom: '2026-06-28', dateTo: '2026-06-28', includeEmpty: true })[0]?.reportHour === '2026-06-28T00:00:00',
  'admin report mock hourly trend should zero-fill from midnight',
)
assert(
  listMockAdminMonthlyTrend({ dateFrom: '2026-06-26', dateTo: '2026-06-28' })[0]?.reportMonth === '2026-06',
  'admin report mock monthly trend should include months with filtered daily rows',
)
assert(
  listMockAdminMonthlyTrend({ dateFrom: '2026-06-26', dateTo: '2026-06-28' })[0]?.netPaidAmount === '30220.00',
  'admin report mock monthly trend should aggregate after applying the date range',
)
assert(
  listMockAdminMonthlyTrend({ dateFrom: '2026-06-26', dateTo: '2026-06-28' })[0]?.orderCount === 134,
  'admin report mock monthly trend should sum filtered daily order counts',
)
assert(
  listMockAdminMonthlyTrend({ dateFrom: '2026-07-01' }).length === 0,
  'admin report mock monthly trend should exclude months before the filter range',
)
assert(
  listMockAdminMonthlyTrend({ dateFrom: '2026-05-01', dateTo: '2026-06-28', includeEmpty: true })[0]?.reportMonth === '2026-05',
  'admin report mock monthly trend should include missing months when zero fill is enabled',
)
assert(
  listMockAdminMonthlyTrend({ dateFrom: '2026-05-01', dateTo: '2026-06-28', includeEmpty: true })[0]?.netPaidAmount === '0.00',
  'admin report mock monthly trend should zero-fill missing months',
)
assertThrows(
  () => listMockAdminDailyTrend({ dateFrom: '2026-06-28', includeEmpty: true }),
  'ADMIN_REPORT_INCLUDE_EMPTY_RANGE_REQUIRED',
  'admin report mock trend zero fill should require both range boundaries',
)
assertThrows(
  () => listMockAdminDailyTrend({ dateFrom: '2026-01-01', dateTo: '2027-01-02', includeEmpty: true }),
  'ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE',
  'admin report mock daily zero fill should enforce the backend range limit',
)
assertThrows(
  () => listMockAdminHourlyTrend({ dateFrom: '2026-01-01', dateTo: '2026-02-01', includeEmpty: true }),
  'ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE',
  'admin report mock hourly zero fill should enforce the backend range limit',
)
assertThrows(
  () => listMockAdminMonthlyTrend({ dateFrom: '2021-01-01', dateTo: '2026-02-01', includeEmpty: true }),
  'ADMIN_REPORT_INCLUDE_EMPTY_RANGE_TOO_LARGE',
  'admin report mock monthly zero fill should enforce the backend range limit',
)

const rawFileRequestText = findFunction(client.sourceFile, 'rawFileRequest').getText(client.sourceFile)
assertContains(rawFileRequestText, 'fetch(buildUrl(path)', 'raw file request must use API base URL')
assertContains(rawFileRequestText, "credentials: 'include'", 'raw file request must include admin session cookies')
assertContains(rawFileRequestText, "method: 'GET'", 'raw file request must stay read-only GET')
assertContains(rawFileRequestText, "headers: new Headers({ Accept: options.accept ?? '*/*' })", 'raw file request must set accept header')
assertContains(rawFileRequestText, "response.headers.get('Content-Type')", 'raw file request must inspect response content type')
assertContains(rawFileRequestText, 'FILE_CONTENT_TYPE_MISMATCH', 'raw file request must fail closed on file content type mismatch')
assertContains(rawFileRequestText, 'options.expectedContentType', 'raw file request must support expected file content type')
assertNotContains(rawFileRequestText, 'getCsrfToken', 'raw file request must not bootstrap CSRF for GET downloads')
assertNotContains(rawFileRequestText, 'IDEMPOTENCY_HEADER', 'raw file request must not add idempotency headers')

const {
  buildAdminProductBreakdownCsvText,
  buildAdminProductBreakdownXlsxBlob,
  buildAdminPaymentReconciliationXlsxBlob,
  buildAdminTrendCsvText,
  buildAdminTrendXlsxBlob,
  buildAdminOrdersXlsxBlob,
  escapeCsvCell,
  neutralizeSpreadsheetFormulaText,
} = loadRuntimeFunctions([adminReportXlsxWorkbook.sourceFile, adminReportExportCsv.sourceFile, scenicText.sourceFile], [
  'ticketNameByCategory',
  'ticketNameByEnglishKeyword',
  'descriptionMap',
  'adminPaymentReconciliationCsvHeaders',
  'adminProductBreakdownCsvHeaders',
  'adminOrderCsvHeaders',
  'adminTrendMetricCsvHeaders',
  'adminReportXlsxContentType',
  'textEncoder',
  'crc32Table',
  'escapeCsvCell',
  'neutralizeSpreadsheetFormulaText',
  'sanitizeXmlText',
  'escapeXmlText',
  'columnName',
  'buildWorksheetXml',
  'makeCrc32Table',
  'crc32',
  'writeUint16',
  'writeUint32',
  'appendBytes',
  'buildStoreZip',
  'buildWorkbookBlob',
  'hasChinese',
  'normalize',
  'hasAny',
  'scenicTicketName',
  'scenicProductName',
  'productBreakdownExportValue',
  'buildAdminProductBreakdownCsvText',
  'buildAdminProductBreakdownXlsxBlob',
  'buildAdminPaymentReconciliationXlsxBlob',
  'buildAdminTrendCsvText',
  'buildAdminTrendXlsxBlob',
  'buildAdminOrdersXlsxBlob',
])
assert(neutralizeSpreadsheetFormulaText('=1+1') === "'=1+1", 'Spreadsheet text starting with = must be neutralized')
assert(neutralizeSpreadsheetFormulaText(' +cmd') === "' +cmd", 'Spreadsheet text with leading spaces before + must be neutralized')
assert(escapeCsvCell('=1+1') === "'=1+1", 'CSV cells starting with = must be neutralized')
assert(escapeCsvCell('+cmd') === "'+cmd", 'CSV cells starting with + must be neutralized')
assert(escapeCsvCell('@cmd') === "'@cmd", 'CSV cells starting with @ must be neutralized')
assert(escapeCsvCell('  @cmd') === "'  @cmd", 'CSV cells with leading spaces before @ must be neutralized')
assert(escapeCsvCell(' =cmd') === "' =cmd", 'CSV cells with leading spaces before = must be neutralized')
assert(escapeCsvCell(' +cmd') === "' +cmd", 'CSV cells with leading spaces before + must be neutralized')
assert(escapeCsvCell(' -cmd') === "' -cmd", 'CSV cells with leading spaces before - must be neutralized')
assert(escapeCsvCell(' \tcmd') === '"\' \tcmd"', 'CSV cells with leading spaces before tab must be neutralized')
assert(escapeCsvCell('\tcmd') === '"\'\tcmd"', 'CSV cells starting with tab must be neutralized')
assert(escapeCsvCell('\rcmd') === '"\'\rcmd"', 'CSV cells starting with CR must be neutralized')
assert(escapeCsvCell('\ncmd') === '"\'\ncmd"', 'CSV cells starting with LF must be neutralized')
assert(escapeCsvCell('-10') === "'-10", 'CSV cells starting with - must be neutralized')
assert(escapeCsvCell('a,b') === '"a,b"', 'CSV cells with comma must be quoted')
assert(escapeCsvCell('quote "x"') === '"quote ""x"""', 'CSV cells with quotes must be escaped and quoted')
const trendCsvText = buildAdminTrendCsvText('hourly', [
  {
    period: '=2026-06',
    orderCount: 1,
    paidOrderCount: 1,
    completedOrderCount: 0,
    refundedOrderCount: 0,
    cancelledOrderCount: 0,
    netPaidAmount: '88.00',
    ticketCount: 1,
    soldTicketCount: 1,
    checkedInTicketCount: 0,
    refundedTicketCount: 0,
  },
])
assertContains(trendCsvText, 'reportHour,orderCount,paidOrderCount', 'admin trend CSV must include kind-specific period header')
assertContains(trendCsvText, "'=2026-06,1,1,0", 'admin trend CSV must neutralize formula-like period cells')

const trendXlsxBlob = buildAdminTrendXlsxBlob('hourly', [
  {
    period: '=2026-06',
    orderCount: 1,
    paidOrderCount: 1,
    completedOrderCount: 0,
    refundedOrderCount: 0,
    cancelledOrderCount: 0,
    netPaidAmount: 'bad\u0001<amount>&',
    ticketCount: 1,
    soldTicketCount: 1,
    checkedInTicketCount: 0,
    refundedTicketCount: 0,
  },
])
const trendXlsxBytes = new Uint8Array(await trendXlsxBlob.arrayBuffer())
const trendWorksheetXml = readStoreZipEntryText(trendXlsxBytes, 'xl/worksheets/sheet1.xml')
assert(trendXlsxBlob.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'admin trend mock XLSX blob must use XLSX content type')
assertContains(trendWorksheetXml, 'reportHour', 'admin trend mock XLSX must include kind-specific period header')
assertContains(trendWorksheetXml, 'netPaidAmount', 'admin trend mock XLSX must include fixed metric headers')
assertContains(trendWorksheetXml, '&apos;=2026-06', 'admin trend mock XLSX formula-like period text must be neutralized')
assertContains(trendWorksheetXml, 'bad&lt;amount&gt;&amp;', 'admin trend mock XLSX XML text must be escaped')
assert(!trendWorksheetXml.includes('\u0001'), 'admin trend mock XLSX XML text must remove disallowed control characters')

const productBreakdownCsvText = buildAdminProductBreakdownCsvText([
  {
    productId: 1,
    ticketTypeId: 10,
    productName: '=bad product',
    ticketName: ' +bad ticket',
    orderCount: 2,
    ticketCount: 4,
    soldTicketCount: 3,
    checkedInTicketCount: 1,
    refundedTicketCount: 1,
    netPaidAmount: '88.00',
  },
  {
    productId: 2,
    ticketTypeId: 11,
    productName: 'Yulong River Adult Ticket With Very Long Pier And Scenic Route Name',
    ticketName: 'Adult Ticket Long Display Name',
    orderCount: 1,
    ticketCount: 2,
    soldTicketCount: 2,
    checkedInTicketCount: 0,
    refundedTicketCount: 0,
    netPaidAmount: '176.00',
  },
])
assertContains(productBreakdownCsvText, 'productId,ticketTypeId,productName,ticketName', 'admin product breakdown CSV must include fixed headers')
assertContains(productBreakdownCsvText, "'=bad product", 'admin product breakdown CSV must neutralize formula-like product names')
assertContains(productBreakdownCsvText, "' +bad ticket", 'admin product breakdown CSV must neutralize formula-like ticket names')
assertContains(productBreakdownCsvText, '遇龙河竹筏成人票', 'admin product breakdown CSV must localize legacy English product names')
assertContains(productBreakdownCsvText, '遇龙河成人票', 'admin product breakdown CSV must localize legacy English ticket names')
assert(!productBreakdownCsvText.includes('Adult Ticket Long Display Name'), 'admin product breakdown CSV must not export legacy English ticket names')

const productBreakdownXlsxBlob = buildAdminProductBreakdownXlsxBlob([
  {
    productId: 1,
    ticketTypeId: 10,
    productName: '=bad product',
    ticketName: 'bad\u0001<ticket>&',
    orderCount: 2,
    ticketCount: 4,
    soldTicketCount: 3,
    checkedInTicketCount: 1,
    refundedTicketCount: 1,
    netPaidAmount: '88.00',
  },
  {
    productId: 2,
    ticketTypeId: 11,
    productName: 'Yulong River Adult Ticket With Very Long Pier And Scenic Route Name',
    ticketName: 'Adult Ticket Long Display Name',
    orderCount: 1,
    ticketCount: 2,
    soldTicketCount: 2,
    checkedInTicketCount: 0,
    refundedTicketCount: 0,
    netPaidAmount: '176.00',
  },
])
const productBreakdownXlsxBytes = new Uint8Array(await productBreakdownXlsxBlob.arrayBuffer())
const productBreakdownWorksheetXml = readStoreZipEntryText(productBreakdownXlsxBytes, 'xl/worksheets/sheet1.xml')
assert(productBreakdownXlsxBlob.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'admin product breakdown mock XLSX blob must use XLSX content type')
assertContains(productBreakdownWorksheetXml, 'productId', 'admin product breakdown mock XLSX must include fixed headers')
assertContains(productBreakdownWorksheetXml, 'netPaidAmount', 'admin product breakdown mock XLSX must include net paid amount header')
assertContains(productBreakdownWorksheetXml, '&apos;=bad product', 'admin product breakdown mock XLSX formula-like text must be neutralized')
assertContains(productBreakdownWorksheetXml, 'bad&lt;ticket&gt;&amp;', 'admin product breakdown mock XLSX XML text must be escaped')
assertContains(productBreakdownWorksheetXml, '遇龙河竹筏成人票', 'admin product breakdown XLSX must localize legacy English product names')
assertContains(productBreakdownWorksheetXml, '遇龙河成人票', 'admin product breakdown XLSX must localize legacy English ticket names')
assert(!productBreakdownWorksheetXml.includes('Adult Ticket Long Display Name'), 'admin product breakdown XLSX must not export legacy English ticket names')
assert(!productBreakdownWorksheetXml.includes('\u0001'), 'admin product breakdown mock XLSX XML text must remove disallowed control characters')

const xlsxBlob = buildAdminOrdersXlsxBlob([
  {
    orderNo: '=1+1',
    buyerName: 'bad\u0001<name>&',
    buyerPhoneMasked: '139****2222',
    orderStatus: 'PAID',
    paymentStatus: 'PAID',
    totalAmount: '100.00',
    payableAmount: '100.00',
    orderTime: '2026-06-30 10:00:00',
    itemCount: 1,
  },
])
const xlsxBytes = new Uint8Array(await xlsxBlob.arrayBuffer())
const worksheetXml = readStoreZipEntryText(xlsxBytes, 'xl/worksheets/sheet1.xml')
assert(xlsxBlob.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'mock XLSX blob must use XLSX content type')
assert(xlsxBytes[0] === 0x50 && xlsxBytes[1] === 0x4B, 'mock XLSX must be a ZIP payload')
assertContains(worksheetXml, '&apos;=1+1', 'mock XLSX formula-like text must be neutralized')
assertContains(worksheetXml, 'bad&lt;name&gt;&amp;', 'mock XLSX XML text must be escaped')
assert(!worksheetXml.includes('\u0001'), 'mock XLSX XML text must remove disallowed control characters')

const paymentReconciliationXlsxBlob = buildAdminPaymentReconciliationXlsxBlob({
  dateFrom: '=2026-06-26',
  dateTo: 'bad\u0001<date>&',
  orderNetPaidAmount: '30220.00',
  capturedPaymentAmount: '30380.00',
  refundAuditAmount: '144.00',
  expectedNetAmount: '30204.00',
  unreconciledAmount: '16.00',
  capturedPaymentCount: 124,
  refundAuditLogCount: 2,
  reconciled: false,
})
const paymentReconciliationXlsxBytes = new Uint8Array(await paymentReconciliationXlsxBlob.arrayBuffer())
const paymentReconciliationWorksheetXml = readStoreZipEntryText(paymentReconciliationXlsxBytes, 'xl/worksheets/sheet1.xml')
assert(paymentReconciliationXlsxBlob.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'admin payment reconciliation mock XLSX blob must use XLSX content type')
assertContains(paymentReconciliationWorksheetXml, 'dateFrom', 'admin payment reconciliation mock XLSX must include headers')
assertContains(paymentReconciliationWorksheetXml, 'unreconciledAmount', 'admin payment reconciliation mock XLSX must include unreconciled amount header')
assertContains(paymentReconciliationWorksheetXml, '&apos;=2026-06-26', 'admin payment reconciliation mock XLSX formula-like text must be neutralized')
assertContains(paymentReconciliationWorksheetXml, 'bad&lt;date&gt;&amp;', 'admin payment reconciliation mock XLSX XML text must be escaped')
assert(!paymentReconciliationWorksheetXml.includes('\u0001'), 'admin payment reconciliation mock XLSX XML text must remove disallowed control characters')

console.log('Frontend API contract smoke passed')
