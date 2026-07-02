import { ReloadOutlined } from '@ant-design/icons'
import { Alert, Button, Flex, Select, Space, Tag, Typography } from 'antd'
import { useMemo, useState } from 'react'
import type {
  AdminCheckInFailureCode,
  AdminExportFileFormat,
  AdminExportJob,
  AdminExportJobStatus,
  AdminExportType,
  AdminRefundType,
} from '../../shared/api/types'
import { ApiErrorDetails } from '../../shared/components/ApiErrorDetails'
import {
  adminExportJobsMode,
  downloadAdminExportJobFile,
  useAdminExportJobCreateMutation,
  useAdminExportJobsQuery,
} from '../admin-export-jobs/queries'
import {
  buildAdminExportJobFilters,
  exportTypeOptions,
  filterEntries,
  filterTagLabel,
  statusOptions,
} from './adminExportJobDisplay'
import { AdminExportJobCreateToolbar } from './components/AdminExportJobCreateToolbar'
import { AdminExportJobTable } from './components/AdminExportJobTable'

const { Text, Title } = Typography

export function AdminExportJobsPanel() {
  const [createExportType, setCreateExportType] = useState<AdminExportType>('ORDER_DETAIL')
  const [fileFormat, setFileFormat] = useState<AdminExportFileFormat>('CSV')
  const [statusFilter, setStatusFilter] = useState<AdminExportJobStatus | 'ALL'>('ALL')
  const [typeFilter, setTypeFilter] = useState<AdminExportType | 'ALL'>('ALL')
  const [dateFrom, setDateFrom] = useState('2026-06-26')
  const [dateTo, setDateTo] = useState('2026-06-28')
  const [ticketCode, setTicketCode] = useState('')
  const [orderNo, setOrderNo] = useState('')
  const [operatorUsername, setOperatorUsername] = useState('')
  const [failureCode, setFailureCode] = useState<AdminCheckInFailureCode | ''>('')
  const [refundType, setRefundType] = useState<AdminRefundType | ''>('')
  const [includeEmpty, setIncludeEmpty] = useState(false)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(5)
  const [createdJob, setCreatedJob] = useState<AdminExportJob | null>(null)
  const [downloadError, setDownloadError] = useState<unknown>(null)
  const [downloadingJobId, setDownloadingJobId] = useState<string | null>(null)
  const listParams = {
    page,
    pageSize,
    ...(statusFilter !== 'ALL' ? { status: statusFilter } : {}),
    ...(typeFilter !== 'ALL' ? { exportType: typeFilter } : {}),
  }
  const exportJobsQuery = useAdminExportJobsQuery(listParams)
  const createExportJobMutation = useAdminExportJobCreateMutation()
  const filters = useMemo(() => buildAdminExportJobFilters({
    dateFrom,
    dateTo,
    exportType: createExportType,
    failureCode,
    includeEmpty,
    operatorUsername,
    orderNo,
    refundType,
    ticketCode,
  }), [createExportType, dateFrom, dateTo, failureCode, includeEmpty, operatorUsername, orderNo, refundType, ticketCode])
  const result = exportJobsQuery.data

  async function createExportJob() {
    setCreatedJob(null)
    setDownloadError(null)
    setPage(1)

    try {
      const job = await createExportJobMutation.mutateAsync({
        exportType: createExportType,
        fileFormat,
        filters,
      })
      setCreatedJob(job)
    } catch {
      // React Query exposes the error state; keep the click handler from creating an unhandled rejection.
    }
  }

  async function downloadJob(job: AdminExportJob) {
    setDownloadError(null)
    setDownloadingJobId(job.jobId)

    try {
      const blob = await downloadAdminExportJobFile(job.jobId, job.fileFormat)
      const objectUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = objectUrl
      link.download = job.fileName ?? `admin-export-${job.jobId}.${job.fileFormat.toLowerCase()}`
      document.body.appendChild(link)
      link.click()
      link.remove()
      URL.revokeObjectURL(objectUrl)
    } catch (error) {
      setDownloadError(error)
    } finally {
      setDownloadingJobId(null)
    }
  }

  return (
    <Space className="admin-card-stack admin-export-jobs-panel" orientation="vertical" size={14}>
      <div className="admin-section-heading admin-export-jobs-heading">
        <div>
          <Title level={2}>异步导出任务</Title>
          <Text type="secondary">大文件先创建任务，再用只读 GET 查看状态；创建任务必须走管理员会话和 CSRF。</Text>
        </div>
        <Space size={8} wrap>
          <Tag color={adminExportJobsMode === 'api' ? 'blue' : 'gold'}>
            {adminExportJobsMode === 'api' ? 'API Export Jobs' : 'Mock Export Jobs'}
          </Tag>
          <Button icon={<ReloadOutlined />} loading={exportJobsQuery.isFetching} onClick={() => void exportJobsQuery.refetch()}>
            刷新
          </Button>
        </Space>
      </div>

      <Alert
        showIcon
        type="info"
        title="任务边界"
        description="前端只提交 exportType、fileFormat 和白名单 filters；不提交 adminUserId、任务状态、fileName、storageKey 或下载链接。"
      />

      {createdJob ? (
        <Alert
          showIcon
          type="success"
          title="异步导出任务已创建"
          description={`任务 ${createdJob.jobId} 已进入 ${createdJob.status}，后端 worker 负责生成文件。`}
        />
      ) : null}

      {createExportJobMutation.error ? (
        <Alert
          showIcon
          type="error"
          title="异步导出任务创建失败"
          description={<ApiErrorDetails error={createExportJobMutation.error} fallback="导出任务创建失败，请稍后重试。" />}
        />
      ) : null}

      {exportJobsQuery.error ? (
        <Alert
          showIcon
          type="error"
          title="异步导出任务列表读取失败"
          description={<ApiErrorDetails error={exportJobsQuery.error} fallback="任务列表读取失败，请稍后重试。" />}
        />
      ) : null}

      {downloadError ? (
        <Alert
          showIcon
          type="error"
          title="异步导出文件下载失败"
          description={<ApiErrorDetails error={downloadError} fallback="任务文件尚未生成或已经失效，请刷新后重试。" />}
        />
      ) : null}

      <AdminExportJobCreateToolbar
        createExportType={createExportType}
        dateFrom={dateFrom}
        dateTo={dateTo}
        failureCode={failureCode}
        fileFormat={fileFormat}
        includeEmpty={includeEmpty}
        isCreating={createExportJobMutation.isPending}
        onCreate={() => void createExportJob()}
        onCreateExportTypeChange={setCreateExportType}
        onDateFromChange={setDateFrom}
        onDateToChange={setDateTo}
        onFailureCodeChange={setFailureCode}
        onFileFormatChange={setFileFormat}
        onIncludeEmptyChange={setIncludeEmpty}
        onOperatorUsernameChange={setOperatorUsername}
        onOrderNoChange={setOrderNo}
        onRefundTypeChange={setRefundType}
        onTicketCodeChange={setTicketCode}
        operatorUsername={operatorUsername}
        orderNo={orderNo}
        refundType={refundType}
        ticketCode={ticketCode}
      />

      <div className="admin-export-job-filter-preview" aria-label="异步导出筛选预览">
        <Text type="secondary">当前 filters：</Text>
        {filterEntries(filters).length > 0
          ? filterEntries(filters).map(([key, value]) => <Tag key={key}>{filterTagLabel(key, value)}</Tag>)
          : <Tag>空对象</Tag>}
      </div>

      <Flex className="admin-export-job-list-toolbar" gap={10} wrap>
        <Select
          className="admin-export-job-type-control"
          onChange={(value) => {
            setTypeFilter(value)
            setPage(1)
          }}
          options={[{ label: '全部类型', value: 'ALL' }, ...exportTypeOptions]}
          value={typeFilter}
        />
        <Select
          className="admin-export-job-status-control"
          onChange={(value) => {
            setStatusFilter(value)
            setPage(1)
          }}
          options={[{ label: '全部状态', value: 'ALL' }, ...statusOptions]}
          value={statusFilter}
        />
      </Flex>

      <AdminExportJobTable
        currentPage={result?.page ?? page}
        downloadingJobId={downloadingJobId}
        isLoading={exportJobsQuery.isLoading}
        onDownload={(job) => void downloadJob(job)}
        onPageChange={(nextPage, nextPageSize) => {
          setPage(nextPage)
          setPageSize(nextPageSize)
        }}
        pageSize={result?.pageSize ?? pageSize}
        rows={result?.items ?? []}
        total={result?.total ?? 0}
      />

      <Text className="admin-orders-footnote" type="secondary">
        列表只展示公开 jobId、任务状态、错误码、申请人账号和文件名；下载必须等任务成功且文件元数据存在，前端不读取 storageKey。
      </Text>
    </Space>
  )
}
