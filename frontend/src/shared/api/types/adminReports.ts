export type AdminReportParams = {
  dateFrom?: string
  dateTo?: string
}

export type AdminTrendReportParams = {
  dateFrom?: string
  dateTo?: string
  includeEmpty?: boolean
}

export type AdminReportSummary = {
  dateFrom: string
  dateTo: string
  orderCount: number
  paidOrderCount: number
  completedOrderCount: number
  refundedOrderCount: number
  cancelledOrderCount: number
  netPaidAmount: string
  ticketCount: number
  soldTicketCount: number
  checkedInTicketCount: number
  refundedTicketCount: number
}

export type AdminPaymentReconciliation = {
  dateFrom: string
  dateTo: string
  orderNetPaidAmount: string
  capturedPaymentAmount: string
  refundAuditAmount: string
  expectedNetAmount: string
  unreconciledAmount: string
  capturedPaymentCount: number
  refundAuditLogCount: number
  reconciled: boolean
}

export type AdminProductBreakdown = {
  productId: number
  ticketTypeId: number
  productName: string
  ticketName: string
  orderCount: number
  ticketCount: number
  soldTicketCount: number
  checkedInTicketCount: number
  refundedTicketCount: number
  netPaidAmount: string
}

export type AdminDailyTrend = {
  reportDate: string
  orderCount: number
  paidOrderCount: number
  completedOrderCount: number
  refundedOrderCount: number
  cancelledOrderCount: number
  netPaidAmount: string
  ticketCount: number
  soldTicketCount: number
  checkedInTicketCount: number
  refundedTicketCount: number
}

export type AdminHourlyTrend = {
  reportHour: string
  orderCount: number
  paidOrderCount: number
  completedOrderCount: number
  refundedOrderCount: number
  cancelledOrderCount: number
  netPaidAmount: string
  ticketCount: number
  soldTicketCount: number
  checkedInTicketCount: number
  refundedTicketCount: number
}

export type AdminMonthlyTrend = {
  reportMonth: string
  orderCount: number
  paidOrderCount: number
  completedOrderCount: number
  refundedOrderCount: number
  cancelledOrderCount: number
  netPaidAmount: string
  ticketCount: number
  soldTicketCount: number
  checkedInTicketCount: number
  refundedTicketCount: number
}
