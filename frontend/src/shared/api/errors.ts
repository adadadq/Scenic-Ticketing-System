import type { ApiFailure } from './types'

export class ApiError extends Error {
  code: string
  requestId: string

  constructor(error: ApiFailure) {
    super(error.message)
    this.name = 'ApiError'
    this.code = error.code
    this.requestId = error.request_id
  }
}

export function formatApiError(error: unknown, fallback = '操作失败，请稍后重试。') {
  if (error instanceof ApiError) {
    return error.requestId ? `${error.message}（请求编号：${error.requestId}）` : error.message
  }

  return fallback
}
