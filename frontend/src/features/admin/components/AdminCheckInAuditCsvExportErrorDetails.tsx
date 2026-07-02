import { AdminExportErrorDetails } from './AdminExportErrorDetails'

export function AdminCheckInAuditCsvExportErrorDetails({ error }: { error: unknown }) {
  return (
    <AdminExportErrorDetails
      error={error}
      fallback="核验审计 CSV 暂时无法导出，请稍后重试。"
    />
  )
}
