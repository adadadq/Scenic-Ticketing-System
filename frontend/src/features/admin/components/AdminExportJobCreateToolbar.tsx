import { FileAddOutlined, SearchOutlined } from '@ant-design/icons'
import { Button, Flex, Input, Select } from 'antd'
import type {
  AdminCheckInFailureCode,
  AdminExportFileFormat,
  AdminExportType,
  AdminRefundType,
} from '../../../shared/api/types'
import {
  failureCodeOptions,
  fileFormatOptions,
  refundTypeOptions,
  exportTypeOptions,
  supportsOperator,
  supportsOrderNo,
  supportsTicketCode,
  supportsTrendEmpty,
} from '../adminExportJobDisplay'

export function AdminExportJobCreateToolbar({
  createExportType,
  dateFrom,
  dateTo,
  failureCode,
  fileFormat,
  includeEmpty,
  isCreating,
  onCreate,
  onCreateExportTypeChange,
  onDateFromChange,
  onDateToChange,
  onFailureCodeChange,
  onFileFormatChange,
  onIncludeEmptyChange,
  onOperatorUsernameChange,
  onOrderNoChange,
  onRefundTypeChange,
  onTicketCodeChange,
  operatorUsername,
  orderNo,
  refundType,
  ticketCode,
}: {
  createExportType: AdminExportType
  dateFrom: string
  dateTo: string
  failureCode: AdminCheckInFailureCode | ''
  fileFormat: AdminExportFileFormat
  includeEmpty: boolean
  isCreating: boolean
  onCreate: () => void
  onCreateExportTypeChange: (value: AdminExportType) => void
  onDateFromChange: (value: string) => void
  onDateToChange: (value: string) => void
  onFailureCodeChange: (value: AdminCheckInFailureCode | '') => void
  onFileFormatChange: (value: AdminExportFileFormat) => void
  onIncludeEmptyChange: (value: boolean) => void
  onOperatorUsernameChange: (value: string) => void
  onOrderNoChange: (value: string) => void
  onRefundTypeChange: (value: AdminRefundType | '') => void
  onTicketCodeChange: (value: string) => void
  operatorUsername: string
  orderNo: string
  refundType: AdminRefundType | ''
  ticketCode: string
}) {
  return (
    <Flex className="admin-export-job-create-toolbar" gap={10} wrap>
      <Select
        className="admin-export-job-type-control"
        onChange={onCreateExportTypeChange}
        options={exportTypeOptions}
        value={createExportType}
      />
      <Select
        className="admin-export-job-format-control"
        onChange={onFileFormatChange}
        options={fileFormatOptions}
        value={fileFormat}
      />
      <Input
        allowClear
        className="admin-export-job-date-control"
        onChange={(event) => onDateFromChange(event.target.value)}
        placeholder="起始日期 YYYY-MM-DD"
        value={dateFrom}
      />
      <Input
        allowClear
        className="admin-export-job-date-control"
        onChange={(event) => onDateToChange(event.target.value)}
        placeholder="截至日期 YYYY-MM-DD"
        value={dateTo}
      />
      {supportsTicketCode(createExportType) ? (
        <Input
          allowClear
          className="admin-export-job-text-control"
          onChange={(event) => onTicketCodeChange(event.target.value)}
          placeholder="票码"
          prefix={<SearchOutlined />}
          value={ticketCode}
        />
      ) : null}
      {supportsOrderNo(createExportType) ? (
        <Input
          allowClear
          className="admin-export-job-text-control"
          onChange={(event) => onOrderNoChange(event.target.value)}
          placeholder="订单号"
          prefix={<SearchOutlined />}
          value={orderNo}
        />
      ) : null}
      {supportsOperator(createExportType) ? (
        <Input
          allowClear
          className="admin-export-job-text-control"
          onChange={(event) => onOperatorUsernameChange(event.target.value)}
          placeholder="操作人账号"
          prefix={<SearchOutlined />}
          value={operatorUsername}
        />
      ) : null}
      {createExportType === 'CHECK_IN_FAILURE_AUDIT' ? (
        <Select
          allowClear
          className="admin-export-job-code-control"
          onChange={(value) => onFailureCodeChange(value ?? '')}
          options={failureCodeOptions}
          placeholder="失败码"
          value={failureCode || undefined}
        />
      ) : null}
      {createExportType === 'REFUND_AUDIT' ? (
        <Select
          allowClear
          className="admin-export-job-code-control"
          onChange={(value) => onRefundTypeChange(value ?? '')}
          options={refundTypeOptions}
          placeholder="退款类型"
          value={refundType || undefined}
        />
      ) : null}
      {supportsTrendEmpty(createExportType) ? (
        <Select
          className="admin-export-job-code-control"
          onChange={onIncludeEmptyChange}
          options={[
            { label: '仅活动桶', value: false },
            { label: '补齐空桶', value: true },
          ]}
          value={includeEmpty}
        />
      ) : null}
      <Button
        className="admin-export-job-create-action"
        icon={<FileAddOutlined />}
        loading={isCreating}
        onClick={onCreate}
        type="primary"
      >
        创建任务
      </Button>
    </Flex>
  )
}
