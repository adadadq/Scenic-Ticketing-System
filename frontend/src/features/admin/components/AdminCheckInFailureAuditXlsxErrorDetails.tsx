import { AdminExportErrorDetails } from './AdminExportErrorDetails'

export function AdminCheckInFailureAuditXlsxErrorDetails({ error }: { error: unknown }) {
  return (
    <AdminExportErrorDetails
      error={error}
      fallback="核验失败审计 XLSX 暂时无法导出，请稍后重试。"
      supportingText="请保留错误码和请求编号，便于后端定位管理员会话、筛选参数或表格导出服务问题。"
    />
  )
}
