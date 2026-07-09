export type AdminSystemSettingLog = {
  createdAt: string
  operatorDisplayName: string
  operatorUsername: string
  action: string
  sourceIp?: string | null
}

export type AdminSystemSettings = {
  scenicName: string
  serviceTimeStart: string
  serviceTimeEnd: string
  ticketTimeStart: string
  ticketTimeEnd: string
  checkInTimeStart: string
  checkInTimeEnd: string
  perOrderLimit: number
  sessionTtlMinutes: number
  csrfEnabled: boolean
  loginGuardEnabled: boolean
  smsEnabled: boolean
  mailEnabled: boolean
  refundEnabled: boolean
  stockEnabled: boolean
  auditRetentionDays: number
  lastBackupLabel: string
  updatedAt?: string | null
  recentLogs: AdminSystemSettingLog[]
}

export type AdminSystemSettingsUpdateRequest = Partial<Omit<AdminSystemSettings, 'lastBackupLabel' | 'recentLogs' | 'updatedAt'>>
