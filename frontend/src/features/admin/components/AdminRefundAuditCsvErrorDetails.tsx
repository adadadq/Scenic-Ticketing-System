import { AdminExportErrorDetails } from './AdminExportErrorDetails'

export function AdminRefundAuditCsvErrorDetails({ error }: { error: unknown }) {
  return (
    <AdminExportErrorDetails
      error={error}
      fallback="退款审计 CSV 暂时无法导出，请稍后重试。"
    />
  )
}
