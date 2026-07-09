import type { VisitorRegisterRequest } from '../../shared/api/types'

export type AuthMode = 'login' | 'register'

export type LoginFormValues = {
  username: string
  password: string
}

export type RegisterFormValues = VisitorRegisterRequest
