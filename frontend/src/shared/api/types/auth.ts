export type VisitorScope = 'TEMP' | 'REGISTERED' | (string & {})
export type AdminRole = 'SUPER_ADMIN' | 'OPERATOR' | (string & {})

export type VisitorMe = {
  visitorId: number
  visitorName: string
  phone: string
  visitorScope: VisitorScope
  isRegistered: boolean
}

export type AdminMe = {
  adminUserId: number
  username: string
  displayName: string
  role: AdminRole
}

export type VisitorLoginRequest = {
  username: string
  password: string
}

export type AdminLoginRequest = {
  username: string
  password: string
}

export type AdminProfileUpdateRequest = {
  username: string
  currentPassword: string
  newPassword?: string
}

export type VisitorRegisterRequest = {
  username: string
  password: string
  phone: string
}
