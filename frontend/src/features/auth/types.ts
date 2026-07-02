import type { VisitorRegisterRequest } from '../../shared/api/types'

export type AuthMode = 'login' | 'register'

export type LoginFormValues = {
  phone: string
}

export type RegisterFormValues = VisitorRegisterRequest & {
  realNameConfirmed?: boolean
}
