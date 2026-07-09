import { AdminExportErrorDetails } from './AdminExportErrorDetails'

export function AdminCheckInAuditExportErrorDetails({ error }: { error: unknown }) {
  return (
    <AdminExportErrorDetails
      error={error}
      fallback="核验审计 XLSX 暂时无法导出，请稍后重试。"
    />
  )
}
