import { Flex, Typography } from 'antd'
import { ApiError } from '../../../shared/api/errors'

const { Text } = Typography

type AdminOrderDetailErrorDetailsProps = {
  error: unknown
}

function AdminOrderDetailOperationErrorDetails({
  error,
  message,
  supportingText,
}: AdminOrderDetailErrorDetailsProps & {
  message: string
  supportingText: string
}) {
  const apiError = error instanceof ApiError ? error : null

  return (
    <Flex className="api-error-details" gap={8} vertical>
      <Text>{message}</Text>
      <Text type="secondary">{supportingText}</Text>
      {apiError ? (
        <Flex className="api-error-details-meta" gap={8} wrap>
          <Text code>错误码：{apiError.code}</Text>
          {apiError.requestId ? <Text code>请求编号：{apiError.requestId}</Text> : null}
        </Flex>
      ) : null}
    </Flex>
  )
}

export function AdminCheckInErrorDetails({ error }: AdminOrderDetailErrorDetailsProps) {
  return (
    <AdminOrderDetailOperationErrorDetails
      error={error}
      message="当前票码暂时无法核验，请刷新详情后重试。"
      supportingText="请保留错误码和请求编号，便于后端定位核验服务问题。"
    />
  )
}

export function AdminRefundAuditErrorDetails({ error }: AdminOrderDetailErrorDetailsProps) {
  return (
    <AdminOrderDetailOperationErrorDetails
      error={error}
      message="退款审计日志暂时无法读取，请稍后重试。"
      supportingText="请保留错误码和请求编号，便于后端定位管理员会话、订单号或审计日志读取问题。"
    />
  )
}

export function AdminRefundErrorDetails({ error }: AdminOrderDetailErrorDetailsProps) {
  return (
    <AdminOrderDetailOperationErrorDetails
      error={error}
      message="当前订单暂时无法退款，请刷新详情后重试。"
      supportingText="请保留错误码和请求编号，便于后端定位退款状态机、库存回补或支付记录问题。"
    />
  )
}

export function AdminPartialRefundErrorDetails({ error }: AdminOrderDetailErrorDetailsProps) {
  return (
    <AdminOrderDetailOperationErrorDetails
      error={error}
      message="当前票项暂时无法部分退款，请刷新详情后重试。"
      supportingText="请保留错误码和请求编号，便于后端定位票项状态、库存回补或支付记录问题。"
    />
  )
}
