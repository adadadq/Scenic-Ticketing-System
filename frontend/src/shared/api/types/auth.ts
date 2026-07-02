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
  phone: string
}

export type AdminLoginRequest = {
  username: string
  password: string
}

export type VisitorRegisterRequest = {
  phone: string
  visitorName: string
  idType: 'ID_CARD'
  idNumber: string
}
