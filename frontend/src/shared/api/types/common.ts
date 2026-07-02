export type ApiSuccess<T> = {
  success: true
  data: T
  request_id: string
}

export type ApiFailure = {
  success: false
  code: string
  message: string
  request_id: string
}

export type ApiResponse<T> = ApiSuccess<T> | ApiFailure

export type LogoutPayload = {
  loggedOut: true
}

export type CsrfPayload = {
  headerName: string
}

export type HealthPayload = {
  status: 'ok'
  service: string
  environment: string
}

export type DatabaseHealthPayload = HealthPayload & {
  database: 'ok'
}
