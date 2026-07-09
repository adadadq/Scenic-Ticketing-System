import { DownloadOutlined } from '@ant-design/icons'
import { Button, Space, Table, Tag, Typography } from 'antd'
import type { AdminExportJob, AdminExportJobStatus } from '../../../shared/api/types'
import {
  exportTypeLabel,
  filterEntries,
  filterTagLabel,
  formatTime,
  statusTag,
} from '../adminExportJobDisplay'

const { Text } = Typography

export function AdminExportJobTable({
  currentPage,
  downloadingJobId,
  isLoading,
  onDownload,
  onPageChange,
  pageSize,
  rows,
  total,
}: {
  currentPage: number
  downloadingJobId: string | null
  isLoading: boolean
  onDownload: (job: AdminExportJob) => void
  onPageChange: (nextPage: number, nextPageSize: number) => void
  pageSize: number
  rows: AdminExportJob[]
  total: number
}) {
  return (
    <Table<AdminExportJob>
      className="admin-export-job-table"
      columns={[
        {
          key: 'job',
          title: '任务',
          width: 230,
          render: (_, job) => (
            <Space orientation="vertical" size={0}>
              <Text code>{job.jobId}</Text>
              <Text type="secondary">{exportTypeLabel(job.exportType)} · {job.fileFormat}</Text>
            </Space>
          ),
        },
        {
          dataIndex: 'status',
          title: '状态',
          width: 100,
          render: (status: AdminExportJobStatus) => statusTag(status),
        },
        {
          key: 'time',
          title: '时间',
          width: 180,
          render: (_, job) => (
            <Space orientation="vertical" size={0}>
              <Text>{formatTime(job.requestedAt)}</Text>
              <Text type="secondary">@{job.requestedByUsername}</Text>
              <Text type="secondary">完成：{formatTime(job.finishedAt)}</Text>
            </Space>
          ),
        },
        {
          key: 'filters',
          title: '筛选',
          width: 260,
          render: (_, job) => (
            <Space size={[4, 4]} wrap>
              {filterEntries(job.filters).length > 0
                ? filterEntries(job.filters).map(([key, value]) => <Tag key={key}>{filterTagLabel(key, value)}</Tag>)
                : <Text type="secondary">无筛选</Text>}
            </Space>
          ),
        },
        {
          key: 'result',
          title: '结果',
          width: 220,
          render: (_, job) => (
            <Space orientation="vertical" size={0}>
              {job.fileName ? <Text>{job.fileName}</Text> : <Text type="secondary">文件未生成</Text>}
              {job.errorCode ? <Text type="danger">{job.errorCode}</Text> : null}
            </Space>
          ),
        },
        {
          key: 'action',
          title: '操作',
          width: 118,
          render: (_, job) => (
            <Button
              className="admin-export-job-download-action"
              disabled={job.status !== 'SUCCEEDED' || !job.fileName}
              icon={<DownloadOutlined />}
              loading={downloadingJobId === job.jobId}
              onClick={() => onDownload(job)}
              size="small"
            >
              下载
            </Button>
          ),
        },
      ]}
      dataSource={rows}
      loading={isLoading}
      locale={{ emptyText: '暂无异步导出任务' }}
      pagination={{
        current: currentPage,
        onChange: onPageChange,
        pageSize,
        showSizeChanger: true,
        total,
      }}
      rowKey={(job) => job.jobId}
      scroll={{ x: 1110 }}
      size="small"
    />
  )
}
