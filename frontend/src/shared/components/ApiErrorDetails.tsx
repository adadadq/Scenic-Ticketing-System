import { Flex, Typography } from 'antd'
import { ApiError } from '../api/errors'

const { Text } = Typography

type ApiErrorDetailsProps = {
  error: unknown
  fallback: string
  showMeta?: boolean
  supportingText?: string
}

export function ApiErrorDetails({ error, fallback, showMeta = true, supportingText }: ApiErrorDetailsProps) {
  const apiError = error instanceof ApiError ? error : null
  const message = apiError?.message ?? fallback

  return (
    <Flex className="api-error-details" gap={8} vertical>
      <Text>{message}</Text>
      {supportingText ? <Text type="secondary">{supportingText}</Text> : null}
      {apiError && showMeta ? (
        <Flex className="api-error-details-meta" gap={8} wrap>
          <Text code>错误码：{apiError.code}</Text>
          {apiError.requestId ? <Text code>请求编号：{apiError.requestId}</Text> : null}
        </Flex>
      ) : null}
    </Flex>
  )
}
