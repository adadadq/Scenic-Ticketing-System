import type { ApiFailure, ApiResponse, ApiSuccess } from './types'

const REQUEST_ID_HEADER = 'X-Request-Id'

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function invalidResponse(response: Response): ApiFailure {
  return {
    success: false,
    code: 'INVALID_RESPONSE',
    message: '服务响应格式异常',
    request_id: response.headers.get(REQUEST_ID_HEADER) ?? '',
  }
}

export async function parseApiResponse<T>(response: Response): Promise<ApiResponse<T>> {
  const payload = (await response.json().catch(() => null)) as unknown

  if (!isRecord(payload) || typeof payload.success !== 'boolean') {
    return invalidResponse(response)
  }

  if (payload.success === true && 'data' in payload && typeof payload.request_id === 'string') {
    return payload as ApiSuccess<T>
  }

  if (
    payload.success === false &&
    typeof payload.code === 'string' &&
    typeof payload.message === 'string' &&
    typeof payload.request_id === 'string'
  ) {
    return payload as ApiFailure
  }

  return invalidResponse(response)
}
