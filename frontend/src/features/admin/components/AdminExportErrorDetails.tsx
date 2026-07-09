import { Flex, Typography } from 'antd'
import { ApiError } from '../../../shared/api/errors'

const { Text } = Typography

type AdminExportErrorDetailsProps = {
  error: unknown
  fallback: string
  supportingText?: string
}

export function AdminExportErrorDetails({
  error,
  fallback,
  supportingText = '请保留错误码和请求编号，便于后端定位管理员会话、筛选参数或导出服务问题。',
}: AdminExportErrorDetailsProps) {
  const apiError = error instanceof ApiError ? error : null
  const isExportTooLarge = apiError?.code === 'ADMIN_EXPORT_TOO_LARGE'

  return (
    <Flex className="api-error-details" gap={8} vertical>
      <Text>
        {isExportTooLarge
          ? '导出数据超过同步导出上限，请缩小日期或筛选范围后重试。'
          : fallback}
      </Text>
      <Text type="secondary">
        {isExportTooLarge
          ? '当前同步导出适合小到中等数据量；大范围导出请先按日期、订单号、票码、失败码或操作人等条件分批下载。'
          : supportingText}
      </Text>
      {apiError ? (
        <Flex className="api-error-details-meta" gap={8} wrap>
          <Text code>错误码：{apiError.code}</Text>
          {apiError.requestId ? <Text code>请求编号：{apiError.requestId}</Text> : null}
        </Flex>
      ) : null}
    </Flex>
  )
}
