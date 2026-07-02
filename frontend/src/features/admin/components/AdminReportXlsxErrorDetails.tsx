import { AdminExportErrorDetails } from './AdminExportErrorDetails'

type AdminReportXlsxErrorDetailsProps = {
  error: unknown
  fallback?: string
}

export function AdminReportXlsxErrorDetails({
  error,
  fallback = '后台订单 XLSX 暂时无法导出，请稍后重试。',
}: AdminReportXlsxErrorDetailsProps) {
  return (
    <AdminExportErrorDetails
      error={error}
      fallback={fallback}
      supportingText="请保留错误码和请求编号，便于后端定位导出服务问题。"
    />
  )
}
