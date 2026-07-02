import {
  assert,
  assertContains,
  assertEndpoint,
  assertNotContains,
  collectApiRequests,
  findRuntimeDeclaration,
  loadRuntimeFunctions,
} from './api-contract-smoke-utils.mjs'

export function runApiEndpointContracts({ client, endpoints, searchBuilders }) {
  const requests = [...collectApiRequests(endpoints.sourceFile), ...collectApiRequests(client.sourceFile)]
  const expectedEndpoints = [
    { method: 'GET', path: '/api/health', typeArgument: 'HealthPayload' },
    { method: 'GET', path: '/api/health/db', typeArgument: 'DatabaseHealthPayload' },
    { method: 'GET', path: '/api/auth/csrf', skipCsrf: true },
    { method: 'GET', path: '/api/auth/me' },
    { method: 'POST', path: '/api/auth/visitor/login' },
    { method: 'POST', path: '/api/auth/visitor/register' },
    { method: 'POST', path: '/api/auth/logout' },
    { method: 'POST', path: '/api/admin/auth/login', typeArgument: 'AdminMe' },
    { method: 'GET', path: '/api/admin/auth/me', typeArgument: 'AdminMe' },
    { method: 'POST', path: '/api/admin/auth/logout', typeArgument: 'LogoutPayload' },
    { method: 'POST', path: '/api/admin/check-ins', typeArgument: 'AdminCheckIn' },
    { method: 'POST', path: '/api/admin/check-ins/batch', typeArgument: 'AdminBatchCheckIn' },
    { method: 'POST', path: '/api/admin/check-ins/batch/undo', typeArgument: 'AdminBatchUndoCheckIn' },
    { method: 'GET', path: '/api/admin/orders${}', typeArgument: 'AdminOrderList' },
    { method: 'GET', path: '/api/admin/orders/${}', typeArgument: 'AdminOrderDetail' },
    { method: 'POST', path: '/api/admin/orders/${}/refund', typeArgument: 'AdminRefund' },
    { method: 'POST', path: '/api/admin/orders/${}/refund/items', typeArgument: 'AdminPartialRefund' },
    { method: 'GET', path: '/api/admin/orders/${}/refund-logs', typeArgument: 'AdminRefundAuditLog[]' },
    { method: 'GET', path: '/api/admin/refund-logs${}', typeArgument: 'AdminRefundAuditLogList' },
    { method: 'GET', path: '/api/admin/check-in-failure-logs${}', typeArgument: 'AdminCheckInFailureAuditLogList' },
    { method: 'GET', path: '/api/admin/reports/daily-trend${}', typeArgument: 'AdminDailyTrend[]' },
    { method: 'GET', path: '/api/admin/reports/hourly-trend${}', typeArgument: 'AdminHourlyTrend[]' },
    { method: 'GET', path: '/api/admin/reports/monthly-trend${}', typeArgument: 'AdminMonthlyTrend[]' },
    { method: 'GET', path: '/api/admin/reports/payment-reconciliation${}', typeArgument: 'AdminPaymentReconciliation' },
    { method: 'GET', path: '/api/admin/reports/product-breakdown${}', typeArgument: 'AdminProductBreakdown[]' },
    { method: 'GET', path: '/api/admin/reports/summary${}', typeArgument: 'AdminReportSummary' },
    { method: 'GET', path: '/api/catalog/products' },
    { method: 'GET', path: '/api/catalog/time-slots?${}' },
    { method: 'POST', path: '/api/orders' },
    { method: 'GET', path: '/api/me/orders${}' },
    { method: 'GET', path: '/api/me/orders/${}' },
    { idempotencyKey: true, method: 'POST', path: '/api/orders/${}/pay' },
    { method: 'POST', path: '/api/orders/${}/cancel' },
  ]

  for (const endpoint of expectedEndpoints) {
    assertEndpoint(requests, endpoint)
  }

  assertContains(endpoints.text, 'ticketTypeId: String(params.ticketTypeId)', 'time slot query')
  assertContains(endpoints.text, 'visitDate: params.visitDate', 'time slot query')
  assertContains(endpoints.text, 'new URLSearchParams({ status })', 'orders status filter')
  assertContains(endpoints.text, 'buildAdminOrderListSearch(params)', 'admin orders list search helper')
  assertContains(searchBuilders.text, "search.set('status', params.status)", 'admin orders status filter')
  assertContains(searchBuilders.text, "search.set('paymentStatus', params.paymentStatus)", 'admin orders payment status filter')
  assertContains(searchBuilders.text, "search.set('orderNo', orderNo)", 'admin orders order number filter')
  assertContains(searchBuilders.text, "search.set('buyerPhone', buyerPhone)", 'admin orders buyer phone filter')
  assertContains(searchBuilders.text, "search.set('page', String(params.page))", 'admin orders page filter')
  assertContains(searchBuilders.text, "search.set('pageSize', String(params.pageSize))", 'admin orders page size filter')
  assertContains(endpoints.text, 'buildAdminReportSearch(params)', 'admin reports search helper')
  assertContains(endpoints.text, 'buildAdminTrendReportSearch(params)', 'admin trend reports search helper')
  assertContains(searchBuilders.text, "search.set('dateFrom', dateFrom)", 'admin reports dateFrom filter')
  assertContains(searchBuilders.text, "search.set('dateTo', dateTo)", 'admin reports dateTo filter')
  assertContains(searchBuilders.text, "search.set('includeEmpty', 'true')", 'admin trend reports includeEmpty filter')
  assertContains(endpoints.text, '/api/admin/reports/daily-trend${buildAdminTrendReportSearch(params)}', 'admin reports daily trend endpoint')
  assertContains(endpoints.text, '/api/admin/reports/hourly-trend${buildAdminTrendReportSearch(params)}', 'admin reports hourly trend endpoint')
  assertContains(endpoints.text, '/api/admin/reports/monthly-trend${buildAdminTrendReportSearch(params)}', 'admin reports monthly trend endpoint')
  assertContains(endpoints.text, '/api/admin/reports/daily-trend.csv${buildAdminTrendReportSearch(params)}', 'admin daily trend CSV export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/daily-trend.xlsx${buildAdminTrendReportSearch(params)}', 'admin daily trend XLSX export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/hourly-trend.csv${buildAdminTrendReportSearch(params)}', 'admin hourly trend CSV export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/hourly-trend.xlsx${buildAdminTrendReportSearch(params)}', 'admin hourly trend XLSX export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/monthly-trend.csv${buildAdminTrendReportSearch(params)}', 'admin monthly trend CSV export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/monthly-trend.xlsx${buildAdminTrendReportSearch(params)}', 'admin monthly trend XLSX export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/payment-reconciliation${buildAdminReportSearch(params)}', 'admin payment reconciliation endpoint keeps report search')
  assertContains(endpoints.text, '/api/admin/reports/payment-reconciliation.csv${buildAdminReportSearch(params)}', 'admin payment reconciliation CSV export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/product-breakdown${buildAdminReportSearch(params)}', 'admin reports product endpoint keeps report search')
  assertContains(endpoints.text, '/api/admin/reports/product-breakdown.csv${buildAdminReportSearch(params)}', 'admin product breakdown CSV export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/product-breakdown.xlsx${buildAdminReportSearch(params)}', 'admin product breakdown XLSX export endpoint')
  assertContains(endpoints.text, '/api/admin/reports/summary${buildAdminReportSearch(params)}', 'admin reports summary endpoint keeps report search')
  assertContains(endpoints.text, 'buildAdminRefundAuditLogSearch(params)', 'admin refund audit log search helper')
  assertContains(searchBuilders.text, "search.set('refundType', params.refundType)", 'admin refund audit type filter')
  assertContains(searchBuilders.text, "search.set('operatorUsername', operatorUsername)", 'admin refund audit operator filter')
  assertContains(searchBuilders.text, "search.set('orderNo', orderNo)", 'admin refund audit order filter')
  assertContains(endpoints.text, '/api/admin/refund-logs${buildAdminRefundAuditLogSearch(params)}', 'admin refund audit search endpoint')
  assertContains(endpoints.text, 'buildAdminRefundAuditLogExportSearch(params)', 'admin refund audit export search helper')
  assertContains(endpoints.text, '/api/admin/refund-logs.csv${buildAdminRefundAuditLogExportSearch(params)}', 'admin refund audit CSV export endpoint')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/refund-logs.csv", 'admin refund audit CSV export raw file request')
  assertContains(endpoints.text, '/api/admin/refund-logs.xlsx${buildAdminRefundAuditLogExportSearch(params)}', 'admin refund audit XLSX export endpoint')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/refund-logs.xlsx", 'admin refund audit XLSX export raw file request')
  const adminRefundAuditExportApiDeclaration = findRuntimeDeclaration(endpoints.sourceFile, 'adminRefundAuditLogExportsApi')
  assertContains(adminRefundAuditExportApiDeclaration, "accept: 'text/csv'", 'admin refund audit CSV export accept header')
  assertContains(adminRefundAuditExportApiDeclaration, "expectedContentType: 'text/csv'", 'admin refund audit CSV export content type guard')
  assertContains(adminRefundAuditExportApiDeclaration, "accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin refund audit XLSX export accept header')
  assertContains(adminRefundAuditExportApiDeclaration, "expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin refund audit XLSX export content type guard')
  assertContains(endpoints.text, 'buildAdminCheckInAuditLogExportSearch(params)', 'admin check-in audit export search helper')
  assertContains(searchBuilders.text, "search.set('ticketCode', ticketCode)", 'admin check-in audit ticket code export filter')
  assertContains(searchBuilders.text, "search.set('operatorUsername', operatorUsername)", 'admin check-in audit operator export filter')
  assertContains(searchBuilders.text, "search.set('orderNo', orderNo)", 'admin check-in audit order export filter')
  assertContains(searchBuilders.text, "search.set('reason', reason)", 'admin check-in audit reason export filter')
  assertContains(endpoints.text, '/api/admin/check-in-logs.csv${buildAdminCheckInAuditLogExportSearch(params)}', 'admin check-in audit CSV export endpoint')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/check-in-logs.csv", 'admin check-in audit CSV export raw file request')
  assertContains(endpoints.text, '/api/admin/check-in-logs.xlsx${buildAdminCheckInAuditLogExportSearch(params)}', 'admin check-in audit XLSX export endpoint')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/check-in-logs.xlsx", 'admin check-in audit XLSX export raw file request')
  const adminCheckInAuditExportApiDeclaration = findRuntimeDeclaration(endpoints.sourceFile, 'adminCheckInAuditLogExportsApi')
  assertContains(adminCheckInAuditExportApiDeclaration, "accept: 'text/csv'", 'admin check-in audit CSV export accept header')
  assertContains(adminCheckInAuditExportApiDeclaration, "expectedContentType: 'text/csv'", 'admin check-in audit CSV export content type guard')
  assertContains(adminCheckInAuditExportApiDeclaration, "accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin check-in audit XLSX export accept header')
  assertContains(adminCheckInAuditExportApiDeclaration, "expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin check-in audit XLSX export content type guard')
  assertContains(endpoints.text, 'buildAdminCheckInFailureAuditLogSearch(params)', 'admin check-in failure audit search helper')
  assertContains(endpoints.text, 'buildAdminCheckInFailureAuditLogExportSearch(params)', 'admin check-in failure audit CSV export search helper')
  assertContains(searchBuilders.text, "search.set('ticketCode', ticketCode)", 'admin check-in failure audit ticket code filter')
  assertContains(searchBuilders.text, "search.set('failureCode', params.failureCode)", 'admin check-in failure audit failure code filter')
  assertContains(searchBuilders.text, "search.set('operatorUsername', operatorUsername)", 'admin check-in failure audit operator filter')
  assertContains(endpoints.text, '/api/admin/check-in-failure-logs${buildAdminCheckInFailureAuditLogSearch(params)}', 'admin check-in failure audit search endpoint')
  assertContains(endpoints.text, '/api/admin/check-in-failure-logs.csv${buildAdminCheckInFailureAuditLogExportSearch(params)}', 'admin check-in failure audit CSV export endpoint')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/check-in-failure-logs.csv", 'admin check-in failure audit CSV export raw file request')
  assertContains(endpoints.text, '/api/admin/check-in-failure-logs.xlsx${buildAdminCheckInFailureAuditLogExportSearch(params)}', 'admin check-in failure audit XLSX export endpoint')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/check-in-failure-logs.xlsx", 'admin check-in failure audit XLSX export raw file request')
  const adminCheckInFailureAuditExportApiDeclaration = findRuntimeDeclaration(endpoints.sourceFile, 'adminCheckInFailureAuditLogExportsApi')
  assertContains(adminCheckInFailureAuditExportApiDeclaration, "accept: 'text/csv'", 'admin check-in failure audit CSV export accept header')
  assertContains(adminCheckInFailureAuditExportApiDeclaration, "expectedContentType: 'text/csv'", 'admin check-in failure audit CSV export content type guard')
  assertContains(adminCheckInFailureAuditExportApiDeclaration, "accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin check-in failure audit XLSX export accept header')
  assertContains(adminCheckInFailureAuditExportApiDeclaration, "expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin check-in failure audit XLSX export content type guard')
  assertContains(endpoints.text, 'buildAdminExportJobListSearch(params)', 'admin export jobs list search helper')
  assertContains(searchBuilders.text, "search.set('exportType', params.exportType)", 'admin export jobs exportType filter')
  assertContains(searchBuilders.text, "search.set('fileFormat', params.fileFormat)", 'admin export jobs fileFormat filter')
  assertContains(searchBuilders.text, "search.set('status', params.status)", 'admin export jobs status filter')
  const adminExportJobsApiDeclaration = findRuntimeDeclaration(endpoints.sourceFile, 'adminExportJobsApi')
  assertContains(adminExportJobsApiDeclaration, "apiRequest<AdminExportJob>('/api/admin/export-jobs'", 'admin export job create endpoint')
  assertContains(adminExportJobsApiDeclaration, "method: 'POST'", 'admin export job create uses POST and CSRF boundary')
  assertContains(adminExportJobsApiDeclaration, 'filters: body.filters', 'admin export job create submits filters only through DTO boundary')
  assertContains(adminExportJobsApiDeclaration, '/api/admin/export-jobs/${encodeURIComponent(jobId)}', 'admin export job detail endpoint')
  assertContains(adminExportJobsApiDeclaration, '/api/admin/export-jobs/${encodeURIComponent(jobId)}/download', 'admin export job download endpoint')
  assertContains(adminExportJobsApiDeclaration, 'rawFileRequest(`/api/admin/export-jobs/${encodeURIComponent(jobId)}/download`', 'admin export job download raw file request')
  assertContains(adminExportJobsApiDeclaration, 'apiRequest<AdminExportJobList>(`/api/admin/export-jobs${buildAdminExportJobListSearch(params)}`)', 'admin export job list endpoint')
  assertContains(endpoints.text, '/api/admin/orders/${encodeURIComponent(orderNo)}/refund', 'admin full refund endpoint')
  assertContains(endpoints.text, 'body: { reason: compactText(body.reason) }', 'admin full refund API client only submits reason')
  assertContains(endpoints.text, '/api/admin/orders/${encodeURIComponent(orderNo)}/refund/items', 'admin partial refund endpoint')
  assertContains(endpoints.text, 'itemNos: body.itemNos.map((itemNo) => itemNo.trim())', 'admin partial refund API client trims selected item numbers without dropping invalid blanks')
  assertContains(endpoints.text, 'reason: compactText(body.reason)', 'admin partial refund API client trims optional reason')
  assertContains(endpoints.text, '/api/admin/reports/orders.csv${buildAdminReportSearch(params)}', 'admin order CSV export endpoint')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/orders.csv", 'admin order CSV export raw file request')
  assertContains(endpoints.text, "accept: 'text/csv'", 'admin order CSV export accept header')
  assertContains(endpoints.text, "expectedContentType: 'text/csv'", 'admin order CSV export content type guard')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/daily-trend.xlsx", 'admin daily trend XLSX export raw file request')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/hourly-trend.xlsx", 'admin hourly trend XLSX export raw file request')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/monthly-trend.xlsx", 'admin monthly trend XLSX export raw file request')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/payment-reconciliation.csv", 'admin payment reconciliation CSV export raw file request')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/product-breakdown.csv", 'admin product breakdown CSV export raw file request')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/payment-reconciliation.xlsx", 'admin payment reconciliation XLSX export raw file request')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/product-breakdown.xlsx", 'admin product breakdown XLSX export raw file request')
  assertContains(endpoints.text, '/api/admin/reports/orders.xlsx${buildAdminReportSearch(params)}', 'admin order XLSX export endpoint')
  assertContains(endpoints.text, "rawFileRequest(`/api/admin/reports/orders.xlsx", 'admin order XLSX export raw file request')
  assertContains(endpoints.text, "accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin order XLSX export accept header')
  assertContains(endpoints.text, "expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin order XLSX export content type guard')
  const adminReportExportApiDeclaration = findRuntimeDeclaration(endpoints.sourceFile, 'adminReportExportsApi')
  assertContains(adminReportExportApiDeclaration, "dailyTrendCsv: (params?: AdminTrendReportParams)", 'admin daily trend CSV export typed params')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/daily-trend.csv${buildAdminTrendReportSearch(params)}', 'admin daily trend CSV export must use trend search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/daily-trend.xlsx${buildAdminTrendReportSearch(params)}', 'admin daily trend XLSX export must use trend search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/hourly-trend.csv${buildAdminTrendReportSearch(params)}', 'admin hourly trend CSV export must use trend search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/hourly-trend.xlsx${buildAdminTrendReportSearch(params)}', 'admin hourly trend XLSX export must use trend search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/monthly-trend.csv${buildAdminTrendReportSearch(params)}', 'admin monthly trend CSV export must use trend search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/monthly-trend.xlsx${buildAdminTrendReportSearch(params)}', 'admin monthly trend XLSX export must use trend search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/payment-reconciliation.csv${buildAdminReportSearch(params)}', 'admin payment reconciliation CSV export must use report search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/payment-reconciliation.xlsx${buildAdminReportSearch(params)}', 'admin payment reconciliation XLSX export must use report search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/product-breakdown.csv${buildAdminReportSearch(params)}', 'admin product breakdown CSV export must use report search')
  assertContains(adminReportExportApiDeclaration, '/api/admin/reports/product-breakdown.xlsx${buildAdminReportSearch(params)}', 'admin product breakdown XLSX export must use report search')
  assertContains(adminReportExportApiDeclaration, "accept: 'text/csv'", 'admin trend CSV export accept header')
  assertContains(adminReportExportApiDeclaration, "expectedContentType: 'text/csv'", 'admin trend CSV export content type guard')
  assertContains(adminReportExportApiDeclaration, "accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin report XLSX export accept header')
  assertContains(adminReportExportApiDeclaration, "expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin report XLSX export content type guard')
  const productBreakdownXlsxExportStart = adminReportExportApiDeclaration.indexOf('productBreakdownXlsx:')
  const productBreakdownXlsxExportEnd = adminReportExportApiDeclaration.indexOf('paymentReconciliationXlsx:', productBreakdownXlsxExportStart)
  assert(productBreakdownXlsxExportStart >= 0, 'admin report exports must declare productBreakdownXlsx')
  assert(productBreakdownXlsxExportEnd > productBreakdownXlsxExportStart, 'admin report product breakdown XLSX export block must be bounded')
  const productBreakdownXlsxExportBlock = adminReportExportApiDeclaration.slice(
    productBreakdownXlsxExportStart,
    productBreakdownXlsxExportEnd,
  )
  assertContains(productBreakdownXlsxExportBlock, '/api/admin/reports/product-breakdown.xlsx${buildAdminReportSearch(params)}', 'admin product breakdown XLSX export block must use report search')
  assertContains(productBreakdownXlsxExportBlock, "accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin product breakdown XLSX export accept header')
  assertContains(productBreakdownXlsxExportBlock, "expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", 'admin product breakdown XLSX export content type guard')
  const trendXlsxExportBlocks = [
    ['dailyTrendXlsx:', 'hourlyTrendCsv:', '/api/admin/reports/daily-trend.xlsx${buildAdminTrendReportSearch(params)}'],
    ['hourlyTrendXlsx:', 'monthlyTrendCsv:', '/api/admin/reports/hourly-trend.xlsx${buildAdminTrendReportSearch(params)}'],
    ['monthlyTrendXlsx:', 'ordersCsv:', '/api/admin/reports/monthly-trend.xlsx${buildAdminTrendReportSearch(params)}'],
  ]
  for (const [startMarker, endMarker, endpointText] of trendXlsxExportBlocks) {
    const blockStart = adminReportExportApiDeclaration.indexOf(startMarker)
    const blockEnd = adminReportExportApiDeclaration.indexOf(endMarker, blockStart)
    assert(blockStart >= 0, `admin report exports must declare ${startMarker}`)
    assert(blockEnd > blockStart, `admin report ${startMarker} block must be bounded`)
    const block = adminReportExportApiDeclaration.slice(blockStart, blockEnd)
    assertContains(block, endpointText, `admin report ${startMarker} block must use trend search`)
    assertContains(block, "accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", `admin report ${startMarker} accept header`)
    assertContains(block, "expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'", `admin report ${startMarker} content type guard`)
  }
  assertContains(endpoints.text, 'encodeURIComponent(orderNo)', 'order number path encoding')

  const adminOrderListRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/orders${}',
    typeArgument: 'AdminOrderList',
  })
  const adminOrderDetailRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/orders/${}',
    typeArgument: 'AdminOrderDetail',
  })
  const adminReportSummaryRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/reports/summary${}',
    typeArgument: 'AdminReportSummary',
  })
  const adminPaymentReconciliationRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/reports/payment-reconciliation${}',
    typeArgument: 'AdminPaymentReconciliation',
  })
  const adminReportProductRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/reports/product-breakdown${}',
    typeArgument: 'AdminProductBreakdown[]',
  })
  const adminReportTrendRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/reports/daily-trend${}',
    typeArgument: 'AdminDailyTrend[]',
  })
  const adminReportHourlyTrendRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/reports/hourly-trend${}',
    typeArgument: 'AdminHourlyTrend[]',
  })
  const adminReportMonthlyTrendRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/reports/monthly-trend${}',
    typeArgument: 'AdminMonthlyTrend[]',
  })
  const adminRefundAuditLogSearchRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/refund-logs${}',
    typeArgument: 'AdminRefundAuditLogList',
  })
  const adminCheckInFailureAuditLogSearchRequest = assertEndpoint(requests, {
    method: 'GET',
    path: '/api/admin/check-in-failure-logs${}',
    typeArgument: 'AdminCheckInFailureAuditLogList',
  })
  const adminRefundRequest = assertEndpoint(requests, {
    method: 'POST',
    path: '/api/admin/orders/${}/refund',
    typeArgument: 'AdminRefund',
  })
  const adminPartialRefundRequest = assertEndpoint(requests, {
    method: 'POST',
    path: '/api/admin/orders/${}/refund/items',
    typeArgument: 'AdminPartialRefund',
  })
  assert(!adminOrderListRequest.hasIdempotencyKey && !adminOrderListRequest.skipCsrf, 'admin order list must stay read-only GET without mutating headers')
  assert(!adminOrderDetailRequest.hasIdempotencyKey && !adminOrderDetailRequest.skipCsrf, 'admin order detail must stay read-only GET without mutating headers')
  assert(!adminReportSummaryRequest.hasIdempotencyKey && !adminReportSummaryRequest.skipCsrf, 'admin report summary must stay read-only GET without mutating headers')
  assert(!adminPaymentReconciliationRequest.hasIdempotencyKey && !adminPaymentReconciliationRequest.skipCsrf, 'admin payment reconciliation must stay read-only GET without mutating headers')
  assert(!adminReportProductRequest.hasIdempotencyKey && !adminReportProductRequest.skipCsrf, 'admin report product breakdown must stay read-only GET without mutating headers')
  assert(!adminReportTrendRequest.hasIdempotencyKey && !adminReportTrendRequest.skipCsrf, 'admin report daily trend must stay read-only GET without mutating headers')
  assert(!adminReportHourlyTrendRequest.hasIdempotencyKey && !adminReportHourlyTrendRequest.skipCsrf, 'admin report hourly trend must stay read-only GET without mutating headers')
  assert(!adminReportMonthlyTrendRequest.hasIdempotencyKey && !adminReportMonthlyTrendRequest.skipCsrf, 'admin report monthly trend must stay read-only GET without mutating headers')
  assert(!adminRefundAuditLogSearchRequest.hasIdempotencyKey && !adminRefundAuditLogSearchRequest.skipCsrf, 'admin refund audit search must stay read-only GET without mutating headers')
  assert(!adminCheckInFailureAuditLogSearchRequest.hasIdempotencyKey && !adminCheckInFailureAuditLogSearchRequest.skipCsrf, 'admin check-in failure audit search must stay read-only GET without mutating headers')
  assert(!adminRefundRequest.hasIdempotencyKey && !adminRefundRequest.skipCsrf, 'admin full refund must stay CSRF-protected without idempotency key')
  assert(!adminPartialRefundRequest.hasIdempotencyKey && !adminPartialRefundRequest.skipCsrf, 'admin partial refund must stay CSRF-protected without idempotency key')
  assertNotContains(adminPartialRefundRequest.text, 'refundedAmount', 'admin partial refund request body')
  assertNotContains(adminPartialRefundRequest.text, 'orderStatus', 'admin partial refund request body')
  assertNotContains(adminPartialRefundRequest.text, 'paymentStatus', 'admin partial refund request body')
  assertNotContains(adminPartialRefundRequest.text, 'inventory', 'admin partial refund request body')

  const {
    buildAdminCheckInAuditLogExportSearch,
    buildAdminCheckInFailureAuditLogExportSearch,
    buildAdminCheckInFailureAuditLogSearch,
    buildAdminOrderListSearch,
    buildAdminRefundAuditLogExportSearch,
    buildAdminRefundAuditLogSearch,
    buildAdminReportSearch,
    buildAdminTrendReportSearch,
  } = loadRuntimeFunctions(searchBuilders.sourceFile, [
    'buildSearch',
    'compactText',
    'buildAdminOrderListSearch',
    'buildAdminReportSearch',
    'buildAdminTrendReportSearch',
    'buildAdminRefundAuditLogSearch',
    'buildAdminRefundAuditLogExportSearch',
    'buildAdminCheckInAuditLogExportSearch',
    'buildAdminCheckInFailureAuditLogSearch',
    'buildAdminCheckInFailureAuditLogExportSearch',
  ])
  assert(
    buildAdminOrderListSearch({ orderNo: ' ORD ', buyerPhone: '   ', page: 2, pageSize: 50 }) === '?orderNo=ORD&page=2&pageSize=50',
    'admin order search must trim text filters and omit blank buyerPhone',
  )
  assert(
    buildAdminOrderListSearch({ status: 'PAID', paymentStatus: 'PARTIAL_REFUND', buyerPhone: '2222' }) === '?status=PAID&paymentStatus=PARTIAL_REFUND&buyerPhone=2222',
    'admin order search must encode allowed filters in contract order',
  )
  assert(buildAdminOrderListSearch() === '', 'admin order search without params must not add ?')
  assert(
    buildAdminReportSearch({ dateFrom: ' 2026-06-26 ', dateTo: '2026-06-28' }) === '?dateFrom=2026-06-26&dateTo=2026-06-28',
    'admin report search must trim and encode date range filters',
  )
  assert(buildAdminReportSearch({ dateFrom: ' ', dateTo: '' }) === '', 'admin report search must omit blank dates')
  assert(
    buildAdminReportSearch({ dateFrom: '2026-06-26', dateTo: '2026-06-28', includeEmpty: true }) === '?dateFrom=2026-06-26&dateTo=2026-06-28',
    'admin report search must not leak trend-only includeEmpty to summary/product/export endpoints',
  )
  assert(
    buildAdminTrendReportSearch({ dateFrom: ' 2026-06-26 ', dateTo: '2026-06-28', includeEmpty: true }) === '?dateFrom=2026-06-26&dateTo=2026-06-28&includeEmpty=true',
    'admin trend report search must trim date filters and encode includeEmpty',
  )
  assert(
    buildAdminTrendReportSearch({ includeEmpty: false }) === '',
    'admin trend report search must omit false includeEmpty',
  )
  assert(
    buildAdminRefundAuditLogSearch({
      refundType: 'PARTIAL',
      orderNo: ' YT2606280003 ',
      operatorUsername: ' admin ',
      dateFrom: '2026-06-28',
      page: 2,
      pageSize: 5,
    }) === '?refundType=PARTIAL&orderNo=YT2606280003&operatorUsername=admin&dateFrom=2026-06-28&page=2&pageSize=5',
    'admin refund audit search must trim and encode filters in contract order',
  )
  assert(buildAdminRefundAuditLogSearch({ orderNo: ' ', operatorUsername: '' }) === '', 'admin refund audit search must omit blank filters')
  assert(
    buildAdminRefundAuditLogExportSearch({
      refundType: 'PARTIAL',
      orderNo: ' YT2606280003 ',
      operatorUsername: ' admin ',
      dateFrom: '2026-06-28',
      dateTo: '2026-06-28',
    }) === '?refundType=PARTIAL&orderNo=YT2606280003&operatorUsername=admin&dateFrom=2026-06-28&dateTo=2026-06-28',
    'admin refund audit XLSX export search must trim and encode filters without pagination',
  )
  assert(
    !buildAdminRefundAuditLogExportSearch({
      orderNo: 'YT2606280003',
      page: 2,
      pageSize: 50,
    }).includes('page'),
    'admin refund audit XLSX export search must ignore pagination params',
  )
  assert(
    buildAdminCheckInAuditLogExportSearch({
      ticketCode: ' TK2606280001A ',
      orderNo: ' YT2606280001 ',
      operatorUsername: ' admin ',
      reason: ' 误核 ',
      dateFrom: '2026-06-28',
      dateTo: '2026-06-29',
    }) === '?ticketCode=TK2606280001A&orderNo=YT2606280001&operatorUsername=admin&reason=%E8%AF%AF%E6%A0%B8&dateFrom=2026-06-28&dateTo=2026-06-29',
    'admin check-in audit export search must trim and encode filters in contract order',
  )
  assert(
    !buildAdminCheckInAuditLogExportSearch({
      ticketCode: 'TK2606280001A',
      page: 2,
      pageSize: 50,
    }).includes('page'),
    'admin check-in audit CSV/XLSX export search must ignore pagination params',
  )
  assert(
    buildAdminCheckInFailureAuditLogSearch({
      ticketCode: ' TK-MISSING ',
      failureCode: 'TICKET_NOT_FOUND',
      operatorUsername: ' admin ',
      dateFrom: '2026-07-01',
      dateTo: '2026-07-01',
      page: 2,
      pageSize: 5,
    }) === '?ticketCode=TK-MISSING&failureCode=TICKET_NOT_FOUND&operatorUsername=admin&dateFrom=2026-07-01&dateTo=2026-07-01&page=2&pageSize=5',
    'admin check-in failure audit search must trim and encode filters in contract order',
  )
  assert(buildAdminCheckInFailureAuditLogSearch({ ticketCode: ' ', operatorUsername: '' }) === '', 'admin check-in failure audit search must omit blank filters')
  assert(
    buildAdminCheckInFailureAuditLogExportSearch({
      ticketCode: ' TK-MISSING ',
      failureCode: 'TICKET_NOT_CHECKED_IN',
      operatorUsername: ' shift-b ',
      dateFrom: '2026-07-01',
      dateTo: '2026-07-31',
    }) === '?ticketCode=TK-MISSING&failureCode=TICKET_NOT_CHECKED_IN&operatorUsername=shift-b&dateFrom=2026-07-01&dateTo=2026-07-31',
    'admin check-in failure audit CSV export search must trim and encode filters without pagination',
  )
  assert(
    !buildAdminCheckInFailureAuditLogExportSearch({
      ticketCode: 'TK-MISSING',
      page: 2,
      pageSize: 50,
    }).includes('page'),
    'admin check-in failure audit CSV export search must ignore pagination params',
  )

  return { requests }
}
