import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import { Alert, Button, Space, Tag, Typography } from 'antd'
import { useState } from 'react'
import type {
  AdminCheckInFailureAuditLogExportParams,
  AdminCheckInFailureAuditLogParams,
} from '../../shared/api/types'
import { downloadAdminCheckInFailureAuditLogsCsv } from '../admin-check-in-failure-logs/exportCsv'
import { downloadAdminCheckInFailureAuditLogsXlsx } from '../admin-check-in-failure-logs/exportXlsx'
import {
  adminCheckInFailureLogsMode,
  useAdminCheckInFailureAuditLogSearchQuery,
} from '../admin-check-in-failure-logs/queries'
import {
  type CheckInFailureCodeFilter,
} from './adminCheckInFailureAuditDisplay'
import { AdminCheckInFailureAuditCsvErrorDetails } from './components/AdminCheckInFailureAuditCsvErrorDetails'
import { AdminCheckInFailureAuditSearchErrorDetails } from './components/AdminCheckInFailureAuditSearchErrorDetails'
import { AdminCheckInFailureAuditTable } from './components/AdminCheckInFailureAuditTable'
import { AdminCheckInFailureAuditToolbar } from './components/AdminCheckInFailureAuditToolbar'
import { AdminCheckInFailureAuditXlsxErrorDetails } from './components/AdminCheckInFailureAuditXlsxErrorDetails'

const { Text, Title } = Typography

export function AdminCheckInFailureAuditLogPanel() {
  const [failureCode, setFailureCode] = useState<CheckInFailureCodeFilter>('ALL')
  const [ticketCode, setTicketCode] = useState('')
  const [operatorUsername, setOperatorUsername] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(5)
  const [csvExportError, setCsvExportError] = useState<unknown>(null)
  const [xlsxExportError, setXlsxExportError] = useState<unknown>(null)
  const [isCsvExporting, setIsCsvExporting] = useState(false)
  const [isXlsxExporting, setIsXlsxExporting] = useState(false)
  const queryParams: AdminCheckInFailureAuditLogParams = {
    page,
    pageSize,
    ...(failureCode !== 'ALL' ? { failureCode } : {}),
    ...(ticketCode.trim() ? { ticketCode } : {}),
    ...(operatorUsername.trim() ? { operatorUsername } : {}),
    ...(dateFrom.trim() ? { dateFrom } : {}),
    ...(dateTo.trim() ? { dateTo } : {}),
  }
  const exportParams: AdminCheckInFailureAuditLogExportParams = {
    ...(failureCode !== 'ALL' ? { failureCode } : {}),
    ...(ticketCode.trim() ? { ticketCode } : {}),
    ...(operatorUsername.trim() ? { operatorUsername } : {}),
    ...(dateFrom.trim() ? { dateFrom } : {}),
    ...(dateTo.trim() ? { dateTo } : {}),
  }
  const failureLogsQuery = useAdminCheckInFailureAuditLogSearchQuery(queryParams)
  const result = failureLogsQuery.data

  function updateFilter(action: () => void) {
    action()
    setPage(1)
  }

  function clearFilters() {
    setFailureCode('ALL')
    setTicketCode('')
    setOperatorUsername('')
    setDateFrom('')
    setDateTo('')
    setPage(1)
  }

  async function exportFailureLogsCsv() {
    setCsvExportError(null)
    setIsCsvExporting(true)

    try {
      await downloadAdminCheckInFailureAuditLogsCsv(exportParams)
    } catch (error) {
      setCsvExportError(error)
    } finally {
      setIsCsvExporting(false)
    }
  }

  async function exportFailureLogsXlsx() {
    setXlsxExportError(null)
    setIsXlsxExporting(true)

    try {
      await downloadAdminCheckInFailureAuditLogsXlsx(exportParams)
    } catch (error) {
      setXlsxExportError(error)
    } finally {
      setIsXlsxExporting(false)
    }
  }

  return (
    <Space className="admin-card-stack admin-check-in-failure-log-panel" orientation="vertical" size={14}>
      <div className="admin-section-heading admin-check-in-failure-log-heading">
        <div>
          <Title level={2}>核验失败审计</Title>
          <Text type="secondary">只读 GET：按失败码、票码、操作人和日期定位核验业务失败尝试。</Text>
        </div>
        <Space size={8} wrap>
          <Tag color={adminCheckInFailureLogsMode === 'api' ? 'blue' : 'gold'}>
            {adminCheckInFailureLogsMode === 'api' ? 'API Failure Audit' : 'Mock Failure Audit'}
          </Tag>
          <Button
            className="admin-check-in-failure-log-csv-export-action"
            icon={<DownloadOutlined />}
            loading={isCsvExporting}
            onClick={() => void exportFailureLogsCsv()}
          >
            导出失败 CSV
          </Button>
          <Button
            className="admin-check-in-failure-log-xlsx-export-action"
            icon={<DownloadOutlined />}
            loading={isXlsxExporting}
            onClick={() => void exportFailureLogsXlsx()}
          >
            导出失败 XLSX
          </Button>
          <Button
            className="admin-check-in-failure-log-refresh-action"
            icon={<ReloadOutlined />}
            loading={failureLogsQuery.isFetching}
            onClick={() => void failureLogsQuery.refetch()}
          >
            刷新
          </Button>
        </Space>
      </div>

      {csvExportError ? (
        <Alert
          showIcon
          type="error"
          title="核验失败审计 CSV 导出失败"
          description={<AdminCheckInFailureAuditCsvErrorDetails error={csvExportError} />}
        />
      ) : null}

      {xlsxExportError ? (
        <Alert
          showIcon
          type="error"
          title="核验失败审计 XLSX 导出失败"
          description={<AdminCheckInFailureAuditXlsxErrorDetails error={xlsxExportError} />}
        />
      ) : null}

      {failureLogsQuery.error ? (
        <Alert
          showIcon
          type="error"
          title="核验失败审计检索失败"
          description={<AdminCheckInFailureAuditSearchErrorDetails error={failureLogsQuery.error} />}
          action={(
            <Button size="small" onClick={() => void failureLogsQuery.refetch()}>
              重试
            </Button>
          )}
        />
      ) : null}

      <AdminCheckInFailureAuditToolbar
        dateFrom={dateFrom}
        dateTo={dateTo}
        failureCode={failureCode}
        onClear={clearFilters}
        onDateFromChange={(value) => updateFilter(() => setDateFrom(value))}
        onDateToChange={(value) => updateFilter(() => setDateTo(value))}
        onFailureCodeChange={(value) => updateFilter(() => setFailureCode(value))}
        onOperatorUsernameChange={(value) => updateFilter(() => setOperatorUsername(value))}
        onTicketCodeChange={(value) => updateFilter(() => setTicketCode(value))}
        operatorUsername={operatorUsername}
        ticketCode={ticketCode}
      />

      <AdminCheckInFailureAuditTable
        currentPage={result?.page ?? page}
        isLoading={failureLogsQuery.isLoading}
        onPageChange={(nextPage, nextPageSize) => {
          setPage(nextPage)
          setPageSize(nextPageSize)
        }}
        pageSize={result?.pageSize ?? pageSize}
        rows={result?.items ?? []}
        total={result?.total ?? 0}
      />

      <Text className="admin-orders-footnote" type="secondary">
        当前读取 {result?.items.length ?? 0} / {result?.total ?? 0} 条失败记录；CSV/XLSX 仅导出票码、动作、失败码、操作人和请求编号，不展示订单内部 id、手机号、证件号或查询语句。
      </Text>
    </Space>
  )
}
