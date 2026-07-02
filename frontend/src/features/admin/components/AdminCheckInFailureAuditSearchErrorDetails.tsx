import { Flex, Typography } from 'antd'
import { ApiError } from '../../../shared/api/errors'

const { Text } = Typography

export function AdminCheckInFailureAuditSearchErrorDetails({ error }: { error: unknown }) {
  const apiError = error instanceof ApiError ? error : null

  return (
    <Flex className="api-error-details" gap={8} vertical>
      <Text>核验失败审计暂时无法检索，请稍后重试。</Text>
      <Text type="secondary">请保留错误码和请求编号，便于后端定位管理员会话、失败码筛选或分页读取问题。</Text>
      {apiError ? (
        <Flex className="api-error-details-meta" gap={8} wrap>
          <Text code>错误码：{apiError.code}</Text>
          {apiError.requestId ? <Text code>请求编号：{apiError.requestId}</Text> : null}
        </Flex>
      ) : null}
    </Flex>
  )
}
