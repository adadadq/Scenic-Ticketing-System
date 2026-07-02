import { CloseCircleOutlined, DownloadOutlined, SearchOutlined } from '@ant-design/icons'
import { Alert, Button, Flex, Input, Space, Tag, Typography } from 'antd'
import { useMemo, useState } from 'react'
import type { AdminCheckInAuditLogExportParams } from '../../shared/api/types'
import { downloadAdminCheckInAuditLogsCsv } from '../admin-check-in-logs/exportCsv'
import {
  adminCheckInLogsMode,
  downloadAdminCheckInAuditLogsXlsx,
} from '../admin-check-in-logs/exportXlsx'
import { AdminCheckInAuditCsvExportErrorDetails } from './components/AdminCheckInAuditCsvExportErrorDetails'
import { AdminCheckInAuditExportErrorDetails } from './components/AdminCheckInAuditExportErrorDetails'

const { Text, Title } = Typography

export function AdminCheckInAuditExportPanel() {
  const [ticketCode, setTicketCode] = useState('')
  const [orderNo, setOrderNo] = useState('')
  const [operatorUsername, setOperatorUsername] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [csvExportError, setCsvExportError] = useState<unknown>(null)
  const [xlsxExportError, setXlsxExportError] = useState<unknown>(null)
  const [isCsvExporting, setIsCsvExporting] = useState(false)
  const [isXlsxExporting, setIsXlsxExporting] = useState(false)
  const exportParams = useMemo<AdminCheckInAuditLogExportParams>(() => ({
    ...(ticketCode.trim() ? { ticketCode: ticketCode.trim() } : {}),
    ...(orderNo.trim() ? { orderNo: orderNo.trim() } : {}),
    ...(operatorUsername.trim() ? { operatorUsername: operatorUsername.trim() } : {}),
    ...(dateFrom.trim() ? { dateFrom: dateFrom.trim() } : {}),
    ...(dateTo.trim() ? { dateTo: dateTo.trim() } : {}),
  }), [dateFrom, dateTo, operatorUsername, orderNo, ticketCode])
  const hasFilters = Object.keys(exportParams).length > 0

  function clearFilters() {
    setTicketCode('')
    setOrderNo('')
    setOperatorUsername('')
    setDateFrom('')
    setDateTo('')
  }

  async function exportCheckInLogsXlsx() {
    setXlsxExportError(null)
    setIsXlsxExporting(true)

    try {
      await downloadAdminCheckInAuditLogsXlsx(exportParams)
    } catch (error) {
      setXlsxExportError(error)
    } finally {
      setIsXlsxExporting(false)
    }
  }

  async function exportCheckInLogsCsv() {
    setCsvExportError(null)
    setIsCsvExporting(true)

    try {
      await downloadAdminCheckInAuditLogsCsv(exportParams)
    } catch (error) {
      setCsvExportError(error)
    } finally {
      setIsCsvExporting(false)
    }
  }

  return (
    <Space className="admin-card-stack admin-check-in-log-export-panel" orientation="vertical" size={14}>
      <div className="admin-section-heading admin-check-in-log-export-heading">
        <div>
          <Title level={2}>核验审计导出</Title>
          <Text type="secondary">只读 GET：按票码、订单号、操作人和日期导出核验审计 CSV/XLSX。</Text>
        </div>
        <Tag color={adminCheckInLogsMode === 'api' ? 'blue' : 'gold'}>
          {adminCheckInLogsMode === 'api' ? 'API Check-in Audit' : 'Mock Check-in Audit'}
        </Tag>
      </div>

      {csvExportError ? (
        <Alert
          showIcon
          type="error"
          title="核验审计 CSV 导出失败"
          description={<AdminCheckInAuditCsvExportErrorDetails error={csvExportError} />}
        />
      ) : null}

      {xlsxExportError ? (
        <Alert
          showIcon
          type="error"
          title="核验审计导出失败"
          description={<AdminCheckInAuditExportErrorDetails error={xlsxExportError} />}
        />
      ) : null}

      <Flex className="admin-check-in-log-export-toolbar" gap={10} wrap>
        <Input
          allowClear
          className="admin-check-in-log-export-control"
          onChange={(event) => setTicketCode(event.target.value)}
          placeholder="票码"
          prefix={<SearchOutlined />}
          value={ticketCode}
        />
        <Input
          allowClear
          className="admin-check-in-log-export-control"
          onChange={(event) => setOrderNo(event.target.value)}
          placeholder="订单号"
          prefix={<SearchOutlined />}
          value={orderNo}
        />
        <Input
          allowClear
          className="admin-check-in-log-export-control"
          onChange={(event) => setOperatorUsername(event.target.value)}
          placeholder="操作人账号"
          prefix={<SearchOutlined />}
          value={operatorUsername}
        />
        <Input
          allowClear
          className="admin-check-in-log-export-date"
          onChange={(event) => setDateFrom(event.target.value)}
          placeholder="起始日期 YYYY-MM-DD"
          value={dateFrom}
        />
        <Input
          allowClear
          className="admin-check-in-log-export-date"
          onChange={(event) => setDateTo(event.target.value)}
          placeholder="截至日期 YYYY-MM-DD"
          value={dateTo}
        />
        <Button
          className="admin-check-in-log-csv-export-action"
          icon={<DownloadOutlined />}
          loading={isCsvExporting}
          onClick={exportCheckInLogsCsv}
        >
          导出核验 CSV
        </Button>
        <Button
          className="admin-check-in-log-xlsx-export-action"
          icon={<DownloadOutlined />}
          loading={isXlsxExporting}
          onClick={exportCheckInLogsXlsx}
        >
          导出核验 XLSX
        </Button>
        <Button disabled={!hasFilters} icon={<CloseCircleOutlined />} onClick={clearFilters}>
          清空
        </Button>
      </Flex>

      <Text className="admin-orders-footnote" type="secondary">
        导出列固定为订单号、票项号、票码、动作、操作人账号、操作人展示名、请求编号和审计时间；不包含手机号、证件号或内部管理员 id。
      </Text>
    </Space>
  )
}
