import { useState } from 'react'
import { Alert, Button, Flex, Input, Space, Switch, Tag, Typography } from 'antd'
import { CalendarOutlined, CloseCircleOutlined, DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import { ApiErrorDetails } from '../../shared/components/ApiErrorDetails'
import {
  adminReportsMode,
  useAdminDailyTrendQuery,
  useAdminHourlyTrendQuery,
  useAdminMonthlyTrendQuery,
  useAdminPaymentReconciliationQuery,
  useAdminProductBreakdownQuery,
  useAdminReportSummaryQuery,
} from '../admin-reports/queries'
import { useAdminReportExports } from '../admin-reports/useAdminReportExports'
import { defaultReportParams } from './adminReportDisplay'
import { AdminPaymentReconciliationPanel } from './components/AdminPaymentReconciliationPanel'
import { AdminReportCsvErrorDetails } from './components/AdminReportCsvErrorDetails'
import { AdminReportProductPanel } from './components/AdminReportProductPanel'
import { AdminReportSummaryMetrics } from './components/AdminReportSummaryMetrics'
import { AdminReportTrendExportBar } from './components/AdminReportTrendExportBar'
import { AdminReportTrendPanel } from './components/AdminReportTrendPanel'
import { AdminReportXlsxErrorDetails } from './components/AdminReportXlsxErrorDetails'

const { Text, Title } = Typography
const maxTrendZeroFillDays = 31

function countInclusiveDays(dateFrom?: string, dateTo?: string) {
  if (!dateFrom || !dateTo) {
    return null
  }

  const start = new Date(`${dateFrom}T00:00:00Z`).getTime()
  const end = new Date(`${dateTo}T00:00:00Z`).getTime()
  const millisecondsPerDay = 24 * 60 * 60 * 1000

  return Math.floor((end - start) / millisecondsPerDay) + 1
}

export function AdminReportsPanel() {
  const [dateFrom, setDateFrom] = useState(defaultReportParams.dateFrom ?? '')
  const [dateTo, setDateTo] = useState(defaultReportParams.dateTo ?? '')
  const [includeEmptyTrendBuckets, setIncludeEmptyTrendBuckets] = useState(false)
  const reportParams = {
    ...(dateFrom.trim() ? { dateFrom: dateFrom.trim() } : {}),
    ...(dateTo.trim() ? { dateTo: dateTo.trim() } : {}),
  }
  const zeroFillDayCount = countInclusiveDays(reportParams.dateFrom, reportParams.dateTo)
  const canIncludeEmptyTrendBuckets = zeroFillDayCount !== null &&
    zeroFillDayCount >= 1 &&
    zeroFillDayCount <= maxTrendZeroFillDays
  const trendReportParams = {
    ...reportParams,
    ...(includeEmptyTrendBuckets && canIncludeEmptyTrendBuckets ? { includeEmpty: true } : {}),
  }
  const reportExports = useAdminReportExports({ reportParams, trendReportParams })
  const summaryQuery = useAdminReportSummaryQuery(reportParams)
  const reconciliationQuery = useAdminPaymentReconciliationQuery(reportParams)
  const productBreakdownQuery = useAdminProductBreakdownQuery(reportParams)
  const dailyTrendQuery = useAdminDailyTrendQuery(trendReportParams)
  const hourlyTrendQuery = useAdminHourlyTrendQuery(trendReportParams)
  const monthlyTrendQuery = useAdminMonthlyTrendQuery(trendReportParams)
  const summary = summaryQuery.data
  const productRows = productBreakdownQuery.data ?? []
  const trendRows = dailyTrendQuery.data ?? []
  const hourlyTrendRows = hourlyTrendQuery.data ?? []
  const monthlyTrendRows = monthlyTrendQuery.data ?? []
  const activeError = summaryQuery.error ??
    reconciliationQuery.error ??
    productBreakdownQuery.error ??
    dailyTrendQuery.error ??
    hourlyTrendQuery.error ??
    monthlyTrendQuery.error
  const isFetching = summaryQuery.isFetching ||
    reconciliationQuery.isFetching ||
    productBreakdownQuery.isFetching ||
    dailyTrendQuery.isFetching ||
    hourlyTrendQuery.isFetching ||
    monthlyTrendQuery.isFetching
  const isLoading = summaryQuery.isLoading ||
    reconciliationQuery.isLoading ||
    productBreakdownQuery.isLoading ||
    dailyTrendQuery.isLoading ||
    hourlyTrendQuery.isLoading ||
    monthlyTrendQuery.isLoading

  function refetchReports() {
    void summaryQuery.refetch()
    void reconciliationQuery.refetch()
    void productBreakdownQuery.refetch()
    void dailyTrendQuery.refetch()
    void hourlyTrendQuery.refetch()
    void monthlyTrendQuery.refetch()
  }

  function resetReportFilters() {
    setDateFrom(defaultReportParams.dateFrom ?? '')
    setDateTo(defaultReportParams.dateTo ?? '')
    setIncludeEmptyTrendBuckets(false)
  }

  return (
    <Space className="admin-card-stack" orientation="vertical" size={16}>
      <div className="admin-section-heading">
        <div>
          <Title level={2}>运营报表</Title>
          <Text type="secondary">只读报表 read-model：按订单创建日期聚合，不展示游客敏感字段。</Text>
        </div>
        <Space size={8} wrap>
          <Tag color={adminReportsMode === 'api' ? 'blue' : 'gold'}>
            {adminReportsMode === 'api' ? 'API Reports' : 'Mock Reports'}
          </Tag>
          <Button
            className="admin-report-export-action"
            icon={<DownloadOutlined />}
            loading={reportExports.loading.ordersCsv}
            onClick={reportExports.actions.exportOrdersCsv}
          >
            导出订单 CSV
          </Button>
          <Button
            className="admin-report-xlsx-export-action"
            icon={<DownloadOutlined />}
            loading={reportExports.loading.ordersXlsx}
            onClick={reportExports.actions.exportOrdersXlsx}
          >
            导出订单 XLSX
          </Button>
          <Button icon={<ReloadOutlined />} loading={isFetching} onClick={refetchReports}>
            刷新
          </Button>
        </Space>
      </div>

      <Flex className="admin-report-filter-bar" gap={12} justify="space-between" wrap>
        <Space size={8} wrap>
          <Input
            aria-label="报表开始日期筛选"
            className="admin-report-date-from"
            onChange={(event) => setDateFrom(event.target.value)}
            prefix={<CalendarOutlined />}
            type="date"
            value={dateFrom}
          />
          <Input
            aria-label="报表结束日期筛选"
            className="admin-report-date-to"
            onChange={(event) => setDateTo(event.target.value)}
            prefix={<CalendarOutlined />}
            type="date"
            value={dateTo}
          />
          <Button
            className="admin-report-reset-filters"
            icon={<CloseCircleOutlined />}
            onClick={resetReportFilters}
          >
            重置报表筛选
          </Button>
        </Space>
        <Space className="admin-report-zero-fill-control" size={8} wrap>
          <Switch
            checked={includeEmptyTrendBuckets && canIncludeEmptyTrendBuckets}
            className="admin-report-include-empty"
            disabled={!canIncludeEmptyTrendBuckets}
            onChange={setIncludeEmptyTrendBuckets}
          />
          <Text type="secondary">
            {canIncludeEmptyTrendBuckets
              ? (includeEmptyTrendBuckets ? '趋势补齐空时间桶' : '趋势仅显示有订单活动时间桶')
              : `补零需完整且不超过 ${maxTrendZeroFillDays} 天的日期范围`}
          </Text>
        </Space>
      </Flex>

      {activeError ? (
        <Alert
          showIcon
          type="error"
          title="后台报表读取失败"
          description={(
            <ApiErrorDetails
              error={activeError}
              fallback="后台运营报表暂时无法读取，请稍后重试。"
              supportingText="请保留错误码和请求编号，便于后端定位管理员会话、报表日期范围或聚合查询问题。"
            />
          )}
          action={(
            <Button size="small" onClick={refetchReports}>
              重试
            </Button>
          )}
        />
      ) : null}

      {reportExports.errors.ordersCsv ? (
        <Alert
          showIcon
          type="error"
          title="CSV 导出失败"
          description={<AdminReportCsvErrorDetails error={reportExports.errors.ordersCsv} />}
        />
      ) : null}

      {reportExports.errors.trendCsv ? (
        <Alert
          showIcon
          type="error"
          title="趋势 CSV 导出失败"
          description={<AdminReportCsvErrorDetails error={reportExports.errors.trendCsv} />}
        />
      ) : null}

      {reportExports.errors.trendXlsx ? (
        <Alert
          showIcon
          type="error"
          title="趋势 XLSX 导出失败"
          description={(
            <AdminReportXlsxErrorDetails
              error={reportExports.errors.trendXlsx}
              fallback="趋势 XLSX 暂时无法导出，请稍后重试。"
            />
          )}
        />
      ) : null}

      {reportExports.errors.productBreakdownCsv ? (
        <Alert
          showIcon
          type="error"
          title="产品维度 CSV 导出失败"
          description={(
            <AdminReportCsvErrorDetails
              error={reportExports.errors.productBreakdownCsv}
              fallback="产品维度 CSV 暂时无法导出，请稍后重试。"
            />
          )}
        />
      ) : null}

      {reportExports.errors.paymentReconciliationCsv ? (
        <Alert
          showIcon
          type="error"
          title="支付对账 CSV 导出失败"
          description={(
            <AdminReportCsvErrorDetails
              error={reportExports.errors.paymentReconciliationCsv}
              fallback="支付对账 CSV 暂时无法导出，请稍后重试。"
            />
          )}
        />
      ) : null}

      {reportExports.errors.productBreakdownXlsx ? (
        <Alert
          showIcon
          type="error"
          title="产品维度 XLSX 导出失败"
          description={(
            <AdminReportXlsxErrorDetails
              error={reportExports.errors.productBreakdownXlsx}
              fallback="产品维度 XLSX 暂时无法导出，请稍后重试。"
            />
          )}
        />
      ) : null}

      {reportExports.errors.paymentReconciliationXlsx ? (
        <Alert
          showIcon
          type="error"
          title="支付对账 XLSX 导出失败"
          description={(
            <AdminReportXlsxErrorDetails
              error={reportExports.errors.paymentReconciliationXlsx}
              fallback="支付对账 XLSX 暂时无法导出，请稍后重试。"
            />
          )}
        />
      ) : null}

      {reportExports.errors.ordersXlsx ? (
        <Alert
          showIcon
          type="error"
          title="XLSX 导出失败"
          description={<AdminReportXlsxErrorDetails error={reportExports.errors.ordersXlsx} />}
        />
      ) : null}

      <AdminReportSummaryMetrics reportParams={reportParams} summary={summary} />
      <AdminPaymentReconciliationPanel
        error={reconciliationQuery.error}
        isCsvExporting={reportExports.loading.paymentReconciliationCsv}
        isXlsxExporting={reportExports.loading.paymentReconciliationXlsx}
        isLoading={reconciliationQuery.isLoading}
        onExportCsv={reportExports.actions.exportPaymentReconciliationCsv}
        onExportXlsx={reportExports.actions.exportPaymentReconciliationXlsx}
        reconciliation={reconciliationQuery.data}
        reportParams={reportParams}
      />

      <AdminReportTrendExportBar
        isAnyTrendExporting={reportExports.loading.isAnyTrendExporting}
        isTrendCsvExporting={reportExports.loading.trendCsv}
        isTrendXlsxExporting={reportExports.loading.trendXlsx}
        onExportCsv={(kind) => void reportExports.actions.exportTrendCsv(kind)}
        onExportXlsx={(kind) => void reportExports.actions.exportTrendXlsx(kind)}
      />

      <Flex className="admin-report-content-grid" gap={16} wrap>
        <AdminReportTrendPanel
          emptyText="当前日期范围暂无小时报表数据。"
          isLoading={hourlyTrendQuery.isLoading}
          subtitle="按订单创建小时聚合"
          title="小时趋势"
          trendRows={hourlyTrendRows}
        />
        <AdminReportTrendPanel
          isLoading={isLoading}
          subtitle="按订单创建日聚合"
          title="每日趋势"
          trendRows={trendRows}
        />
        <AdminReportTrendPanel
          emptyText="当前日期范围暂无月度报表数据。"
          isLoading={monthlyTrendQuery.isLoading}
          subtitle="按订单创建月聚合"
          title="月度趋势"
          trendRows={monthlyTrendRows}
        />
        <AdminReportProductPanel
          isCsvExporting={reportExports.loading.productBreakdownCsv}
          isXlsxExporting={reportExports.loading.productBreakdownXlsx}
          isLoading={productBreakdownQuery.isLoading}
          onExportCsv={reportExports.actions.exportProductBreakdownCsv}
          onExportXlsx={reportExports.actions.exportProductBreakdownXlsx}
          productRows={productRows}
        />
      </Flex>

      <Text className="admin-orders-footnote" type="secondary">
        报表接口为只读 GET；CSV/XLSX 导出同样只读；退款/核验状态变更后续单独接入。
      </Text>
    </Space>
  )
}
