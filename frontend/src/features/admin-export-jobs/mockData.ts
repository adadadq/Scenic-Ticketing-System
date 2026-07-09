import type {
  AdminExportJob,
  AdminExportJobCreateRequest,
  AdminExportJobList,
  AdminExportJobListParams,
} from '../../shared/api/types'

const mockAdminExportJobs: AdminExportJob[] = [
  {
    jobId: 'mock-export-job-order-csv-260701',
    exportType: 'ORDER_DETAIL',
    fileFormat: 'CSV',
    filters: { dateFrom: '2026-06-26', dateTo: '2026-06-28' },
    status: 'SUCCEEDED',
    requestId: 'mock-request-order-csv-260701',
    fileName: 'admin-orders-2026-06-26-2026-06-28.csv',
    requestedByUsername: 'admin',
    requestedByDisplayName: '演示管理员',
    requestedAt: '2026-07-01T09:10:00+08:00',
    startedAt: '2026-07-01T09:10:12+08:00',
    finishedAt: '2026-07-01T09:10:35+08:00',
  },
  {
    jobId: 'mock-export-job-check-in-xlsx-260701',
    exportType: 'CHECK_IN_AUDIT',
    fileFormat: 'XLSX',
    filters: { dateFrom: '2026-06-26', dateTo: '2026-06-28', operatorUsername: 'admin' },
    status: 'RUNNING',
    requestId: 'mock-request-check-in-xlsx-260701',
    fileName: null,
    requestedByUsername: 'admin',
    requestedByDisplayName: '演示管理员',
    requestedAt: '2026-07-01T09:18:00+08:00',
    startedAt: '2026-07-01T09:18:08+08:00',
    finishedAt: null,
  },
  {
    jobId: 'mock-export-job-failure-csv-260701',
    exportType: 'CHECK_IN_FAILURE_AUDIT',
    fileFormat: 'CSV',
    filters: { failureCode: 'TICKET_ALREADY_USED', dateFrom: '2026-06-26', dateTo: '2026-06-28' },
    status: 'FAILED',
    requestId: 'mock-request-failure-csv-260701',
    fileName: null,
    errorCode: 'ADMIN_EXPORT_JOB_UNSUPPORTED',
    errorMessage: '当前 worker 暂未支持该导出组合',
    requestedByUsername: 'admin',
    requestedByDisplayName: '演示管理员',
    requestedAt: '2026-07-01T09:05:00+08:00',
    startedAt: '2026-07-01T09:05:20+08:00',
    finishedAt: '2026-07-01T09:05:31+08:00',
  },
]

let createdMockExportJobCount = 0

function normalizePage(params: AdminExportJobListParams) {
  return {
    page: Math.max(params.page ?? 1, 1),
    pageSize: Math.max(params.pageSize ?? 5, 1),
  }
}

export async function listMockAdminExportJobs(params: AdminExportJobListParams = {}): Promise<AdminExportJobList> {
  const filtered = mockAdminExportJobs.filter((job) => {
    if (params.exportType && job.exportType !== params.exportType) {
      return false
    }

    if (params.fileFormat && job.fileFormat !== params.fileFormat) {
      return false
    }

    if (params.status && job.status !== params.status) {
      return false
    }

    return true
  })
  const { page, pageSize } = normalizePage(params)
  const start = (page - 1) * pageSize

  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length,
    page,
    pageSize,
  }
}

export async function createMockAdminExportJob(body: AdminExportJobCreateRequest): Promise<AdminExportJob> {
  createdMockExportJobCount += 1
  const job: AdminExportJob = {
    jobId: `mock-export-job-created-${String(createdMockExportJobCount).padStart(3, '0')}`,
    exportType: body.exportType,
    fileFormat: body.fileFormat,
    filters: body.filters,
    status: 'PENDING',
    requestId: `mock-request-created-${String(createdMockExportJobCount).padStart(3, '0')}`,
    fileName: null,
    requestedByUsername: 'admin',
    requestedByDisplayName: '演示管理员',
    requestedAt: new Date().toISOString(),
    startedAt: null,
    finishedAt: null,
  }

  mockAdminExportJobs.unshift(job)
  return job
}

export async function downloadMockAdminExportJob(jobId: string) {
  const job = mockAdminExportJobs.find((item) => item.jobId === jobId)

  if (!job || job.status !== 'SUCCEEDED') {
    throw new Error('导出任务尚未生成文件')
  }

  const content = `jobId,exportType,fileFormat,status\n${job.jobId},${job.exportType},${job.fileFormat},${job.status}\n`
  return new Blob([content], { type: job.fileFormat === 'CSV' ? 'text/csv' : 'application/octet-stream' })
}
