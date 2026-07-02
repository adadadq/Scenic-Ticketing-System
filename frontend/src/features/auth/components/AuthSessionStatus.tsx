import {
  LoginOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Button, Popover, Space, Tag, Typography } from 'antd'
import type { VisitorMe } from '../../../shared/api/types'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'

const { Text } = Typography

type AuthSessionStatusProps = {
  isLogoutPending: boolean
  sessionError: unknown
  isSessionError: boolean
  isSessionLoading: boolean
  onLogin: () => void
  onLogout: () => void
  onRegister: () => void
  onRetrySession: () => void
  visitor: VisitorMe | null
}

export function AuthSessionStatus({
  isLogoutPending,
  sessionError,
  isSessionError,
  isSessionLoading,
  onLogin,
  onLogout,
  onRegister,
  onRetrySession,
  visitor,
}: AuthSessionStatusProps) {
  const isRegistered = visitor?.isRegistered

  return (
    <Space className="auth-status" size={10} wrap>
      <UserOutlined />
      {isSessionError ? (
        <>
          <Popover
            content={(
              <ApiErrorDetails
                error={sessionError}
                fallback="游客会话检查失败，请稍后重试。"
                supportingText="如持续失败，请保留错误码和请求编号，便于后端定位 Cookie、CSRF 或会话读取问题。"
              />
            )}
            title="游客会话检查失败"
            trigger={['hover', 'focus', 'click']}
          >
            <button
              aria-haspopup="dialog"
              aria-label="查看游客会话检查失败详情"
              className="auth-session-error-trigger"
              type="button"
            >
              <Text strong type="danger">
                会话检查失败
              </Text>
            </button>
          </Popover>
          <Button onClick={onRetrySession} size="small">
            重试
          </Button>
        </>
      ) : visitor ? (
        <>
          <Text strong>{visitor.visitorName}</Text>
          <Tag color={isRegistered ? 'green' : 'gold'}>
            {isRegistered ? '已实名' : '临时游客'}
          </Tag>
          {!isRegistered ? (
            <Button icon={<SafetyCertificateOutlined />} onClick={onRegister} size="small" type="primary">
              实名登记
            </Button>
          ) : null}
          <Button icon={<LogoutOutlined />} loading={isLogoutPending} onClick={onLogout} size="small">
            退出
          </Button>
        </>
      ) : (
        <>
          <Text strong>{isSessionLoading ? '检查登录状态' : '未登录'}</Text>
          <Tag>游客</Tag>
          <Button icon={<LoginOutlined />} loading={isSessionLoading} onClick={onLogin} size="small" type="primary">
            手机号登录
          </Button>
        </>
      )}
    </Space>
  )
}
