export type AdminExportType =
  | 'ORDER_DETAIL'
  | 'CHECK_IN_AUDIT'
  | 'CHECK_IN_FAILURE_AUDIT'
  | 'REFUND_AUDIT'
  | 'PAYMENT_RECONCILIATION'
  | 'PRODUCT_BREAKDOWN'
  | 'DAILY_TREND'
  | 'HOURLY_TREND'
  | 'MONTHLY_TREND'

export type AdminExportFileFormat = 'CSV' | 'XLSX'

export type AdminExportJobStatus = 'PENDING' | 'RUNNING' | 'SUCCEEDED' | 'FAILED'

export type AdminExportJobFilterValue = string | boolean

export type AdminExportJobFilters = Record<string, AdminExportJobFilterValue>

export type AdminExportJobCreateRequest = {
  exportType: AdminExportType
  fileFormat: AdminExportFileFormat
  filters: AdminExportJobFilters
}

export type AdminExportJobListParams = {
  exportType?: AdminExportType
  fileFormat?: AdminExportFileFormat
  status?: AdminExportJobStatus
  page?: number
  pageSize?: number
}

export type AdminExportJob = {
  jobId: string
  exportType: AdminExportType
  fileFormat: AdminExportFileFormat
  filters: AdminExportJobFilters
  status: AdminExportJobStatus
  requestId: string | null
  fileName?: string | null
  errorCode?: string | null
  errorMessage?: string | null
  requestedByUsername: string
  requestedByDisplayName: string
  requestedAt: string
  startedAt?: string | null
  finishedAt?: string | null
}

export type AdminExportJobList = {
  items: AdminExportJob[]
  total: number
  page: number
  pageSize: number
}
