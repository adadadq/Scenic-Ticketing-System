import { useQuery } from '@tanstack/react-query'
import { Badge, Popover, Space } from 'antd'
import type { BadgeProps } from 'antd'
import { useVisitorSessionQuery } from '../features/auth/queries'
import { healthApi } from '../shared/api/endpoints'
import type { DatabaseHealthPayload, HealthPayload } from '../shared/api/types'
import { ApiErrorDetails } from '../shared/components/ApiErrorDetails'

type StatusStripProps = {
  showVisitorSession?: boolean
  variant?: 'admin' | 'visitor'
}

type StatusBadgeDescriptor = {
  error?: unknown
  errorTitle?: string
  fallback?: string
  label: string
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
    return { label: 'API', status: 'processing' as const, text: '服务检查中' }
  }

  if (healthQuery.isError) {
    return {
      error: healthQuery.error,
      errorTitle: '服务健康检查失败',
      fallback: '服务健康检查失败，请确认后端服务是否启动。',
      label: 'API',
      status: 'error' as const,
      supportingText: '如持续失败，请保留错误码和请求编号，便于后端定位健康检查或网关问题。',
      text: '服务异常',
    }
  }

  return {
    label: 'API',
    status: 'success' as const,
    text: `服务正常 · ${healthQuery.data?.environment ?? '环境未知'}`,
  }
}

function databaseHealthBadge(healthQuery: {
  data?: DatabaseHealthPayload
  error?: unknown
  isError: boolean
  isLoading: boolean
}): StatusBadgeDescriptor {
  if (healthQuery.isLoading) {
    return { label: 'DB', status: 'processing' as const, text: '数据库检查中' }
  }

  if (healthQuery.isError) {
    return {
      error: healthQuery.error,
      errorTitle: '数据库健康检查失败',
      fallback: '数据库健康检查失败，请确认数据库连接是否可用。',
      label: 'DB',
      status: 'error' as const,
      supportingText: '如持续失败，请保留错误码和请求编号，便于后端定位连接池、迁移或数据库权限问题。',
      text: '数据库异常',
    }
  }

  return {
    label: 'DB',
    status: healthQuery.data?.database === 'ok' ? 'success' as const : 'warning' as const,
    text: healthQuery.data?.database === 'ok' ? '数据库正常' : '数据库状态未知',
  }
}

function visitorSessionBadge(sessionQuery: ReturnType<typeof useVisitorSessionQuery>): StatusBadgeDescriptor {
  const visitor = sessionQuery.data ?? null

  if (sessionQuery.isLoading) {
    return { label: '登录', status: 'processing' as const, text: '检查中' }
  }

  if (sessionQuery.isError) {
    return {
      error: sessionQuery.error,
      errorTitle: '登录状态检查失败',
      fallback: '登录状态检查失败，请稍后重试。',
      label: '登录',
      status: 'error' as const,
      supportingText: '如多次失败，请联系客服并提供页面上的问题编号。',
      text: '状态异常',
    }
  }

  if (!visitor) {
    return { label: '登录', status: 'default' as const, text: '未登录' }
  }

  return visitor.isRegistered
    ? { label: '登录', status: 'success' as const, text: '已登录' }
    : { label: '登录', status: 'warning' as const, text: '未注册' }
}

function StatusBadgeWithDiagnostics({
  error,
  errorTitle,
  fallback = '状态检查失败，请稍后重试。',
  label,
  status,
  supportingText,
  text,
}: StatusBadgeDescriptor) {
  const badge = (
    <span
      className={error ? 'status-diagnostic-badge is-error' : 'status-diagnostic-badge'}
      tabIndex={error ? 0 : undefined}
    >
      <span className="status-badge-label">{label}</span>
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

function visitorStatusCopy(badge: StatusBadgeDescriptor, kind: 'database' | 'service'): StatusBadgeDescriptor {
  if (kind === 'service') {
    return {
      ...badge,
      errorTitle: badge.error ? '服务暂时不可用' : badge.errorTitle,
      fallback: badge.error ? '服务暂时不可用，请稍后重试。' : badge.fallback,
      label: '服务',
      supportingText: badge.error ? '如多次失败，请联系客服并提供页面上的问题编号。' : badge.supportingText,
      text: badge.error ? '暂不可用' : badge.text.replace(/^服务正常.*/, '正常').replace('服务检查中', '检查中'),
    }
  }

  return {
    ...badge,
    errorTitle: badge.error ? '数据暂时不可用' : badge.errorTitle,
    fallback: badge.error ? '数据暂时不可用，请稍后重试。' : badge.fallback,
    label: '数据',
    supportingText: badge.error ? '如多次失败，请联系客服并提供页面上的问题编号。' : badge.supportingText,
    text: badge.error
      ? '暂不可用'
      : badge.text.replace('数据库检查中', '检查中').replace('数据库正常', '正常').replace('数据库状态未知', '状态未知'),
  }
}

export function StatusStrip({ showVisitorSession = true, variant = 'visitor' }: StatusStripProps) {
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
  const sessionQuery = useVisitorSessionQuery({ enabled: showVisitorSession })
  const healthBadge = serviceHealthBadge(healthQuery)
  const databaseBadge = databaseHealthBadge(databaseHealthQuery)
  const displayedHealthBadge = variant === 'visitor' ? visitorStatusCopy(healthBadge, 'service') : healthBadge
  const displayedDatabaseBadge = variant === 'visitor' ? visitorStatusCopy(databaseBadge, 'database') : databaseBadge
  const sessionBadge = showVisitorSession ? visitorSessionBadge(sessionQuery) : null

  return (
    <Space className="status-strip" size={16} wrap>
      <StatusBadgeWithDiagnostics {...displayedHealthBadge} />
      <StatusBadgeWithDiagnostics {...displayedDatabaseBadge} />
      {sessionBadge ? <StatusBadgeWithDiagnostics {...sessionBadge} /> : null}
      {variant === 'admin' ? (
        <span className="status-diagnostic-badge csrf-status-badge">
          <span className="status-badge-label">CSRF</span>
          <Badge status="default" text="按需校验" />
        </span>
      ) : null}
    </Space>
  )
}
