import { parseSource } from './api-contract-smoke-utils.mjs'

export async function loadApiContractSourceBundle() {
  const endpoints = await parseSource('shared/api/endpoints.ts')
  const searchBuilders = await parseSource('shared/api/searchBuilders.ts')
  const client = await parseSource('shared/api/client.ts')
  const scenicText = await parseSource('shared/display/scenicText.ts')
  const bookingAdapters = await parseSource('features/booking/adapters.ts')
  const bookingFlow = await parseSource('features/booking/bookingFlow.ts')
  const bookingWorkbench = await parseSource('features/booking/BookingWorkbench.tsx')
  const bookingHeader = await parseSource('features/booking/components/BookingHeader.tsx')
  const bookingReadinessList = await parseSource('features/booking/components/BookingReadinessList.tsx')
  const bookingStepsCard = await parseSource('features/booking/components/BookingStepsCard.tsx')
  const ticketSelector = await parseSource('features/booking/components/TicketSelector.tsx')
  const dateSlotPicker = await parseSource('features/booking/components/DateSlotPicker.tsx')
  const bookingCss = await parseSource('features/booking/booking.css')
  const orderAdapters = await parseSource('features/orders/adapters.ts')
  const ordersWorkbench = await parseSource('features/orders/OrdersWorkbench.tsx')
  const ordersHeader = await parseSource('features/orders/components/OrdersHeader.tsx')
  const ordersListCard = await parseSource('features/orders/components/OrdersListCard.tsx')
  const orderWorkflowStrip = await parseSource('features/orders/components/OrderWorkflowStrip.tsx')
  const orderDetailSurfaces = await parseSource('features/orders/components/OrderDetailSurfaces.tsx')
  const orderDetailSections = await parseSource('features/orders/components/OrderDetailSections.tsx')
  const ordersCss = await parseSource('features/orders/orders.css')
  const adminAuthQueries = await parseSource('features/admin-auth/queries.ts')
  const adminAuthController = await parseSource('features/admin-auth/useAdminSessionController.ts')
  const adminOrderQueries = await parseSource('features/admin-orders/queries.ts')
  const adminOrderMockData = await parseSource('features/admin-orders/mockData.ts')
  const adminOrderMockSeeds = await parseSource('features/admin-orders/mockOrderSeeds.ts')
  const adminAppShell = await parseSource('app/AdminAppShell.tsx')
  const adminWorkbench = await parseSource('features/admin/AdminWorkbench.tsx')
  const adminOrdersPanel = await parseSource('features/admin/AdminOrdersPanel.tsx')
  const adminOrderDisplay = await parseSource('features/admin/adminOrderDisplay.tsx')
  const adminBatchCheckInPanel = await parseSource('features/admin/components/AdminBatchCheckInPanel.tsx')
  const adminBatchUndoCheckInPanel = await parseSource('features/admin/components/AdminBatchUndoCheckInPanel.tsx')
  const adminOrderDetailErrorDetails = await parseSource('features/admin/components/AdminOrderDetailErrorDetails.tsx')
  const adminOrderDetailDrawer = await parseSource('features/admin/components/AdminOrderDetailDrawer.tsx')
  const adminOrderDetailSummary = await parseSource('features/admin/components/AdminOrderDetailSummary.tsx')
  const adminOrderItemsTable = await parseSource('features/admin/components/AdminOrderItemsTable.tsx')
  const adminOrderRefundPanels = await parseSource('features/admin/components/AdminOrderRefundPanels.tsx')
  const adminRefundAuditPanel = await parseSource('features/admin/components/AdminRefundAuditPanel.tsx')
  const adminCheckInAuditExportPanel = await parseSource('features/admin/AdminCheckInAuditExportPanel.tsx')
  const adminExportJobsPanel = await parseSource('features/admin/AdminExportJobsPanel.tsx')
  const adminExportJobDisplay = await parseSource('features/admin/adminExportJobDisplay.tsx')
  const adminExportJobCreateToolbar = await parseSource('features/admin/components/AdminExportJobCreateToolbar.tsx')
  const adminExportJobTable = await parseSource('features/admin/components/AdminExportJobTable.tsx')
  const adminExportJobQueries = await parseSource('features/admin-export-jobs/queries.ts')
  const adminExportJobMockData = await parseSource('features/admin-export-jobs/mockData.ts')
  const adminCheckInAuditExportCsv = await parseSource('features/admin-check-in-logs/exportCsv.ts')
  const adminCheckInAuditExportXlsx = await parseSource('features/admin-check-in-logs/exportXlsx.ts')
  const adminExportErrorDetails = await parseSource('features/admin/components/AdminExportErrorDetails.tsx')
  const adminCheckInAuditCsvExportErrorDetails = await parseSource('features/admin/components/AdminCheckInAuditCsvExportErrorDetails.tsx')
  const adminCheckInAuditExportErrorDetails = await parseSource('features/admin/components/AdminCheckInAuditExportErrorDetails.tsx')
  const adminCheckInFailureLogQueries = await parseSource('features/admin-check-in-failure-logs/queries.ts')
  const adminCheckInFailureLogMockData = await parseSource('features/admin-check-in-failure-logs/mockData.ts')
  const adminCheckInFailureAuditExportCsv = await parseSource('features/admin-check-in-failure-logs/exportCsv.ts')
  const adminCheckInFailureAuditExportXlsx = await parseSource('features/admin-check-in-failure-logs/exportXlsx.ts')
  const adminCheckInFailureLogPanel = await parseSource('features/admin/AdminCheckInFailureAuditLogPanel.tsx')
  const adminCheckInFailureAuditDisplay = await parseSource('features/admin/adminCheckInFailureAuditDisplay.tsx')
  const adminCheckInFailureAuditCsvErrorDetails = await parseSource('features/admin/components/AdminCheckInFailureAuditCsvErrorDetails.tsx')
  const adminCheckInFailureAuditErrorDetails = await parseSource('features/admin/components/AdminCheckInFailureAuditSearchErrorDetails.tsx')
  const adminCheckInFailureAuditXlsxErrorDetails = await parseSource('features/admin/components/AdminCheckInFailureAuditXlsxErrorDetails.tsx')
  const adminCheckInFailureAuditTable = await parseSource('features/admin/components/AdminCheckInFailureAuditTable.tsx')
  const adminCheckInFailureAuditToolbar = await parseSource('features/admin/components/AdminCheckInFailureAuditToolbar.tsx')
  const adminRefundLogQueries = await parseSource('features/admin-refund-logs/queries.ts')
  const adminRefundLogMockData = await parseSource('features/admin-refund-logs/mockData.ts')
  const adminRefundAuditExportCsv = await parseSource('features/admin-refund-logs/exportCsv.ts')
  const adminRefundAuditExportXlsx = await parseSource('features/admin-refund-logs/exportXlsx.ts')
  const adminRefundLogPanel = await parseSource('features/admin/AdminRefundAuditLogPanel.tsx')
  const adminRefundAuditDisplay = await parseSource('features/admin/adminRefundAuditDisplay.tsx')
  const adminRefundAuditCsvErrorDetails = await parseSource('features/admin/components/AdminRefundAuditCsvErrorDetails.tsx')
  const adminRefundAuditErrorDetails = await parseSource('features/admin/components/AdminRefundAuditSearchErrorDetails.tsx')
  const adminRefundAuditXlsxErrorDetails = await parseSource('features/admin/components/AdminRefundAuditXlsxErrorDetails.tsx')
  const adminRefundAuditTable = await parseSource('features/admin/components/AdminRefundAuditTable.tsx')
  const adminRefundAuditToolbar = await parseSource('features/admin/components/AdminRefundAuditToolbar.tsx')
  const adminReportQueries = await parseSource('features/admin-reports/queries.ts')
  const adminReportMockData = await parseSource('features/admin-reports/mockData.ts')
  const adminReportExportCsv = await parseSource('features/admin-reports/exportCsv.ts')
  const adminReportExportsHook = await parseSource('features/admin-reports/useAdminReportExports.ts')
  const adminReportXlsxWorkbook = await parseSource('features/admin-reports/xlsxWorkbook.ts')
  const adminReportsPanel = await parseSource('features/admin/AdminReportsPanel.tsx')
  const adminReportDisplay = await parseSource('features/admin/adminReportDisplay.tsx')
  const adminReportCsvErrorDetails = await parseSource('features/admin/components/AdminReportCsvErrorDetails.tsx')
  const adminPaymentReconciliationPanel = await parseSource('features/admin/components/AdminPaymentReconciliationPanel.tsx')
  const adminReportProductPanel = await parseSource('features/admin/components/AdminReportProductPanel.tsx')
  const adminReportSummaryMetrics = await parseSource('features/admin/components/AdminReportSummaryMetrics.tsx')
  const adminReportTrendExportBar = await parseSource('features/admin/components/AdminReportTrendExportBar.tsx')
  const adminReportTrendPanel = await parseSource('features/admin/components/AdminReportTrendPanel.tsx')
  const adminReportXlsxErrorDetails = await parseSource('features/admin/components/AdminReportXlsxErrorDetails.tsx')
  const appCss = await parseSource('App.css')
  const appLayoutCss = await parseSource('app/app.css')
  const adminCss = await parseSource('features/admin/admin.css')
  const adminReportCss = await parseSource('features/admin/adminReports.css')
  const adminReportSurfaceText = [
    adminReportsPanel.text,
    adminReportExportsHook.text,
    adminReportDisplay.text,
    adminReportCsvErrorDetails.text,
    adminExportErrorDetails.text,
    adminPaymentReconciliationPanel.text,
    adminReportProductPanel.text,
    adminReportSummaryMetrics.text,
    adminReportTrendExportBar.text,
    adminReportTrendPanel.text,
    adminReportXlsxErrorDetails.text,
  ].join('\n')
  const adminOrderMockSurfaceText = [
    adminOrderMockData.text,
    adminOrderMockSeeds.text,
  ].join('\n')
  const adminOrderDetailSurfaceText = [
    adminOrderDetailDrawer.text,
    adminOrderDetailSummary.text,
    adminOrderItemsTable.text,
    adminOrderRefundPanels.text,
    adminRefundAuditPanel.text,
  ].join('\n')
  const adminRefundAuditSurfaceText = [
    adminExportErrorDetails.text,
    adminCheckInAuditExportPanel.text,
    adminCheckInAuditExportCsv.text,
    adminCheckInAuditCsvExportErrorDetails.text,
    adminCheckInAuditExportErrorDetails.text,
    adminCheckInFailureLogPanel.text,
    adminCheckInFailureAuditExportCsv.text,
    adminCheckInFailureAuditExportXlsx.text,
    adminCheckInFailureAuditDisplay.text,
    adminCheckInFailureAuditCsvErrorDetails.text,
    adminCheckInFailureAuditErrorDetails.text,
    adminCheckInFailureAuditXlsxErrorDetails.text,
    adminCheckInFailureAuditTable.text,
    adminCheckInFailureAuditToolbar.text,
    adminRefundLogPanel.text,
    adminRefundAuditExportCsv.text,
    adminRefundAuditExportXlsx.text,
    adminRefundAuditDisplay.text,
    adminRefundAuditCsvErrorDetails.text,
    adminRefundAuditErrorDetails.text,
    adminRefundAuditXlsxErrorDetails.text,
    adminRefundAuditTable.text,
    adminRefundAuditToolbar.text,
  ].join('\n')

  return {
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
  }
}
