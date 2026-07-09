import { Typography } from 'antd'
import type { AdminReportParams, AdminReportSummary } from '../../../shared/api/types'
import { amountLabel, defaultReportParams, metricLabel } from '../adminReportDisplay'

const { Text } = Typography

type AdminReportSummaryMetricsProps = {
  reportParams?: AdminReportParams
  summary?: AdminReportSummary
}

export function AdminReportSummaryMetrics({ reportParams, summary }: AdminReportSummaryMetricsProps) {
  const dateFrom = summary?.dateFrom ?? reportParams?.dateFrom ?? defaultReportParams.dateFrom
  const dateTo = summary?.dateTo ?? reportParams?.dateTo ?? defaultReportParams.dateTo

  return (
    <>
      <div className="admin-report-range">
        <Text type="secondary">统计周期</Text>
        <Text strong>{dateFrom} 至 {dateTo}</Text>
      </div>

      <div className="admin-metric-grid admin-report-metric-grid">
        <div className="admin-metric-tile">
          <Text type="secondary">订单总数</Text>
          <strong>{metricLabel(summary?.orderCount)}</strong>
          <span>已支付 {metricLabel(summary?.paidOrderCount)} 笔</span>
        </div>
        <div className="admin-metric-tile">
          <Text type="secondary">净收入</Text>
          <strong className="price">{amountLabel(summary?.netPaidAmount ?? '0.00')}</strong>
          <span>已完成 {metricLabel(summary?.completedOrderCount)} 笔</span>
        </div>
        <div className="admin-metric-tile">
          <Text type="secondary">票务流转</Text>
          <strong>{metricLabel(summary?.soldTicketCount)} / {metricLabel(summary?.ticketCount)}</strong>
          <span>已核验 {metricLabel(summary?.checkedInTicketCount)} 张</span>
        </div>
        <div className="admin-metric-tile">
          <Text type="secondary">退款与取消</Text>
          <strong>{metricLabel(summary?.refundedOrderCount)}</strong>
          <span className="is-warning">取消 {metricLabel(summary?.cancelledOrderCount)} 笔 · 退款 {metricLabel(summary?.refundedTicketCount)} 张</span>
        </div>
      </div>
    </>
  )
}
