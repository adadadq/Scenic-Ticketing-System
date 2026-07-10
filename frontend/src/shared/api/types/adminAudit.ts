export type AdminAuditLogType = '系统设置' | '票种管理' | '核验入园' | '核验失败' | '发起退款'

export type AdminAuditLog = {
  id: string
  createdAt: string
  operatorDisplayName: string
  operatorUsername: string
  type: AdminAuditLogType
  object: string
  result: '成功' | '警告'
  action: string
  requestId: string | null
  sourceIp: string | null
  deviceId: string | null
  adminSessionId: number | null
  userAgent: string | null
}

export type AdminAuditLogList = {
  items: AdminAuditLog[]
  total: number
  page: number
  pageSize: number
}
