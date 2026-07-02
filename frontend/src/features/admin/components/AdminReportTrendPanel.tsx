import { Flex, Progress, Typography } from 'antd'
import { amountLabel, type AdminTrendMetricRow, maxTrendAmount, trendPeriodLabel } from '../adminReportDisplay'

const { Text, Title } = Typography

type AdminReportTrendPanelProps = {
  emptyText?: string
  isLoading: boolean
  subtitle: string
  title: string
  trendRows: AdminTrendMetricRow[]
}

export function AdminReportTrendPanel({
  emptyText = '当前日期范围暂无报表数据。',
  isLoading,
  subtitle,
  title,
  trendRows,
}: AdminReportTrendPanelProps) {
  const maxAmount = maxTrendAmount(trendRows)

  return (
    <div className="admin-report-panel admin-trend-panel">
      <Flex align="center" justify="space-between" wrap>
        <Title level={3}>{title}</Title>
        <Text type="secondary">{subtitle}</Text>
      </Flex>
      <div className="admin-trend-list">
        {trendRows.map((row) => (
          <div className="admin-trend-row" key={trendPeriodLabel(row)}>
            <div>
              <Text strong>{trendPeriodLabel(row)}</Text>
              <Text type="secondary">{row.orderCount} 单 · {row.soldTicketCount} 张票</Text>
            </div>
            <div className="admin-trend-bar">
              <Progress
                percent={Math.round((Number(row.netPaidAmount) / maxAmount) * 100)}
                showInfo={false}
                size="small"
                strokeColor="#008b84"
              />
              <Text strong>{amountLabel(row.netPaidAmount)}</Text>
            </div>
          </div>
        ))}
        {!isLoading && trendRows.length === 0 ? (
          <Text type="secondary">{emptyText}</Text>
        ) : null}
      </div>
    </div>
  )
}
