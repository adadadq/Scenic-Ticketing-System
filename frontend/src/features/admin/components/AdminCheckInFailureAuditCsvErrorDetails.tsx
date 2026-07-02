import { AdminExportErrorDetails } from './AdminExportErrorDetails'

export function AdminCheckInFailureAuditCsvErrorDetails({ error }: { error: unknown }) {
  return (
    <AdminExportErrorDetails
      error={error}
      fallback="核验失败审计 CSV 暂时无法导出，请稍后重试。"
    />
  )
}
