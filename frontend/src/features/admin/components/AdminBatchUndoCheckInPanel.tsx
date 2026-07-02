import { CheckCircleOutlined, CloseCircleOutlined, RollbackOutlined } from '@ant-design/icons'
import { Alert, Button, Flex, Input, Space, Table, Tag, Typography } from 'antd'
import { useMemo, useState } from 'react'
import type { AdminBatchUndoCheckIn, AdminBatchUndoCheckInResult } from '../../../shared/api/types'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'

const { Text, Title } = Typography
const { TextArea } = Input

function parseTicketCodes(value: string) {
  return value
    .split(/[\s,，]+/)
    .map((ticketCode) => ticketCode.trim())
    .filter(Boolean)
}

function batchUndoResultTag(result: AdminBatchUndoCheckInResult) {
  return result.success ? (
    <Tag color="green" icon={<CheckCircleOutlined />}>成功</Tag>
  ) : (
    <Tag color="red" icon={<CloseCircleOutlined />}>失败</Tag>
  )
}

function batchUndoResultDetail(result: AdminBatchUndoCheckInResult) {
  if (result.success) {
    return `${result.undoCheckIn.orderNo} · ${result.undoCheckIn.itemNo}`
  }

  return `${result.code}：${result.message}`
}

type AdminBatchUndoCheckInPanelProps = {
  error: unknown
  isUndoing: boolean
  onSubmit: (ticketCodes: string[], reason: string) => void
  result?: AdminBatchUndoCheckIn
}

export function AdminBatchUndoCheckInPanel({
  error,
  isUndoing,
  onSubmit,
  result,
}: AdminBatchUndoCheckInPanelProps) {
  const [ticketCodeText, setTicketCodeText] = useState('')
  const [reason, setReason] = useState('')
  const [submittedReason, setSubmittedReason] = useState('')
  const ticketCodes = useMemo(() => parseTicketCodes(ticketCodeText), [ticketCodeText])
  const normalizedReason = reason.trim()

  function submitBatchUndoCheckIn() {
    setSubmittedReason(normalizedReason)
    onSubmit(ticketCodes, reason)
  }

  return (
    <Space className="admin-batch-undo-check-in-panel" orientation="vertical" size={12}>
      <Flex align="flex-start" gap={12} justify="space-between" wrap>
        <div>
          <Title level={3}>批量撤销核验</Title>
          <Text type="secondary">状态变更 POST，只提交 ticketCodes 和可选 reason；逐票业务失败不阻断同批其他票码。</Text>
        </div>
        <Tag color="orange">最多 50 个</Tag>
      </Flex>

      <Flex className="admin-batch-undo-check-in-form" gap={10} wrap>
        <TextArea
          aria-label="批量撤销核验票码输入"
          autoSize={{ minRows: 3, maxRows: 6 }}
          className="admin-batch-undo-check-in-input"
          onChange={(event) => setTicketCodeText(event.target.value)}
          placeholder="每行一个撤销核验码，也可以用逗号或空格分隔"
          value={ticketCodeText}
        />
        <Input
          allowClear
          aria-label="批量撤销核验原因输入"
          className="admin-batch-undo-check-in-reason-input"
          maxLength={100}
          onChange={(event) => setReason(event.target.value)}
          placeholder="可选撤销原因，最多 100 字"
          showCount
          value={reason}
        />
        <Button
          className="admin-batch-undo-check-in-action"
          disabled={ticketCodes.length === 0}
          icon={<RollbackOutlined />}
          loading={isUndoing}
          onClick={submitBatchUndoCheckIn}
        >
          批量撤销
        </Button>
      </Flex>

      {error ? (
        <Alert
          showIcon
          type="error"
          title="批量撤销核验请求失败"
          description={(
            <ApiErrorDetails
              error={error}
              fallback="当前批量撤销核验请求未被接受，请检查票码数量、空票码或重复票码。"
              supportingText="请保留错误码和请求编号，便于后端定位管理员会话、请求体或撤销核验状态机问题。"
            />
          )}
        />
      ) : null}

      {result ? (
        <Space className="admin-batch-undo-check-in-results" orientation="vertical" size={10}>
          <Alert
            showIcon
            type={result.failureCount > 0 ? 'warning' : 'success'}
            title="批量撤销核验完成"
            description={`共 ${result.totalCount} 个票码，成功 ${result.successCount} 个，失败 ${result.failureCount} 个。${submittedReason ? `本次原因：${submittedReason}。` : ''}`}
          />
          <Table<AdminBatchUndoCheckInResult>
            className="admin-batch-undo-check-in-table"
            columns={[
              {
                dataIndex: 'ticketCode',
                title: '票码',
                render: (ticketCode: string) => <Text code>{ticketCode}</Text>,
              },
              {
                key: 'result',
                title: '结果',
                render: (_, row) => batchUndoResultTag(row),
              },
              {
                key: 'detail',
                title: '说明',
                render: (_, row) => batchUndoResultDetail(row),
              },
            ]}
            dataSource={result.results}
            pagination={false}
            rowKey={(row) => `${row.ticketCode}-${row.success ? 'success' : row.code}`}
            scroll={{ x: 620 }}
            size="small"
          />
        </Space>
      ) : null}
    </Space>
  )
}
