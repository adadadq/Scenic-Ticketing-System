import { useQuery } from '@tanstack/react-query'
import { Badge, Popover, Space } from 'antd'
import type { BadgeProps } from 'antd'
import { useVisitorSessionQuery } from '../features/auth/queries'
import { healthApi } from '../shared/api/endpoints'
import type { DatabaseHealthPayload, HealthPayload } from '../shared/api/types'
import { ApiErrorDetails } from '../shared/components/ApiErrorDetails'

type StatusBadgeDescriptor = {
  error?: unknown
  errorTitle?: string
  fallback?: string
  status: BadgeProps['status']
  supportingText?: string
  text: string
}

function serviceHealthBadge(healthQuery: {
  data?: HealthPayload
  error?: unknown
  isError: boolean
  isLoading: boolean
}): StatusBadgeDescriptor {
  if (healthQuery.isLoading) {
    return { status: 'processing' as const, text: '服务检查中' }
  }

  if (healthQuery.isError) {
    return {
      error: healthQuery.error,
      errorTitle: '服务健康检查失败',
      fallback: '服务健康检查失败，请确认后端服务是否启动。',
      status: 'error' as const,
      supportingText: '如持续失败，请保留错误码和请求编号，便于后端定位健康检查或网关问题。',
      text: '服务异常',
    }
  }

  return {
    status: 'success' as const,
    text: `API 正常 · ${healthQuery.data?.environment ?? 'unknown'}`,
  }
}

function databaseHealthBadge(healthQuery: {
  data?: DatabaseHealthPayload
  error?: unknown
  isError: boolean
  isLoading: boolean
}): StatusBadgeDescriptor {
  if (healthQuery.isLoading) {
    return { status: 'processing' as const, text: '数据库检查中' }
  }

  if (healthQuery.isError) {
    return {
      error: healthQuery.error,
      errorTitle: '数据库健康检查失败',
      fallback: '数据库健康检查失败，请确认数据库连接是否可用。',
      status: 'error' as const,
      supportingText: '如持续失败，请保留错误码和请求编号，便于后端定位连接池、迁移或数据库权限问题。',
      text: '数据库异常',
    }
  }

  return {
    status: healthQuery.data?.database === 'ok' ? 'success' as const : 'warning' as const,
    text: healthQuery.data?.database === 'ok' ? 'DB 正常' : 'DB 状态未知',
  }
}

function visitorSessionBadge(sessionQuery: ReturnType<typeof useVisitorSessionQuery>): StatusBadgeDescriptor {
  const visitor = sessionQuery.data ?? null

  if (sessionQuery.isLoading) {
    return { status: 'processing' as const, text: '会话检查中' }
  }

  if (sessionQuery.isError) {
    return {
      error: sessionQuery.error,
      errorTitle: '游客会话检查失败',
      fallback: '游客会话检查失败，请稍后重试。',
      status: 'error' as const,
      supportingText: '如持续失败，请保留错误码和请求编号，便于后端定位 Cookie、CSRF 或会话读取问题。',
      text: '会话异常',
    }
  }

  if (!visitor) {
    return { status: 'default' as const, text: '游客未登录' }
  }

  return visitor.isRegistered
    ? { status: 'success' as const, text: '实名会话' }
    : { status: 'warning' as const, text: '临时游客会话' }
}

function StatusBadgeWithDiagnostics({
  error,
  errorTitle,
  fallback = '状态检查失败，请稍后重试。',
  status,
  supportingText,
  text,
}: StatusBadgeDescriptor) {
  const badge = (
    <span
      className={error ? 'status-diagnostic-badge is-error' : 'status-diagnostic-badge'}
      tabIndex={error ? 0 : undefined}
    >
      <Badge status={status} text={text} />
    </span>
  )

  if (!error) {
    return badge
  }

  return (
    <Popover
      content={<ApiErrorDetails error={error} fallback={fallback} supportingText={supportingText} />}
      title={errorTitle}
      trigger={['hover', 'focus', 'click']}
    >
      {badge}
    </Popover>
  )
}

export function StatusStrip() {
  const healthQuery = useQuery({
    queryFn: healthApi.process,
    queryKey: ['health', 'process'],
    retry: false,
  })
  const databaseHealthQuery = useQuery({
    queryFn: healthApi.database,
    queryKey: ['health', 'database'],
    retry: false,
  })
  const sessionQuery = useVisitorSessionQuery()
  const healthBadge = serviceHealthBadge(healthQuery)
  const databaseBadge = databaseHealthBadge(databaseHealthQuery)
  const sessionBadge = visitorSessionBadge(sessionQuery)

  return (
    <Space className="status-strip" size={16} wrap>
      <StatusBadgeWithDiagnostics {...healthBadge} />
      <StatusBadgeWithDiagnostics {...databaseBadge} />
      <StatusBadgeWithDiagnostics {...sessionBadge} />
    </Space>
  )
}
