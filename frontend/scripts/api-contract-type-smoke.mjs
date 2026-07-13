import ts from 'typescript'
import {
  assert,
  assertContains,
  assertExactPropertyContract,
  assertNotContains,
  assertStringLiteralUnion,
  assertTypeAliasText,
  assertTypeExportBarrel,
  parseSource,
} from './api-contract-smoke-utils.mjs'

export async function runSharedApiTypeContracts() {
  const barrelTypes = await parseSource('shared/api/types.ts')
  const commonTypes = await parseSource('shared/api/types/common.ts')
  const authTypes = await parseSource('shared/api/types/auth.ts')
  const catalogTypes = await parseSource('shared/api/types/catalog.ts')
  const orderTypes = await parseSource('shared/api/types/orders.ts')
  const adminCheckInTypes = await parseSource('shared/api/types/adminCheckIns.ts')
  const adminRefundTypes = await parseSource('shared/api/types/adminRefunds.ts')
  const adminReportTypes = await parseSource('shared/api/types/adminReports.ts')
  const adminExportTypes = await parseSource('shared/api/types/adminExports.ts')

  const types = {
    sourceFile: ts.createSourceFile(
      'shared/api/domain-types.ts',
      [
        commonTypes.text,
        authTypes.text,
        catalogTypes.text,
        orderTypes.text,
        adminCheckInTypes.text,
        adminRefundTypes.text,
      ].join('\n'),
      ts.ScriptTarget.Latest,
      true,
      ts.ScriptKind.TS,
    ),
  }

  assertContains(barrelTypes.text, "from './types/common'", 'shared API type barrel')
  assertContains(barrelTypes.text, "from './types/auth'", 'shared API type barrel')
  assertContains(barrelTypes.text, "from './types/catalog'", 'shared API type barrel')
  assertContains(barrelTypes.text, "from './types/orders'", 'shared API type barrel')
  assertContains(barrelTypes.text, "from './types/adminCheckIns'", 'shared API type barrel')
  assertContains(barrelTypes.text, "from './types/adminRefunds'", 'shared API type barrel')
  assertNotContains(barrelTypes.text, 'export type ApiSuccess<T> =', 'shared API type barrel')
  assertNotContains(barrelTypes.text, 'export type OrderMe =', 'shared API type barrel')
  assertNotContains(barrelTypes.text, 'export type AdminRefundAuditLog =', 'shared API type barrel')
  assertTypeExportBarrel(barrelTypes, 120)

  assertExactPropertyContract(types.sourceFile, 'ApiSuccess', {
    success: { optional: false, type: 'true' },
    data: { optional: false, type: 'T' },
    request_id: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'ApiFailure', {
    success: { optional: false, type: 'false' },
    code: { optional: false, type: 'string' },
    message: { optional: false, type: 'string' },
    request_id: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'VisitorMe', {
    visitorId: { optional: false, type: 'number' },
    visitorName: { optional: false, type: 'string' },
    phone: { optional: false, type: 'string' },
    visitorScope: { optional: false, type: 'VisitorScope' },
    isRegistered: { optional: false, type: 'boolean' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminMe', {
    adminUserId: { optional: false, type: 'number' },
    username: { optional: false, type: 'string' },
    displayName: { optional: false, type: 'string' },
    role: { optional: false, type: 'AdminRole' },
  })
  assertExactPropertyContract(types.sourceFile, 'LogoutPayload', {
    loggedOut: { optional: false, type: 'true' },
  })
  assertExactPropertyContract(types.sourceFile, 'CsrfPayload', {
    headerName: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'HealthPayload', {
    status: { optional: false, type: "'ok'" },
    service: { optional: false, type: 'string' },
    environment: { optional: false, type: 'string' },
  })
  assertTypeAliasText(types.sourceFile, 'DatabaseHealthPayload', "HealthPayload & {\n  database: 'ok'\n}")
  assertExactPropertyContract(types.sourceFile, 'VisitorLoginRequest', {
    username: { optional: false, type: 'string' },
    password: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminLoginRequest', {
    username: { optional: false, type: 'string' },
    password: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'VisitorRegisterRequest', {
    username: { optional: false, type: 'string' },
    password: { optional: false, type: 'string' },
    phone: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'ProductPublic', {
    productId: { optional: false, type: 'number' },
    ticketTypeId: { optional: false, type: 'number' },
    scenicSpotName: { optional: false, type: 'string' },
    productName: { optional: false, type: 'string' },
    ticketName: { optional: false, type: 'string' },
    ticketCategory: { optional: false, type: 'string' },
    originalPrice: { optional: false, type: 'string' },
    salePrice: { optional: false, type: 'string' },
    description: { optional: true, type: 'string | null' },
    refundRule: { optional: true, type: 'string | null' },
    realNameRequired: { optional: false, type: 'boolean' },
    tripType: { optional: false, type: 'string' },
    raftCapacity: { optional: false, type: 'number' },
    startPierName: { optional: false, type: 'string' },
    endPierName: { optional: false, type: 'string' },
    windowPhone: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'TimeSlotPublic', {
    timeSlotId: { optional: false, type: 'number' },
    productId: { optional: false, type: 'number' },
    ticketTypeId: { optional: false, type: 'number' },
    visitDate: { optional: false, type: 'string' },
    slotStartTime: { optional: false, type: 'string' },
    slotEndTime: { optional: false, type: 'string' },
    quotaRemaining: { optional: false, type: 'number' },
  })
  assertExactPropertyContract(types.sourceFile, 'OrderCreateItemRequest', {
    productId: { optional: false, type: 'number' },
    timeSlotId: { optional: false, type: 'number' },
    visitDate: { optional: false, type: 'string' },
    quantity: { optional: false, type: 'number' },
    passengers: { optional: false, type: 'OrderPassengerRequest[]' },
  })
  assertExactPropertyContract(types.sourceFile, 'OrderPassengerRequest', {
    passengerName: { optional: false, type: 'string' },
    idType: { optional: false, type: 'string' },
    idNumber: { optional: false, type: 'string' },
    phone: { optional: false, type: 'string' },
    templateId: { optional: true, type: 'number' },
  })
  assertExactPropertyContract(types.sourceFile, 'OrderCreateRequest', {
    buyerName: { optional: false, type: 'string' },
    buyerPhone: { optional: false, type: 'string' },
    items: { optional: false, type: 'OrderCreateItemRequest[]' },
  })
  assertExactPropertyContract(types.sourceFile, 'OrderItemMe', {
    itemNo: { optional: false, type: 'string' },
    productId: { optional: false, type: 'number' },
    ticketTypeId: { optional: false, type: 'number' },
    productName: { optional: false, type: 'string' },
    ticketName: { optional: false, type: 'string' },
    timeSlotId: { optional: false, type: 'number' },
    visitDate: { optional: false, type: 'string' },
    slotStartTime: { optional: false, type: 'string' },
    slotEndTime: { optional: false, type: 'string' },
    originalPrice: { optional: false, type: 'string' },
    finalPrice: { optional: false, type: 'string' },
    itemStatus: { optional: false, type: 'OrderItemStatus' },
    ticketCode: { optional: true, type: 'string' },
    passengerName: { optional: false, type: 'string' },
    passengerIdType: { optional: false, type: 'string' },
    passengerIdNumberMasked: { optional: false, type: 'string' },
    passengerPhoneMasked: { optional: false, type: 'string' },
    raftNo: { optional: true, type: 'number | null' },
    raftSeatNo: { optional: true, type: 'number | null' },
    raftAssignedAt: { optional: true, type: 'string | null' },
  })
  assertExactPropertyContract(types.sourceFile, 'OrderMe', {
    orderNo: { optional: false, type: 'string' },
    buyerName: { optional: false, type: 'string' },
    buyerPhone: { optional: false, type: 'string' },
    orderStatus: { optional: false, type: 'OrderStatus' },
    paymentStatus: { optional: false, type: 'PaymentStatus' },
    totalAmount: { optional: false, type: 'string' },
    payableAmount: { optional: false, type: 'string' },
    orderTime: { optional: false, type: 'string' },
    canSelfRefund: { optional: false, type: 'boolean' },
    refundDeadline: { optional: true, type: 'string' },
    items: { optional: false, type: 'OrderItemMe[]' },
  })
  assertTypeAliasText(types.sourceFile, 'OrderSummary', 'OrderMe')
  assertTypeAliasText(types.sourceFile, 'MyOrderDetail', 'OrderMe')
  assertStringLiteralUnion(types.sourceFile, 'OrderStatusFilter', ['CREATED', 'PAID', 'CANCELLED', 'REFUNDED'])
  assertStringLiteralUnion(types.sourceFile, 'AdminOrderStatusFilter', ['CREATED', 'PAID', 'CANCELLED', 'COMPLETED', 'REFUNDING', 'REFUNDED'])
  assertStringLiteralUnion(types.sourceFile, 'AdminPaymentStatusFilter', ['UNPAID', 'PAID', 'PARTIAL_REFUND', 'REFUNDED', 'FAILED'])
  assertExactPropertyContract(types.sourceFile, 'AdminOrderListParams', {
    status: { optional: true, type: 'AdminOrderStatusFilter' },
    paymentStatus: { optional: true, type: 'AdminPaymentStatusFilter' },
    orderNo: { optional: true, type: 'string' },
    buyerPhone: { optional: true, type: 'string' },
    page: { optional: true, type: 'number' },
    pageSize: { optional: true, type: 'number' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminOrderSummary', {
    orderNo: { optional: false, type: 'string' },
    visitorId: { optional: false, type: 'number' },
    buyerName: { optional: false, type: 'string' },
    buyerPhoneMasked: { optional: false, type: 'string' },
    orderStatus: { optional: false, type: 'AdminOrderStatus' },
    paymentStatus: { optional: false, type: 'AdminPaymentStatus' },
    totalAmount: { optional: false, type: 'string' },
    payableAmount: { optional: false, type: 'string' },
    orderTime: { optional: false, type: 'string' },
    itemCount: { optional: false, type: 'number' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminOrderList', {
    items: { optional: false, type: 'AdminOrderSummary[]' },
    total: { optional: false, type: 'number' },
    page: { optional: false, type: 'number' },
    pageSize: { optional: false, type: 'number' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminOrderItem', {
    itemNo: { optional: false, type: 'string' },
    productId: { optional: false, type: 'number' },
    ticketTypeId: { optional: false, type: 'number' },
    productName: { optional: false, type: 'string' },
    ticketName: { optional: false, type: 'string' },
    timeSlotId: { optional: false, type: 'number' },
    visitDate: { optional: false, type: 'string' },
    slotStartTime: { optional: false, type: 'string' },
    slotEndTime: { optional: false, type: 'string' },
    originalPrice: { optional: false, type: 'string' },
    finalPrice: { optional: false, type: 'string' },
    itemStatus: { optional: false, type: 'OrderItemStatus' },
    ticketCode: { optional: true, type: 'string | null' },
    passengerName: { optional: false, type: 'string' },
    passengerIdType: { optional: false, type: 'string' },
    passengerIdNumberMasked: { optional: false, type: 'string' },
    passengerPhoneMasked: { optional: false, type: 'string' },
    raftNo: { optional: true, type: 'number | null' },
    raftSeatNo: { optional: true, type: 'number | null' },
    raftAssignedAt: { optional: true, type: 'string | null' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminOrderDetail', {
    orderNo: { optional: false, type: 'string' },
    visitorId: { optional: false, type: 'number' },
    buyerName: { optional: false, type: 'string' },
    buyerPhoneMasked: { optional: false, type: 'string' },
    orderStatus: { optional: false, type: 'AdminOrderStatus' },
    paymentStatus: { optional: false, type: 'AdminPaymentStatus' },
    totalAmount: { optional: false, type: 'string' },
    payableAmount: { optional: false, type: 'string' },
    orderTime: { optional: false, type: 'string' },
    items: { optional: false, type: 'AdminOrderItem[]' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminCheckInRequest', {
    ticketCode: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminBatchCheckInRequest', {
    ticketCodes: { optional: false, type: 'string[]' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminBatchUndoCheckInRequest', {
    ticketCodes: { optional: false, type: 'string[]' },
    reason: { optional: true, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminCheckIn', {
    orderNo: { optional: false, type: 'string' },
    itemNo: { optional: false, type: 'string' },
    ticketCode: { optional: false, type: 'string' },
    orderStatus: { optional: false, type: 'AdminOrderStatus' },
    itemStatus: { optional: false, type: 'OrderItemStatus' },
    checkedInAt: { optional: false, type: 'string' },
    raftNo: { optional: true, type: 'number | null' },
    raftSeatNo: { optional: true, type: 'number | null' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminUndoCheckIn', {
    orderNo: { optional: false, type: 'string' },
    itemNo: { optional: false, type: 'string' },
    ticketCode: { optional: false, type: 'string' },
    orderStatus: { optional: false, type: 'AdminOrderStatus' },
    itemStatus: { optional: false, type: 'OrderItemStatus' },
    undoneAt: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminBatchCheckInSuccessResult', {
    ticketCode: { optional: false, type: 'string' },
    success: { optional: false, type: 'true' },
    checkIn: { optional: false, type: 'AdminCheckIn' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminBatchCheckInFailureResult', {
    ticketCode: { optional: false, type: 'string' },
    success: { optional: false, type: 'false' },
    code: { optional: false, type: 'string' },
    message: { optional: false, type: 'string' },
  })
  assertTypeAliasText(types.sourceFile, 'AdminBatchCheckInResult', 'AdminBatchCheckInSuccessResult | AdminBatchCheckInFailureResult')
  assertExactPropertyContract(types.sourceFile, 'AdminBatchCheckIn', {
    totalCount: { optional: false, type: 'number' },
    successCount: { optional: false, type: 'number' },
    failureCount: { optional: false, type: 'number' },
    results: { optional: false, type: 'AdminBatchCheckInResult[]' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminBatchUndoCheckInSuccessResult', {
    ticketCode: { optional: false, type: 'string' },
    success: { optional: false, type: 'true' },
    undoCheckIn: { optional: false, type: 'AdminUndoCheckIn' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminBatchUndoCheckInFailureResult', {
    ticketCode: { optional: false, type: 'string' },
    success: { optional: false, type: 'false' },
    code: { optional: false, type: 'string' },
    message: { optional: false, type: 'string' },
  })
  assertTypeAliasText(
    types.sourceFile,
    'AdminBatchUndoCheckInResult',
    '| AdminBatchUndoCheckInSuccessResult\n  | AdminBatchUndoCheckInFailureResult',
  )
  assertExactPropertyContract(types.sourceFile, 'AdminBatchUndoCheckIn', {
    totalCount: { optional: false, type: 'number' },
    successCount: { optional: false, type: 'number' },
    failureCount: { optional: false, type: 'number' },
    results: { optional: false, type: 'AdminBatchUndoCheckInResult[]' },
  })
  assertTypeAliasText(types.sourceFile, 'AdminCheckInAuditLogAction', "'CHECK_IN' | 'UNDO_CHECK_IN'")
  assertExactPropertyContract(types.sourceFile, 'AdminCheckInAuditLog', {
    orderNo: { optional: false, type: 'string' },
    itemNo: { optional: false, type: 'string' },
    ticketCode: { optional: false, type: 'string' },
    action: { optional: false, type: 'AdminCheckInAuditLogAction' },
    reason: { optional: false, type: 'string | null' },
    operatorUsername: { optional: false, type: 'string' },
    operatorDisplayName: { optional: false, type: 'string' },
    requestId: { optional: false, type: 'string | null' },
    createdAt: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminCheckInAuditLogExportParams', {
    ticketCode: { optional: true, type: 'string' },
    orderNo: { optional: true, type: 'string' },
    operatorUsername: { optional: true, type: 'string' },
    reason: { optional: true, type: 'string' },
    dateFrom: { optional: true, type: 'string' },
    dateTo: { optional: true, type: 'string' },
  })
  assertTypeAliasText(
    types.sourceFile,
    'AdminCheckInFailureCode',
    "| 'TICKET_NOT_FOUND'\n  | 'TICKET_ALREADY_USED'\n  | 'TICKET_NOT_CHECKABLE'\n  | 'TICKET_NOT_CHECKED_IN'\n  | 'TICKET_UNDO_NOT_ALLOWED'",
  )
  assertExactPropertyContract(types.sourceFile, 'AdminCheckInFailureAuditLog', {
    ticketCode: { optional: false, type: 'string' },
    action: { optional: false, type: "'CHECK_IN' | 'UNDO_CHECK_IN'" },
    failureCode: { optional: false, type: 'AdminCheckInFailureCode' },
    failureMessage: { optional: false, type: 'string' },
    operatorUsername: { optional: false, type: 'string' },
    operatorDisplayName: { optional: false, type: 'string' },
    requestId: { optional: false, type: 'string | null' },
    createdAt: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminCheckInFailureAuditLogParams', {
    ticketCode: { optional: true, type: 'string' },
    failureCode: { optional: true, type: 'AdminCheckInFailureCode' },
    operatorUsername: { optional: true, type: 'string' },
    dateFrom: { optional: true, type: 'string' },
    dateTo: { optional: true, type: 'string' },
    page: { optional: true, type: 'number' },
    pageSize: { optional: true, type: 'number' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminCheckInFailureAuditLogExportParams', {
    ticketCode: { optional: true, type: 'string' },
    failureCode: { optional: true, type: 'AdminCheckInFailureCode' },
    operatorUsername: { optional: true, type: 'string' },
    dateFrom: { optional: true, type: 'string' },
    dateTo: { optional: true, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminCheckInFailureAuditLogList', {
    items: { optional: false, type: 'AdminCheckInFailureAuditLog[]' },
    total: { optional: false, type: 'number' },
    page: { optional: false, type: 'number' },
    pageSize: { optional: false, type: 'number' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminRefundRequest', {
    reason: { optional: true, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminRefund', {
    orderNo: { optional: false, type: 'string' },
    orderStatus: { optional: false, type: 'AdminOrderStatus' },
    paymentStatus: { optional: false, type: 'AdminPaymentStatus' },
    refundedAmount: { optional: false, type: 'string' },
    refundedItemCount: { optional: false, type: 'number' },
    refundedAt: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminPartialRefundRequest', {
    itemNos: { optional: false, type: 'string[]' },
    reason: { optional: true, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminPartialRefund', {
    orderNo: { optional: false, type: 'string' },
    orderStatus: { optional: false, type: 'AdminOrderStatus' },
    paymentStatus: { optional: false, type: 'AdminPaymentStatus' },
    refundedAmount: { optional: false, type: 'string' },
    refundedItemCount: { optional: false, type: 'number' },
    refundedItemNos: { optional: false, type: 'string[]' },
    refundedAt: { optional: false, type: 'string' },
  })
  assertTypeAliasText(types.sourceFile, 'AdminRefundType', "'FULL' | 'PARTIAL'")
  assertExactPropertyContract(types.sourceFile, 'AdminRefundAuditLog', {
    orderNo: { optional: false, type: 'string' },
    refundType: { optional: false, type: 'AdminRefundType' },
    refundedAmount: { optional: false, type: 'string' },
    refundedItemCount: { optional: false, type: 'number' },
    refundedItemNos: { optional: false, type: 'string[]' },
    reason: { optional: false, type: 'string | null' },
    operatorUsername: { optional: false, type: 'string' },
    operatorDisplayName: { optional: false, type: 'string' },
    requestId: { optional: false, type: 'string | null' },
    createdAt: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminRefundAuditLogParams', {
    refundType: { optional: true, type: 'AdminRefundType' },
    orderNo: { optional: true, type: 'string' },
    operatorUsername: { optional: true, type: 'string' },
    dateFrom: { optional: true, type: 'string' },
    dateTo: { optional: true, type: 'string' },
    page: { optional: true, type: 'number' },
    pageSize: { optional: true, type: 'number' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminRefundAuditLogExportParams', {
    refundType: { optional: true, type: 'AdminRefundType' },
    orderNo: { optional: true, type: 'string' },
    operatorUsername: { optional: true, type: 'string' },
    dateFrom: { optional: true, type: 'string' },
    dateTo: { optional: true, type: 'string' },
  })
  assertExactPropertyContract(types.sourceFile, 'AdminRefundAuditLogList', {
    items: { optional: false, type: 'AdminRefundAuditLog[]' },
    total: { optional: false, type: 'number' },
    page: { optional: false, type: 'number' },
    pageSize: { optional: false, type: 'number' },
  })
  assertExactPropertyContract(adminReportTypes.sourceFile, 'AdminReportParams', {
    dateFrom: { optional: true, type: 'string' },
    dateTo: { optional: true, type: 'string' },
  })
  assertExactPropertyContract(adminReportTypes.sourceFile, 'AdminTrendReportParams', {
    dateFrom: { optional: true, type: 'string' },
    dateTo: { optional: true, type: 'string' },
    includeEmpty: { optional: true, type: 'boolean' },
  })
  assertExactPropertyContract(adminReportTypes.sourceFile, 'AdminReportSummary', {
    dateFrom: { optional: false, type: 'string' },
    dateTo: { optional: false, type: 'string' },
    orderCount: { optional: false, type: 'number' },
    paidOrderCount: { optional: false, type: 'number' },
    completedOrderCount: { optional: false, type: 'number' },
    refundedOrderCount: { optional: false, type: 'number' },
    cancelledOrderCount: { optional: false, type: 'number' },
    netPaidAmount: { optional: false, type: 'string' },
    ticketCount: { optional: false, type: 'number' },
    soldTicketCount: { optional: false, type: 'number' },
    checkedInTicketCount: { optional: false, type: 'number' },
    refundedTicketCount: { optional: false, type: 'number' },
  })
  assertExactPropertyContract(adminReportTypes.sourceFile, 'AdminPaymentReconciliation', {
    dateFrom: { optional: false, type: 'string' },
    dateTo: { optional: false, type: 'string' },
    orderNetPaidAmount: { optional: false, type: 'string' },
    capturedPaymentAmount: { optional: false, type: 'string' },
    refundAuditAmount: { optional: false, type: 'string' },
    expectedNetAmount: { optional: false, type: 'string' },
    unreconciledAmount: { optional: false, type: 'string' },
    capturedPaymentCount: { optional: false, type: 'number' },
    refundAuditLogCount: { optional: false, type: 'number' },
    reconciled: { optional: false, type: 'boolean' },
  })
  assertExactPropertyContract(adminReportTypes.sourceFile, 'AdminProductBreakdown', {
    productId: { optional: false, type: 'number' },
    ticketTypeId: { optional: false, type: 'number' },
    productName: { optional: false, type: 'string' },
    ticketName: { optional: false, type: 'string' },
    orderCount: { optional: false, type: 'number' },
    ticketCount: { optional: false, type: 'number' },
    soldTicketCount: { optional: false, type: 'number' },
    checkedInTicketCount: { optional: false, type: 'number' },
    refundedTicketCount: { optional: false, type: 'number' },
    netPaidAmount: { optional: false, type: 'string' },
  })
  assertExactPropertyContract(adminReportTypes.sourceFile, 'AdminDailyTrend', {
    reportDate: { optional: false, type: 'string' },
    orderCount: { optional: false, type: 'number' },
    paidOrderCount: { optional: false, type: 'number' },
    completedOrderCount: { optional: false, type: 'number' },
    refundedOrderCount: { optional: false, type: 'number' },
    cancelledOrderCount: { optional: false, type: 'number' },
    netPaidAmount: { optional: false, type: 'string' },
    ticketCount: { optional: false, type: 'number' },
    soldTicketCount: { optional: false, type: 'number' },
    checkedInTicketCount: { optional: false, type: 'number' },
    refundedTicketCount: { optional: false, type: 'number' },
  })
  assertExactPropertyContract(adminReportTypes.sourceFile, 'AdminHourlyTrend', {
    reportHour: { optional: false, type: 'string' },
    orderCount: { optional: false, type: 'number' },
    paidOrderCount: { optional: false, type: 'number' },
    completedOrderCount: { optional: false, type: 'number' },
    refundedOrderCount: { optional: false, type: 'number' },
    cancelledOrderCount: { optional: false, type: 'number' },
    netPaidAmount: { optional: false, type: 'string' },
    ticketCount: { optional: false, type: 'number' },
    soldTicketCount: { optional: false, type: 'number' },
    checkedInTicketCount: { optional: false, type: 'number' },
    refundedTicketCount: { optional: false, type: 'number' },
  })
  assertExactPropertyContract(adminReportTypes.sourceFile, 'AdminMonthlyTrend', {
    reportMonth: { optional: false, type: 'string' },
    orderCount: { optional: false, type: 'number' },
    paidOrderCount: { optional: false, type: 'number' },
    completedOrderCount: { optional: false, type: 'number' },
    refundedOrderCount: { optional: false, type: 'number' },
    cancelledOrderCount: { optional: false, type: 'number' },
    netPaidAmount: { optional: false, type: 'string' },
    ticketCount: { optional: false, type: 'number' },
    soldTicketCount: { optional: false, type: 'number' },
    checkedInTicketCount: { optional: false, type: 'number' },
    refundedTicketCount: { optional: false, type: 'number' },
  })
  assertContains(barrelTypes.text, "from './types/adminReports'", 'shared api types barrel re-exports admin report DTOs')
  assertContains(barrelTypes.text, "from './types/adminExports'", 'shared api types barrel re-exports admin export DTOs')

  assertContains(adminExportTypes.text, "export type AdminExportType =", 'admin export job type union')
  assertContains(adminExportTypes.text, "'PAYMENT_RECONCILIATION'", 'admin export job payment reconciliation type')
  assertContains(adminExportTypes.text, "export type AdminExportJobStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED'", 'admin export job status union')
  assertContains(adminExportTypes.text, 'export type AdminExportJobCreateRequest', 'admin export job create request DTO')
  assertContains(adminExportTypes.text, 'export type AdminExportJobList', 'admin export job list DTO')
  assertContains(adminExportTypes.text, 'jobId: string', 'admin export job exposes public jobId')
  assertContains(adminExportTypes.text, 'requestId: string | null', 'admin export job exposes requestId for correlation')
  assert(!adminExportTypes.text.includes('storageKey'), 'admin export job DTO must not expose storageKey')
}
