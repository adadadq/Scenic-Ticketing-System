import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminExportJobsApi } from '../../shared/api/endpoints'
import type {
  AdminExportJobCreateRequest,
  AdminExportJobFilters,
  AdminExportJobListParams,
} from '../../shared/api/types'
import {
  createMockAdminExportJob,
  downloadMockAdminExportJob,
  listMockAdminExportJobs,
} from './mockData'

export type AdminExportJobsMode = 'mock' | 'api'

export const adminExportJobsMode: AdminExportJobsMode =
  import.meta.env.VITE_ADMIN_EXPORT_JOBS_MODE === 'mock' ? 'mock' : 'api'

export const adminExportJobQueryKeys = {
  detail: (jobId: string, mode: AdminExportJobsMode = adminExportJobsMode) =>
    ['admin-export-jobs', mode, 'detail', jobId] as const,
  list: (params: AdminExportJobListParams = {}, mode: AdminExportJobsMode = adminExportJobsMode) =>
    ['admin-export-jobs', mode, 'list', normalizeAdminExportJobListParams(params)] as const,
}

function compactText(value?: string) {
  const trimmed = value?.trim()
  return trimmed || undefined
}

export function normalizeAdminExportJobFilters(filters: AdminExportJobFilters = {}): AdminExportJobFilters {
  return Object.entries(filters).reduce<AdminExportJobFilters>((normalized, [key, value]) => {
    if (typeof value === 'boolean') {
      if (value) {
        normalized[key] = true
      }
      return normalized
    }

    const text = compactText(value)
    if (text) {
      normalized[key] = text
    }

    return normalized
  }, {})
}

export function normalizeAdminExportJobCreateRequest(
  body: AdminExportJobCreateRequest,
): AdminExportJobCreateRequest {
  return {
    exportType: body.exportType,
    fileFormat: body.fileFormat,
    filters: normalizeAdminExportJobFilters(body.filters),
  }
}

export function normalizeAdminExportJobListParams(params: AdminExportJobListParams = {}): AdminExportJobListParams {
  return {
    ...(params.exportType ? { exportType: params.exportType } : {}),
    ...(params.fileFormat ? { fileFormat: params.fileFormat } : {}),
    ...(params.status ? { status: params.status } : {}),
    ...(params.page !== undefined ? { page: params.page } : {}),
    ...(params.pageSize !== undefined ? { pageSize: params.pageSize } : {}),
  }
}

export function useAdminExportJobsQuery(params: AdminExportJobListParams = {}) {
  const normalizedParams = normalizeAdminExportJobListParams(params)

  return useQuery({
    queryKey: adminExportJobQueryKeys.list(normalizedParams),
    retry: false,
    queryFn: () => {
      if (adminExportJobsMode === 'api') {
        return adminExportJobsApi.list(normalizedParams)
      }

      return listMockAdminExportJobs(normalizedParams)
    },
  })
}

export function useAdminExportJobCreateMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: AdminExportJobCreateRequest) => {
      const normalizedBody = normalizeAdminExportJobCreateRequest(body)

      if (adminExportJobsMode === 'api') {
        return adminExportJobsApi.create(normalizedBody)
      }

      return createMockAdminExportJob(normalizedBody)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['admin-export-jobs', adminExportJobsMode] })
      queryClient.setQueryData(adminExportJobQueryKeys.detail(result.jobId), result)
    },
  })
}

export async function downloadAdminExportJobFile(jobId: string, fileFormat: 'CSV' | 'XLSX') {
  if (adminExportJobsMode === 'api') {
    return adminExportJobsApi.download(jobId, fileFormat)
  }

  return downloadMockAdminExportJob(jobId)
}
