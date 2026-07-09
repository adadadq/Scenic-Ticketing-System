import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import { Alert, Button, Space, Tag, Typography } from 'antd'
import { useState } from 'react'
import type { AdminRefundAuditLogExportParams, AdminRefundAuditLogParams } from '../../shared/api/types'
import { downloadAdminRefundAuditLogsCsv } from '../admin-refund-logs/exportCsv'
import { downloadAdminRefundAuditLogsXlsx } from '../admin-refund-logs/exportXlsx'
import { adminRefundLogsMode, useAdminRefundAuditLogSearchQuery } from '../admin-refund-logs/queries'
import { type RefundTypeFilter } from './adminRefundAuditDisplay'
import { AdminRefundAuditCsvErrorDetails } from './components/AdminRefundAuditCsvErrorDetails'
import { AdminRefundAuditSearchErrorDetails } from './components/AdminRefundAuditSearchErrorDetails'
import { AdminRefundAuditTable } from './components/AdminRefundAuditTable'
import { AdminRefundAuditToolbar } from './components/AdminRefundAuditToolbar'
import { AdminRefundAuditXlsxErrorDetails } from './components/AdminRefundAuditXlsxErrorDetails'

const { Text, Title } = Typography

export function AdminRefundAuditLogPanel() {
  const [refundType, setRefundType] = useState<RefundTypeFilter>('ALL')
  const [orderNo, setOrderNo] = useState('')
  const [operatorUsername, setOperatorUsername] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(5)
  const [csvExportError, setCsvExportError] = useState<unknown>(null)
  const [isCsvExporting, setIsCsvExporting] = useState(false)
  const [xlsxExportError, setXlsxExportError] = useState<unknown>(null)
  const [isXlsxExporting, setIsXlsxExporting] = useState(false)
  const exportParams: AdminRefundAuditLogExportParams = {
    ...(refundType !== 'ALL' ? { refundType } : {}),
    ...(orderNo.trim() ? { orderNo } : {}),
    ...(operatorUsername.trim() ? { operatorUsername } : {}),
    ...(dateFrom.trim() ? { dateFrom } : {}),
    ...(dateTo.trim() ? { dateTo } : {}),
  }
  const queryParams: AdminRefundAuditLogParams = {
    page,
    pageSize,
    ...exportParams,
  }
  const refundLogsQuery = useAdminRefundAuditLogSearchQuery(queryParams)
  const result = refundLogsQuery.data

  function updateFilter(action: () => void) {
    action()
    setPage(1)
  }

  function clearFilters() {
    setRefundType('ALL')
    setOrderNo('')
    setOperatorUsername('')
    setDateFrom('')
    setDateTo('')
    setPage(1)
  }

  async function exportRefundLogsXlsx() {
    setXlsxExportError(null)
    setIsXlsxExporting(true)

    try {
      await downloadAdminRefundAuditLogsXlsx(exportParams)
    } catch (error) {
      setXlsxExportError(error)
    } finally {
      setIsXlsxExporting(false)
    }
  }

  async function exportRefundLogsCsv() {
    setCsvExportError(null)
    setIsCsvExporting(true)

    try {
      await downloadAdminRefundAuditLogsCsv(exportParams)
    } catch (error) {
      setCsvExportError(error)
    } finally {
      setIsCsvExporting(false)
    }
  }

  return (
    <Space className="admin-card-stack admin-refund-log-panel" orientation="vertical" size={14}>
      <div className="admin-section-heading admin-refund-log-heading">
        <div>
          <Title level={2}>退款审计检索</Title>
          <Text type="secondary">跨订单只读检索：按退款类型、订单号和操作人定位审计记录。</Text>
        </div>
        <Space size={8} wrap>
          <Tag color={adminRefundLogsMode === 'api' ? 'blue' : 'gold'}>
            {adminRefundLogsMode === 'api' ? '真实审计' : '演示审计'}
          </Tag>
          <Button icon={<ReloadOutlined />} loading={refundLogsQuery.isFetching} onClick={() => void refundLogsQuery.refetch()}>
            刷新
          </Button>
          <Button
            className="admin-refund-log-csv-export-action"
            icon={<DownloadOutlined />}
            loading={isCsvExporting}
            onClick={exportRefundLogsCsv}
          >
            导出退款 CSV
          </Button>
          <Button
            className="admin-refund-log-xlsx-export-action"
            icon={<DownloadOutlined />}
            loading={isXlsxExporting}
            onClick={exportRefundLogsXlsx}
          >
            导出退款 XLSX
          </Button>
        </Space>
      </div>

      {csvExportError ? (
        <Alert
          showIcon
          type="error"
          title="退款审计 CSV 导出失败"
          description={<AdminRefundAuditCsvErrorDetails error={csvExportError} />}
        />
      ) : null}

      {xlsxExportError ? (
        <Alert
          showIcon
          type="error"
          title="退款审计导出失败"
          description={<AdminRefundAuditXlsxErrorDetails error={xlsxExportError} />}
        />
      ) : null}

      {refundLogsQuery.error ? (
        <Alert
          showIcon
          type="error"
          title="退款审计检索失败"
          description={<AdminRefundAuditSearchErrorDetails error={refundLogsQuery.error} />}
          action={(
            <Button size="small" onClick={() => void refundLogsQuery.refetch()}>
              重试
            </Button>
          )}
        />
      ) : null}

      <AdminRefundAuditToolbar
        dateFrom={dateFrom}
        dateTo={dateTo}
        onClear={clearFilters}
        onDateFromChange={(value) => updateFilter(() => setDateFrom(value))}
        onDateToChange={(value) => updateFilter(() => setDateTo(value))}
        onOperatorUsernameChange={(value) => updateFilter(() => setOperatorUsername(value))}
        onOrderNoChange={(value) => updateFilter(() => setOrderNo(value))}
        onRefundTypeChange={(value) => updateFilter(() => setRefundType(value))}
        operatorUsername={operatorUsername}
        orderNo={orderNo}
        refundType={refundType}
      />

      <AdminRefundAuditTable
        currentPage={result?.page ?? page}
        isLoading={refundLogsQuery.isLoading}
        onPageChange={(nextPage, nextPageSize) => {
          setPage(nextPage)
          setPageSize(nextPageSize)
        }}
        pageSize={result?.pageSize ?? pageSize}
        rows={result?.items ?? []}
        total={result?.total ?? 0}
      />

      <Text className="admin-orders-footnote" type="secondary">
        当前读取 {result?.items.length ?? 0} / {result?.total ?? 0} 条审计记录；CSV/XLSX 导出复用当前筛选且不提交分页参数；列表不展示内部管理员 id、完整手机号或查询语句。
      </Text>
    </Space>
  )
}
