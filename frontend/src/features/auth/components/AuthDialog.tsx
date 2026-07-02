import { Alert, Modal, Segmented, Space } from 'antd'
import type { FormInstance } from 'antd'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'
import type { AuthMode, LoginFormValues, RegisterFormValues } from '../types'
import { LoginForm } from './LoginForm'
import { RegisterForm } from './RegisterForm'

type AuthDialogProps = {
  activeError: unknown
  isLoginPending: boolean
  isRegisterPending: boolean
  loginForm: FormInstance<LoginFormValues>
  mode: AuthMode
  onClose: () => void
  onLoginSubmit: (values: LoginFormValues) => void
  onModeChange: (mode: AuthMode) => void
  onRegisterSubmit: (values: RegisterFormValues) => void
  open: boolean
  realNameConfirmed?: boolean
  registerForm: FormInstance<RegisterFormValues>
}

export function AuthDialog({
  activeError,
  isLoginPending,
  isRegisterPending,
  loginForm,
  mode,
  onClose,
  onLoginSubmit,
  onModeChange,
  onRegisterSubmit,
  open,
  realNameConfirmed,
  registerForm,
}: AuthDialogProps) {
  const errorTitle = mode === 'login' ? '手机号登录失败' : '实名登记失败'
  const errorFallback = mode === 'login' ? '登录失败，请稍后重试。' : '实名登记失败，请稍后重试。'
  const errorSupportingText = mode === 'login'
    ? '如持续失败，请稍后再试并保留错误码和请求编号，便于后端定位限流或会话问题。'
    : '请确认实名信息与手机号无误；如持续失败，请保留错误码和请求编号，便于后端定位实名校验问题。'

  return (
    <Modal
      destroyOnHidden
      footer={null}
      forceRender
      onCancel={onClose}
      open={open}
      title={mode === 'login' ? '手机号登录' : '实名登记'}
    >
      <Space orientation="vertical" size={16} className="auth-modal-stack">
        <Segmented
          block
          options={[
            { label: '手机号登录', value: 'login' },
            { label: '实名登记', value: 'register' },
          ]}
          onChange={(value) => onModeChange(value as AuthMode)}
          value={mode}
        />

        <Alert
          showIcon
          title={mode === 'login' ? '手机号登录会创建临时游客会话' : '实名后才能创建订单'}
          type="info"
          description="状态变更请求会自动携带 CSRF Header，游客身份由后端会话读取。"
        />

        {activeError ? (
          <Alert
            showIcon
            title={errorTitle}
            type="error"
            description={(
              <ApiErrorDetails
                error={activeError}
                fallback={errorFallback}
                supportingText={errorSupportingText}
              />
            )}
          />
        ) : null}

        <div hidden={mode !== 'login'}>
          <LoginForm form={loginForm} isPending={isLoginPending} onSubmit={onLoginSubmit} />
        </div>

        <div hidden={mode !== 'register'}>
          <RegisterForm
            form={registerForm}
            isPending={isRegisterPending}
            isSubmitEnabled={Boolean(realNameConfirmed)}
            onSubmit={onRegisterSubmit}
          />
        </div>
      </Space>
    </Modal>
  )
}
