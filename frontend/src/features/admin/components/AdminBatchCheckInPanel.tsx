import { CheckCircleOutlined, CloseCircleOutlined, ScanOutlined } from '@ant-design/icons'
import { Alert, Button, Flex, Input, Space, Table, Tag, Typography } from 'antd'
import { useMemo, useState } from 'react'
import type { AdminBatchCheckIn, AdminBatchCheckInResult } from '../../../shared/api/types'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'

const { Text, Title } = Typography
const { TextArea } = Input

function parseTicketCodes(value: string) {
  return value
    .split(/[\s,，]+/)
    .map((ticketCode) => ticketCode.trim())
    .filter(Boolean)
}

function batchResultTag(result: AdminBatchCheckInResult) {
  return result.success ? (
    <Tag color="green" icon={<CheckCircleOutlined />}>成功</Tag>
  ) : (
    <Tag color="red" icon={<CloseCircleOutlined />}>失败</Tag>
  )
}

function batchResultDetail(result: AdminBatchCheckInResult) {
  if (result.success) {
    return `${result.checkIn.orderNo} · ${result.checkIn.itemNo}`
  }

  return `${result.code}：${result.message}`
}

type AdminBatchCheckInPanelProps = {
  error: unknown
  isCheckingIn: boolean
  onSubmit: (ticketCodes: string[]) => void
  result?: AdminBatchCheckIn
}

export function AdminBatchCheckInPanel({
  error,
  isCheckingIn,
  onSubmit,
  result,
}: AdminBatchCheckInPanelProps) {
  const [ticketCodeText, setTicketCodeText] = useState('')
  const ticketCodes = useMemo(() => parseTicketCodes(ticketCodeText), [ticketCodeText])

  function submitBatchCheckIn() {
    onSubmit(ticketCodes)
  }

  return (
    <Space className="admin-batch-check-in-panel" id="admin-mutations" orientation="vertical" size={12}>
      <Flex align="flex-start" gap={12} justify="space-between" wrap>
        <div>
          <Title level={3}>批量票码核验</Title>
          <Text type="secondary">状态变更只提交待核验票码；逐票业务失败不阻断同批其他票码。</Text>
        </div>
        <Tag color="orange">最多 50 个</Tag>
      </Flex>

      <Flex className="admin-batch-check-in-form" gap={10} wrap>
        <TextArea
          aria-label="批量核验票码输入"
          autoSize={{ minRows: 3, maxRows: 6 }}
          className="admin-batch-check-in-input"
          onChange={(event) => setTicketCodeText(event.target.value)}
          placeholder="每行一个核验码，也可以用逗号或空格分隔"
          value={ticketCodeText}
        />
        <Button
          className="admin-batch-check-in-action"
          disabled={ticketCodes.length === 0}
          icon={<ScanOutlined />}
          loading={isCheckingIn}
          onClick={submitBatchCheckIn}
          type="primary"
        >
          批量核验
        </Button>
      </Flex>

      {error ? (
        <Alert
          showIcon
          type="error"
          title="批量核验请求失败"
          description={(
            <ApiErrorDetails
              error={error}
              fallback="当前批量核验请求未被接受，请检查票码数量、空票码或重复票码。"
              supportingText="请保留错误码和请求编号，便于后端定位管理员会话、请求体或核验状态机问题。"
            />
          )}
        />
      ) : null}

      {result ? (
        <Space className="admin-batch-check-in-results" orientation="vertical" size={10}>
          <Alert
            showIcon
            type={result.failureCount > 0 ? 'warning' : 'success'}
            title="批量核验完成"
            description={`共 ${result.totalCount} 个票码，成功 ${result.successCount} 个，失败 ${result.failureCount} 个。`}
          />
          <Table<AdminBatchCheckInResult>
            className="admin-batch-check-in-table"
            columns={[
              {
                dataIndex: 'ticketCode',
                title: '票码',
                render: (ticketCode: string) => <Text code>{ticketCode}</Text>,
              },
              {
                key: 'result',
                title: '结果',
                render: (_, row) => batchResultTag(row),
              },
              {
                key: 'detail',
                title: '说明',
                render: (_, row) => batchResultDetail(row),
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
