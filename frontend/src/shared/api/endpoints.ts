import { apiRequest, rawFileRequest } from './client'
import {
  buildAdminCheckInAuditLogExportSearch,
  buildAdminCheckInFailureAuditLogExportSearch,
  buildAdminCheckInFailureAuditLogSearch,
  buildAdminExportJobListSearch,
  buildAdminOrderListSearch,
  buildAdminRefundAuditLogExportSearch,
  buildAdminRefundAuditLogSearch,
  buildAdminReportSearch,
  buildAdminTrendReportSearch,
  compactText,
} from './searchBuilders'
import type {
  AdminLoginRequest,
  AdminMe,
  AdminProfileUpdateRequest,
  AdminBatchCheckIn,
  AdminBatchCheckInRequest,
  AdminBatchUndoCheckIn,
  AdminBatchUndoCheckInRequest,
  AdminAuditLogList,
  AdminCheckIn,
  AdminCheckInAuditLogExportParams,
  AdminCheckInFailureAuditLogExportParams,
  AdminCheckInFailureAuditLogList,
  AdminCheckInFailureAuditLogParams,
  AdminCheckInRequest,
  AdminHourlyTrend,
  AdminOrderDetail,
  AdminOrderList,
  AdminOrderListParams,
  AdminMonthlyTrend,
  AdminPartialRefund,
  AdminPartialRefundRequest,
  AdminPaymentReconciliation,
  AdminDailyTrend,
  AdminExportJob,
  AdminExportJobCreateRequest,
  AdminExportJobList,
  AdminExportJobListParams,
  AdminProductBreakdown,
  AdminReportParams,
  AdminReportSummary,
  AdminSystemSettings,
  AdminSystemSettingsUpdateRequest,
  AdminTicket,
  AdminTicketSaveRequest,
  Announcement,
  AnnouncementPublishRequest,
  AdminTrendReportParams,
  AdminRefund,
  AdminRefundAuditLog,
  AdminRefundAuditLogExportParams,
  AdminRefundAuditLogList,
  AdminRefundAuditLogParams,
  AdminRefundRequest,
  DatabaseHealthPayload,
  HealthPayload,
  LogoutPayload,
  MyOrderDetail,
  OrderCreateRequest,
  OrderSummary,
  OrderStatusFilter,
  PassengerTemplate,
  PassengerTemplateRequest,
  ProductPublic,
  TimeSlotPublic,
  VisitorLoginRequest,
  VisitorMe,
  VisitorRegisterRequest,
} from './types'

export const healthApi = {
  database: () => apiRequest<DatabaseHealthPayload>('/api/health/db'),
  process: () => apiRequest<HealthPayload>('/api/health'),
}

export const authApi = {
  me: () => apiRequest<VisitorMe>('/api/auth/me'),
  visitorLogin: (body: VisitorLoginRequest) =>
    apiRequest<VisitorMe>('/api/auth/visitor/login', { body, method: 'POST' }),
  visitorRegister: (body: VisitorRegisterRequest) =>
    apiRequest<VisitorMe>('/api/auth/visitor/register', { body, method: 'POST' }),
  logout: () => apiRequest<LogoutPayload>('/api/auth/logout', { method: 'POST' }),
}

export const adminAuthApi = {
  login: (body: AdminLoginRequest) =>
    apiRequest<AdminMe>('/api/admin/auth/login', { body, method: 'POST' }),
  me: () => apiRequest<AdminMe>('/api/admin/auth/me'),
  updateProfile: (body: AdminProfileUpdateRequest) =>
    apiRequest<AdminMe>('/api/admin/auth/profile', { body, method: 'PATCH' }),
  logout: () => apiRequest<LogoutPayload>('/api/admin/auth/logout', { method: 'POST' }),
}

export const adminSettingsApi = {
  get: () => apiRequest<AdminSystemSettings>('/api/admin/settings'),
  update: (body: AdminSystemSettingsUpdateRequest) =>
    apiRequest<AdminSystemSettings>('/api/admin/settings', { body, method: 'PATCH' }),
}

export const adminTicketsApi = {
  list: () => apiRequest<AdminTicket[]>('/api/admin/tickets'),
  create: (body: AdminTicketSaveRequest) =>
    apiRequest<AdminTicket>('/api/admin/tickets', { body, method: 'POST' }),
  update: (ticketId: number, body: AdminTicketSaveRequest) =>
    apiRequest<AdminTicket>(`/api/admin/tickets/${ticketId}`, { body, method: 'PATCH' }),
  delete: (ticketId: number) =>
    apiRequest<{ deleted: boolean }>(`/api/admin/tickets/${ticketId}`, { method: 'DELETE' }),
}

export const adminAuditLogsApi = {
  list: () => apiRequest<AdminAuditLogList>('/api/admin/audit-logs'),
}

export const announcementsApi = {
  current: () => apiRequest<Announcement>('/api/announcements/current'),
  publish: (body: AnnouncementPublishRequest) =>
    apiRequest<Announcement>('/api/admin/announcements/current', {
      body: {
        title: compactText(body.title),
        content: compactText(body.content),
      },
      method: 'POST',
    }),
}

export const adminExportJobsApi = {
  create: (body: AdminExportJobCreateRequest) =>
    apiRequest<AdminExportJob>('/api/admin/export-jobs', {
      body: {
        exportType: body.exportType,
        fileFormat: body.fileFormat,
        filters: body.filters,
      },
      method: 'POST',
    }),
  detail: (jobId: string) =>
    apiRequest<AdminExportJob>(`/api/admin/export-jobs/${encodeURIComponent(jobId)}`),
  download: (jobId: string, fileFormat: 'CSV' | 'XLSX') =>
    rawFileRequest(`/api/admin/export-jobs/${encodeURIComponent(jobId)}/download`, {
      accept: fileFormat === 'XLSX'
        ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        : 'text/csv',
      expectedContentType: fileFormat === 'XLSX'
        ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        : 'text/csv',
    }),
  list: (params?: AdminExportJobListParams) =>
    apiRequest<AdminExportJobList>(`/api/admin/export-jobs${buildAdminExportJobListSearch(params)}`),
}

export const adminOrdersApi = {
  list: (params?: AdminOrderListParams) =>
    apiRequest<AdminOrderList>(`/api/admin/orders${buildAdminOrderListSearch(params)}`),
  detail: (orderNo: string) =>
    apiRequest<AdminOrderDetail>(`/api/admin/orders/${encodeURIComponent(orderNo)}`),
  refundLogs: (orderNo: string) =>
    apiRequest<AdminRefundAuditLog[]>(`/api/admin/orders/${encodeURIComponent(orderNo)}/refund-logs`),
  refund: (orderNo: string, body: AdminRefundRequest = {}) =>
    apiRequest<AdminRefund>(`/api/admin/orders/${encodeURIComponent(orderNo)}/refund`, {
      body: { reason: compactText(body.reason) },
      method: 'POST',
    }),
  partialRefund: (orderNo: string, body: AdminPartialRefundRequest) =>
    apiRequest<AdminPartialRefund>(`/api/admin/orders/${encodeURIComponent(orderNo)}/refund/items`, {
      body: {
        itemNos: body.itemNos.map((itemNo) => itemNo.trim()),
        reason: compactText(body.reason),
      },
      method: 'POST',
    }),
}

export const adminRefundAuditLogsApi = {
  list: (params?: AdminRefundAuditLogParams) =>
    apiRequest<AdminRefundAuditLogList>(`/api/admin/refund-logs${buildAdminRefundAuditLogSearch(params)}`),
}

export const adminRefundAuditLogExportsApi = {
  csv: (params?: AdminRefundAuditLogExportParams) =>
    rawFileRequest(`/api/admin/refund-logs.csv${buildAdminRefundAuditLogExportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  xlsx: (params?: AdminRefundAuditLogExportParams) =>
    rawFileRequest(`/api/admin/refund-logs.xlsx${buildAdminRefundAuditLogExportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
}

export const adminCheckInsApi = {
  batch: (body: AdminBatchCheckInRequest) =>
    apiRequest<AdminBatchCheckIn>('/api/admin/check-ins/batch', {
      body: { ticketCodes: body.ticketCodes.map((ticketCode) => ticketCode.trim()) },
      method: 'POST',
    }),
  batchUndo: (body: AdminBatchUndoCheckInRequest) =>
    apiRequest<AdminBatchUndoCheckIn>('/api/admin/check-ins/batch/undo', {
      body: {
        ticketCodes: body.ticketCodes.map((ticketCode) => ticketCode.trim()),
        reason: compactText(body.reason),
      },
      method: 'POST',
    }),
  create: (body: AdminCheckInRequest) =>
    apiRequest<AdminCheckIn>('/api/admin/check-ins', {
      body: { ticketCode: body.ticketCode.trim() },
      method: 'POST',
    }),
}

export const adminCheckInAuditLogExportsApi = {
  csv: (params?: AdminCheckInAuditLogExportParams) =>
    rawFileRequest(`/api/admin/check-in-logs.csv${buildAdminCheckInAuditLogExportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  xlsx: (params?: AdminCheckInAuditLogExportParams) =>
    rawFileRequest(`/api/admin/check-in-logs.xlsx${buildAdminCheckInAuditLogExportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
}

export const adminCheckInFailureAuditLogsApi = {
  list: (params?: AdminCheckInFailureAuditLogParams) =>
    apiRequest<AdminCheckInFailureAuditLogList>(
      `/api/admin/check-in-failure-logs${buildAdminCheckInFailureAuditLogSearch(params)}`,
    ),
}

export const adminCheckInFailureAuditLogExportsApi = {
  csv: (params?: AdminCheckInFailureAuditLogExportParams) =>
    rawFileRequest(`/api/admin/check-in-failure-logs.csv${buildAdminCheckInFailureAuditLogExportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  xlsx: (params?: AdminCheckInFailureAuditLogExportParams) =>
    rawFileRequest(`/api/admin/check-in-failure-logs.xlsx${buildAdminCheckInFailureAuditLogExportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
}

export const adminReportsApi = {
  dailyTrend: (params?: AdminTrendReportParams) =>
    apiRequest<AdminDailyTrend[]>(`/api/admin/reports/daily-trend${buildAdminTrendReportSearch(params)}`),
  hourlyTrend: (params?: AdminTrendReportParams) =>
    apiRequest<AdminHourlyTrend[]>(`/api/admin/reports/hourly-trend${buildAdminTrendReportSearch(params)}`),
  monthlyTrend: (params?: AdminTrendReportParams) =>
    apiRequest<AdminMonthlyTrend[]>(`/api/admin/reports/monthly-trend${buildAdminTrendReportSearch(params)}`),
  paymentReconciliation: (params?: AdminReportParams) =>
    apiRequest<AdminPaymentReconciliation>(`/api/admin/reports/payment-reconciliation${buildAdminReportSearch(params)}`),
  productBreakdown: (params?: AdminReportParams) =>
    apiRequest<AdminProductBreakdown[]>(`/api/admin/reports/product-breakdown${buildAdminReportSearch(params)}`),
  summary: (params?: AdminReportParams) =>
    apiRequest<AdminReportSummary>(`/api/admin/reports/summary${buildAdminReportSearch(params)}`),
}

export const adminReportExportsApi = {
  dailyTrendCsv: (params?: AdminTrendReportParams) =>
    rawFileRequest(`/api/admin/reports/daily-trend.csv${buildAdminTrendReportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  dailyTrendXlsx: (params?: AdminTrendReportParams) =>
    rawFileRequest(`/api/admin/reports/daily-trend.xlsx${buildAdminTrendReportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  hourlyTrendCsv: (params?: AdminTrendReportParams) =>
    rawFileRequest(`/api/admin/reports/hourly-trend.csv${buildAdminTrendReportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  hourlyTrendXlsx: (params?: AdminTrendReportParams) =>
    rawFileRequest(`/api/admin/reports/hourly-trend.xlsx${buildAdminTrendReportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  monthlyTrendCsv: (params?: AdminTrendReportParams) =>
    rawFileRequest(`/api/admin/reports/monthly-trend.csv${buildAdminTrendReportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  monthlyTrendXlsx: (params?: AdminTrendReportParams) =>
    rawFileRequest(`/api/admin/reports/monthly-trend.xlsx${buildAdminTrendReportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  ordersCsv: (params?: AdminReportParams) =>
    rawFileRequest(`/api/admin/reports/orders.csv${buildAdminReportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  paymentReconciliationCsv: (params?: AdminReportParams) =>
    rawFileRequest(`/api/admin/reports/payment-reconciliation.csv${buildAdminReportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  productBreakdownCsv: (params?: AdminReportParams) =>
    rawFileRequest(`/api/admin/reports/product-breakdown.csv${buildAdminReportSearch(params)}`, {
      accept: 'text/csv',
      expectedContentType: 'text/csv',
    }),
  productBreakdownXlsx: (params?: AdminReportParams) =>
    rawFileRequest(`/api/admin/reports/product-breakdown.xlsx${buildAdminReportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  paymentReconciliationXlsx: (params?: AdminReportParams) =>
    rawFileRequest(`/api/admin/reports/payment-reconciliation.xlsx${buildAdminReportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
  ordersXlsx: (params?: AdminReportParams) =>
    rawFileRequest(`/api/admin/reports/orders.xlsx${buildAdminReportSearch(params)}`, {
      accept: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      expectedContentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }),
}

export const catalogApi = {
  products: () => apiRequest<ProductPublic[]>('/api/catalog/products'),
  timeSlots: (params: { productId?: number; ticketTypeId?: number; visitDate: string }) => {
    const search = new URLSearchParams({ visitDate: params.visitDate })

    if (params.ticketTypeId) {
      search.set('ticketTypeId', String(params.ticketTypeId))
    }

    if (params.productId) {
      search.set('productId', String(params.productId))
    }

    return apiRequest<TimeSlotPublic[]>(`/api/catalog/time-slots?${search.toString()}`)
  },
}

export const ordersApi = {
  create: (body: OrderCreateRequest) =>
    apiRequest<OrderSummary>('/api/orders', { body, method: 'POST' }),
  mine: (status?: OrderStatusFilter) => {
    const search = status ? `?${new URLSearchParams({ status }).toString()}` : ''
    return apiRequest<OrderSummary[]>(`/api/me/orders${search}`)
  },
  detail: (orderNo: string) => apiRequest<MyOrderDetail>(`/api/me/orders/${encodeURIComponent(orderNo)}`),
  pay: (orderNo: string, idempotencyKey: string) =>
    apiRequest<MyOrderDetail>(`/api/orders/${encodeURIComponent(orderNo)}/pay`, {
      idempotencyKey,
      method: 'POST',
    }),
  cancel: (orderNo: string) =>
    apiRequest<MyOrderDetail>(`/api/orders/${encodeURIComponent(orderNo)}/cancel`, { method: 'POST' }),
}

export const passengerTemplatesApi = {
  list: () => apiRequest<PassengerTemplate[]>('/api/me/passenger-templates'),
  create: (body: PassengerTemplateRequest) =>
    apiRequest<PassengerTemplate>('/api/me/passenger-templates', { body, method: 'POST' }),
  update: (templateId: number, body: PassengerTemplateRequest) =>
    apiRequest<PassengerTemplate>(`/api/me/passenger-templates/${templateId}`, { body, method: 'PATCH' }),
  delete: (templateId: number) =>
    apiRequest<{ deleted: boolean }>(`/api/me/passenger-templates/${templateId}`, { method: 'DELETE' }),
}
