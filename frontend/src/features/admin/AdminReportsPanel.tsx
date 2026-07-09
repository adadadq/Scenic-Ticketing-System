import { useState } from 'react'
import { Alert, Button, Dropdown, Input, Select, Typography } from 'antd'
import type { MenuProps } from 'antd'
import {
  BarChartOutlined,
  CalendarOutlined,
  CheckCircleFilled,
  ClockCircleOutlined,
  DollarOutlined,
  DownOutlined,
  DownloadOutlined,
  ExclamationCircleFilled,
  FileTextOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  SunOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import type { AdminDailyTrend, AdminPaymentReconciliation, AdminProductBreakdown, AdminReportSummary } from '../../shared/api/types'
import { scenicTicketName } from '../../shared/display/scenicText'
import {
  useAdminDailyTrendQuery,
  useAdminPaymentReconciliationQuery,
  useAdminProductBreakdownQuery,
  useAdminReportSummaryQuery,
} from '../admin-reports/queries'
import { useAdminReportExports } from '../admin-reports/useAdminReportExports'
import { defaultReportParams } from './adminReportDisplay'
import { AdminNoticeButton } from './components/AdminNoticeButton'

const { Text, Title } = Typography

const sampleTrendRows: AdminDailyTrend[] = [
  { reportDate: '00:00', netPaidAmount: '9500.00', orderCount: 78, paidOrderCount: 72, completedOrderCount: 60, refundedOrderCount: 1, cancelledOrderCount: 2, ticketCount: 150, soldTicketCount: 142, checkedInTicketCount: 40, refundedTicketCount: 1 },
  { reportDate: '04:00', netPaidAmount: '18000.00', orderCount: 105, paidOrderCount: 99, completedOrderCount: 80, refundedOrderCount: 2, cancelledOrderCount: 3, ticketCount: 210, soldTicketCount: 198, checkedInTicketCount: 80, refundedTicketCount: 2 },
  { reportDate: '08:00', netPaidAmount: '30000.00', orderCount: 165, paidOrderCount: 156, completedOrderCount: 120, refundedOrderCount: 3, cancelledOrderCount: 4, ticketCount: 330, soldTicketCount: 312, checkedInTicketCount: 160, refundedTicketCount: 4 },
  { reportDate: '12:00', netPaidAmount: '35500.00', orderCount: 190, paidOrderCount: 181, completedOrderCount: 150, refundedOrderCount: 3, cancelledOrderCount: 4, ticketCount: 380, soldTicketCount: 362, checkedInTicketCount: 220, refundedTicketCount: 4 },
  { reportDate: '16:00', netPaidAmount: '40500.00', orderCount: 210, paidOrderCount: 202, completedOrderCount: 170, refundedOrderCount: 4, cancelledOrderCount: 5, ticketCount: 420, soldTicketCount: 404, checkedInTicketCount: 260, refundedTicketCount: 5 },
  { reportDate: '20:00', netPaidAmount: '32800.00', orderCount: 168, paidOrderCount: 160, completedOrderCount: 132, refundedOrderCount: 3, cancelledOrderCount: 4, ticketCount: 336, soldTicketCount: 320, checkedInTicketCount: 240, refundedTicketCount: 4 },
]

const sampleProductRows: AdminProductBreakdown[] = [
  { productId: 1, ticketTypeId: 1, productName: '遇龙河成人票', ticketName: '遇龙河成人票', orderCount: 256, ticketCount: 512, soldTicketCount: 512, checkedInTicketCount: 426, refundedTicketCount: 4, netPaidAmount: '32568.00' },
  { productId: 2, ticketTypeId: 2, productName: '竹筏漂流票', ticketName: '竹筏漂流票', orderCount: 136, ticketCount: 268, soldTicketCount: 268, checkedInTicketCount: 210, refundedTicketCount: 2, netPaidAmount: '17152.00' },
  { productId: 3, ticketTypeId: 3, productName: '遇龙河儿童票', ticketName: '遇龙河儿童票', orderCount: 98, ticketCount: 186, soldTicketCount: 186, checkedInTicketCount: 148, refundedTicketCount: 1, netPaidAmount: '12648.00' },
  { productId: 4, ticketTypeId: 4, productName: '遇龙河优惠票', ticketName: '遇龙河优惠票', orderCount: 72, ticketCount: 138, soldTicketCount: 138, checkedInTicketCount: 96, refundedTicketCount: 1, netPaidAmount: '13524.00' },
  { productId: 5, ticketTypeId: 5, productName: '遇龙河团队票', ticketName: '遇龙河团队票', orderCount: 51, ticketCount: 96, soldTicketCount: 96, checkedInTicketCount: 70, refundedTicketCount: 1, netPaidAmount: '18816.00' },
]

function money(value?: string) {
  return Number(value ?? 0).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function numberText(value?: number) {
  return (value ?? 0).toLocaleString('zh-CN')
}

function buildMetricCards(summary?: AdminReportSummary) {
  const pending = summary ? Math.max(summary.soldTicketCount - summary.checkedInTicketCount, 0) : 86
  return [
    { icon: <DollarOutlined />, label: '今日收入', value: money(summary?.netPaidAmount ?? '32568.00'), delta: '+12.35% ↗', tone: 'orange' },
    { icon: <FileTextOutlined />, label: '今日订单', value: numberText(summary?.orderCount ?? 256), delta: '+18.75% ↗', tone: 'blue' },
    { icon: <BarChartOutlined />, label: '今日售票', value: numberText(summary?.soldTicketCount ?? 512), delta: '+15.62% ↗', tone: 'green' },
    { icon: <TeamOutlined />, label: '待核验', value: numberText(pending), delta: '-8.46% ↓', tone: 'purple' },
  ]
}

function RevenueChart({ rows }: { rows: AdminDailyTrend[] }) {
  const chartRows = rows.length > 1 ? rows : sampleTrendRows
  const maxAmount = Math.max(...chartRows.map((row) => Number(row.netPaidAmount)), 1)
  const points = chartRows.slice(0, 12).map((row, index, list) => {
    const x = 42 + (list.length === 1 ? 0 : index * (478 / (list.length - 1)))
    const y = 178 - (Number(row.netPaidAmount) / maxAmount) * 128
    return [x, y] as const
  })
  const line = points.map(([x, y], index) => `${index ? 'L' : 'M'}${x} ${y}`).join(' ')
  const area = `${line} L520 178 L42 178 Z`
  const last = chartRows[Math.min(chartRows.length - 1, 4)]

  return (
    <svg className="admin-report-line-chart" viewBox="0 0 560 220" role="img" aria-label="收入趋势">
      {[26, 62, 98, 134, 170].map((y) => <line key={y} x1="42" x2="536" y1={y} y2={y} />)}
      {['50k', '40k', '30k', '20k', '10k', '0'].map((label, index) => (
        <text key={label} x="4" y={30 + index * 34}>{label}</text>
      ))}
      {['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'].map((label, index) => (
        <text key={label} textAnchor="middle" x={42 + index * 82} y="210">{label}</text>
      ))}
      <path d={area} className="chart-area" />
      <path d={line} className="chart-line" />
      {points.map(([x, y]) => <circle key={`${x}-${y}`} cx={x} cy={y} r="4" />)}
      <line className="chart-guide" x1="438" x2="438" y1="26" y2="178" />
      <foreignObject x="454" y="50" width="112" height="58">
        <div className="admin-report-chart-tip">收入<br />￥{money(last?.netPaidAmount)}</div>
      </foreignObject>
    </svg>
  )
}

function SalesChart({ rows }: { rows: AdminProductBreakdown[] }) {
  const chartRows = (rows.length ? rows : sampleProductRows)
    .slice()
    .sort((a, b) => b.soldTicketCount - a.soldTicketCount)
    .slice(0, 4)
  const maxSold = Math.max(...chartRows.map((row) => row.soldTicketCount), 1)

  return (
    <div className="admin-report-bar-chart" role="img" aria-label="票种销量">
      <div className="admin-report-bar-axis">
        {[500, 400, 300, 200, 100, 0].map((tick) => <span key={tick}>{tick}</span>)}
      </div>
      <div className="admin-report-bar-items">
        {chartRows.map((row, index) => (
          <div className="admin-report-bar-item" key={`${row.productId}-${row.ticketTypeId}`}>
            <em>{row.soldTicketCount}</em>
            <i style={{ height: `${Math.max(32, (row.soldTicketCount / maxSold) * 156)}px`, background: ['#008f89', '#38bbb9', '#49bdc0', '#53bdc3'][index] }} />
            <strong>{scenicTicketName(row.ticketName)}</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

function paymentRows(reconciliation?: AdminPaymentReconciliation) {
  return [
    ['应收金额', `￥${money(reconciliation?.expectedNetAmount ?? '32568.00')}`, <DollarOutlined key="receivable" />, 'orange'],
    ['已收金额', `￥${money(reconciliation?.capturedPaymentAmount ?? '32148.00')}`, <CheckCircleFilled key="captured" />, 'green'],
    ['未收金额', `￥${money(reconciliation?.unreconciledAmount ?? '420.00')}`, <ExclamationCircleFilled key="pending" />, 'red'],
    ['对账状态', reconciliation?.reconciled === false ? '存在差异' : '对账平衡', <ClockCircleOutlined key="status" />, 'cyan'],
  ] as const
}

export function AdminReportsPanel({ onOpenProfile }: { onOpenProfile: () => void }) {
  const [dateFrom, setDateFrom] = useState(defaultReportParams.dateFrom ?? '2026-06-28')
  const [dateTo, setDateTo] = useState(defaultReportParams.dateTo ?? '2026-06-28')
  const reportParams = {
    ...(dateFrom ? { dateFrom } : {}),
    ...(dateTo ? { dateTo } : {}),
  }
  const reportExports = useAdminReportExports({ reportParams, trendReportParams: reportParams })
  const summaryQuery = useAdminReportSummaryQuery(reportParams)
  const reconciliationQuery = useAdminPaymentReconciliationQuery(reportParams)
  const productBreakdownQuery = useAdminProductBreakdownQuery(reportParams)
  const dailyTrendQuery = useAdminDailyTrendQuery(reportParams)
  const activeError = summaryQuery.error ?? reconciliationQuery.error ?? productBreakdownQuery.error ?? dailyTrendQuery.error
  const exportError = Object.values(reportExports.errors).find(Boolean)
  const summary = summaryQuery.data
  const reconciliation = reconciliationQuery.data
  const productRows = productBreakdownQuery.data ?? []
  const trendRows = dailyTrendQuery.data ?? []
  const metricCards = buildMetricCards(summary)
  const topRows = (productRows.length ? productRows : sampleProductRows)
    .slice()
    .sort((a, b) => b.soldTicketCount - a.soldTicketCount)
    .slice(0, 5)
  const tableRows = (trendRows.length ? trendRows : sampleTrendRows).slice(-5).reverse()
  const isFetching = summaryQuery.isFetching ||
    reconciliationQuery.isFetching ||
    productBreakdownQuery.isFetching ||
    dailyTrendQuery.isFetching
  const csvLoading = reportExports.loading.ordersCsv ||
    reportExports.loading.paymentReconciliationCsv ||
    reportExports.loading.productBreakdownCsv ||
    reportExports.loading.trendCsv !== null
  const xlsxLoading = reportExports.loading.ordersXlsx ||
    reportExports.loading.paymentReconciliationXlsx ||
    reportExports.loading.productBreakdownXlsx ||
    reportExports.loading.trendXlsx !== null
  const csvMenuItems: MenuProps['items'] = [
    { key: 'orders', label: '订单明细 CSV' },
    { key: 'daily-trend', label: '每日趋势 CSV' },
    { key: 'product', label: '票种销量 CSV' },
    { key: 'payment', label: '支付对账 CSV' },
  ]
  const xlsxMenuItems: MenuProps['items'] = [
    { key: 'orders', label: '订单明细 XLSX' },
    { key: 'daily-trend', label: '每日趋势 XLSX' },
    { key: 'product', label: '票种销量 XLSX' },
    { key: 'payment', label: '支付对账 XLSX' },
  ]

  function refetchReports() {
    void summaryQuery.refetch()
    void reconciliationQuery.refetch()
    void productBreakdownQuery.refetch()
    void dailyTrendQuery.refetch()
  }

  function exportCsv(key: string) {
    if (key === 'orders') void reportExports.actions.exportOrdersCsv()
    if (key === 'daily-trend') void reportExports.actions.exportTrendCsv('daily')
    if (key === 'product') void reportExports.actions.exportProductBreakdownCsv()
    if (key === 'payment') void reportExports.actions.exportPaymentReconciliationCsv()
  }

  function exportXlsx(key: string) {
    if (key === 'orders') void reportExports.actions.exportOrdersXlsx()
    if (key === 'daily-trend') void reportExports.actions.exportTrendXlsx('daily')
    if (key === 'product') void reportExports.actions.exportProductBreakdownXlsx()
    if (key === 'payment') void reportExports.actions.exportPaymentReconciliationXlsx()
  }

  return (
    <section className="admin-report-page" aria-label="报表管理">
      <div className="admin-report-hero">
        <div className="admin-report-hero-copy">
          <Title level={1}>报表管理</Title>
          <Text>多维度数据分析，助力运营决策与业务增长。</Text>
        </div>
        <div className="admin-dashboard-top-actions">
          <div className="admin-weather-card">
            <SunOutlined />
            <span>晴 26°C</span>
            <Text>2026-06-28 16:04</Text>
          </div>
          <AdminNoticeButton />
          <button className="admin-profile-button" type="button" onClick={onOpenProfile}>
            <span className="admin-profile-avatar" />
            <strong>演示管理员</strong>
            <DownOutlined />
          </button>
        </div>
      </div>

      <div className="admin-report-body">
        <div className="admin-report-toolbar">
          <div className="admin-report-date-range">
            <Input aria-label="开始日期" prefix={<CalendarOutlined />} type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            <span>~</span>
            <Input aria-label="结束日期" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </div>
          <Select
            aria-label="渠道筛选"
            className="admin-report-channel-select"
            defaultValue="全部渠道"
            options={[{ value: '全部渠道' }, { value: '线上购票' }, { value: '窗口购票' }]}
          />
          <div className="admin-report-toolbar-actions">
            <Button icon={<ReloadOutlined />} loading={isFetching} onClick={refetchReports}>刷新</Button>
            <Dropdown trigger={['click']} menu={{ items: csvMenuItems, onClick: ({ key }) => exportCsv(key) }}>
              <Button icon={<DownloadOutlined />} loading={csvLoading}>导出 CSV</Button>
            </Dropdown>
            <Dropdown trigger={['click']} menu={{ items: xlsxMenuItems, onClick: ({ key }) => exportXlsx(key) }}>
              <Button icon={<DownloadOutlined />} loading={xlsxLoading}>导出 XLSX</Button>
            </Dropdown>
          </div>
        </div>

        {activeError ? (
          <Alert className="admin-report-lite-alert" showIcon type="warning" message="报表数据暂不可用，当前展示最近一次可视化样例。" />
        ) : null}
        {exportError ? (
          <Alert className="admin-report-lite-alert" showIcon type="error" message="导出失败，请稍后重试。" />
        ) : null}

        <div className="admin-report-metrics">
          {metricCards.map((item) => (
            <div className={`admin-report-metric is-${item.tone}`} key={item.label}>
              <span className="admin-report-metric-icon">{item.icon}</span>
              <div>
                <Text>{item.label} <InfoCircleOutlined /></Text>
                <strong>{item.value}</strong>
                <span>较昨日 <em>{item.delta}</em></span>
              </div>
            </div>
          ))}
        </div>

        <div className="admin-report-chart-grid">
          <section className="admin-report-card admin-report-revenue-card">
            <div className="admin-report-card-head">
              <Title level={2}>收入趋势 <InfoCircleOutlined /></Title>
              <div className="admin-report-segmented">
                <button className="is-active" type="button">小时</button>
                <button type="button">日</button>
                <button type="button">周</button>
                <button type="button">月</button>
              </div>
            </div>
            <RevenueChart rows={trendRows} />
          </section>

          <section className="admin-report-card admin-report-sales-card">
            <Title level={2}>票种销量 <InfoCircleOutlined /></Title>
            <SalesChart rows={productRows} />
          </section>

          <section className="admin-report-card admin-report-payment-card">
            <Title level={2}>支付对账 <InfoCircleOutlined /></Title>
            {paymentRows(reconciliation).map(([label, value, icon, tone]) => (
              <div className={`admin-report-payment-row is-${tone}`} key={label as string}>
                <span>{icon}</span>
                <Text>{label}</Text>
                <strong>{value}</strong>
              </div>
            ))}
          </section>
        </div>

        <div className="admin-report-bottom-grid">
          <section className="admin-report-card admin-report-top-card">
            <Title level={2}>热门票种 TOP5 <InfoCircleOutlined /></Title>
            <div className="admin-report-top-list">
              {topRows.map((row, index) => {
                const value = row.soldTicketCount
                const color = ['#fb4b42', '#1fa36b', '#64c2c9', '#8cbaca', '#b8c8d7'][index]
                return (
                <div className="admin-report-top-row" key={`${row.productId}-${row.ticketTypeId}`}>
                  <span style={{ background: color }}>{index + 1}</span>
                  <Text>{scenicTicketName(row.ticketName)}</Text>
                  <i><b style={{ width: `${Math.max(28, value / 2.7)}px`, background: color }} /></i>
                  <strong>{value} 张</strong>
                </div>
                )
              })}
            </div>
          </section>

          <section className="admin-report-card admin-report-table-card">
            <Title level={2}>运营汇总 <InfoCircleOutlined /></Title>
            <div className="admin-report-summary-table">
              <div className="admin-report-summary-head">
                {['日期', '收入（元）', '订单（笔）', '售票（张）', '待核验（笔）', '退款（笔）'].map((title) => <span key={title}>{title}</span>)}
              </div>
              {tableRows.map((row) => (
                <div className="admin-report-summary-row" key={row.reportDate}>
                  <span>{row.reportDate}</span>
                  <span>{money(row.netPaidAmount)}</span>
                  <span>{row.orderCount}</span>
                  <span>{row.soldTicketCount}</span>
                  <span>{Math.max(row.soldTicketCount - row.checkedInTicketCount, 0)}</span>
                  <span>{row.refundedOrderCount}</span>
                </div>
              ))}
            </div>
            <button className="admin-report-more" type="button">查看更多报表 ›</button>
          </section>
        </div>
      </div>
    </section>
  )
}
