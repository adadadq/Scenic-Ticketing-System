import { ApiError } from './errors'
import { parseApiResponse } from './response'
import type { ApiFailure, ApiSuccess, CsrfPayload } from './types'

export { ApiError, formatApiError } from './errors'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
const CSRF_COOKIE_NAME = import.meta.env.VITE_CSRF_COOKIE_NAME ?? 'scenic_csrf'
const DEFAULT_CSRF_HEADER = 'x-csrf-token'
const IDEMPOTENCY_HEADER = 'Idempotency-Key'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

type RequestOptions = {
  body?: unknown
  idempotencyKey?: string
  method?: HttpMethod
  skipCsrf?: boolean
}

type RawFileRequestOptions = {
  accept?: string
  expectedContentType?: string
}

let csrfHeaderName = DEFAULT_CSRF_HEADER
let csrfToken: string | null = null

function isMutatingMethod(method: HttpMethod) {
  return method !== 'GET'
}

function buildUrl(path: string) {
  return `${API_BASE_URL}${path}`
}

function readCookie(name: string) {
  if (typeof document === 'undefined') {
    return null
  }

  const prefix = `${encodeURIComponent(name)}=`
  const cookie = document.cookie
    .split('; ')
    .find((item) => item.startsWith(prefix))
    ?.slice(prefix.length)

  return cookie ? decodeURIComponent(cookie) : null
}

export async function getCsrfToken() {
  if (csrfToken) {
    return csrfToken
  }

  const response = await apiRequest<CsrfPayload>('/api/auth/csrf', {
    method: 'GET',
    skipCsrf: true,
  })
  csrfHeaderName = response.headerName || DEFAULT_CSRF_HEADER
  csrfToken = readCookie(CSRF_COOKIE_NAME)

  if (!csrfToken) {
    throw new ApiError({
      success: false,
      code: 'CSRF_TOKEN_MISSING',
      message: 'CSRF Cookie 缺失，请刷新页面后重试',
      request_id: '',
    })
  }

  return csrfToken
}

export function resetCsrfToken() {
  csrfHeaderName = DEFAULT_CSRF_HEADER
  csrfToken = null
}

export function createIdempotencyKey(prefix = 'frontend') {
  const random = crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`
  return `${prefix}:${random}`
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? 'GET'
  const headers = new Headers({ Accept: 'application/json' })

  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
  }

  if (options.idempotencyKey) {
    headers.set(IDEMPOTENCY_HEADER, options.idempotencyKey)
  }

  if (isMutatingMethod(method) && !options.skipCsrf) {
    const token = await getCsrfToken()
    headers.set(csrfHeaderName, token)
  }

  const response = await fetch(buildUrl(path), {
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    credentials: 'include',
    headers,
    method,
  })

  const payload = await parseApiResponse<T>(response)

  if (!response.ok || !payload.success) {
    throw new ApiError(payload as ApiFailure)
  }

  return (payload as ApiSuccess<T>).data
}

export async function rawFileRequest(path: string, options: RawFileRequestOptions = {}) {
  const response = await fetch(buildUrl(path), {
    credentials: 'include',
    headers: new Headers({ Accept: options.accept ?? '*/*' }),
    method: 'GET',
  })

  if (!response.ok) {
    const payload = await parseApiResponse<never>(response)
    throw new ApiError(payload as ApiFailure)
  }

  const responseContentType = response.headers.get('Content-Type')?.split(';')[0].trim().toLowerCase() ?? ''
  const expectedContentType = options.expectedContentType?.toLowerCase()

  if (expectedContentType && responseContentType !== expectedContentType) {
    throw new ApiError({
      success: false,
      code: 'FILE_CONTENT_TYPE_MISMATCH',
      message: `文件响应类型不匹配，期望 ${options.expectedContentType}，实际 ${responseContentType || 'unknown'}`,
      request_id: response.headers.get('x-request-id') ?? '',
    })
  }

  return response.blob()
}
