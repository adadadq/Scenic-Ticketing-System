import {
  CheckCircleOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Alert, Modal, Segmented, Space, Typography } from 'antd'
import type { FormInstance } from 'antd'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'
import type { AuthMode, LoginFormValues, RegisterFormValues } from '../types'
import { LoginForm } from './LoginForm'
import { RegisterForm } from './RegisterForm'

const { Text } = Typography

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
  registerForm,
}: AuthDialogProps) {
  const errorTitle = mode === 'login' ? '登录失败' : '注册失败'
  const errorFallback = mode === 'login' ? '登录失败，请稍后重试。' : '注册失败，请稍后重试。'
  const errorSupportingText = mode === 'login'
    ? '如多次失败，请稍后再试，或联系客服并提供页面上的问题编号。'
    : '请确认账号、密码和手机号无误；如多次失败，请联系客服并提供页面上的问题编号。'
  const activeModeTitle = mode === 'login' ? '账号登录' : '注册账号'

  return (
    <Modal
      className="visitor-auth-modal"
      destroyOnHidden
      footer={null}
      forceRender
      onCancel={onClose}
      open={open}
      title="登录 / 注册"
      width={760}
    >
      <Space orientation="vertical" size={16} className="auth-modal-stack">
        <Segmented
          block
          options={[
            { label: '账号登录', value: 'login' },
            { label: '注册账号', value: 'register' },
          ]}
          onChange={(value) => onModeChange(value as AuthMode)}
          value={mode}
        />

        <div className="auth-modal-grid">
          <section className="auth-modal-primary-panel">
            <div className="auth-panel-heading">
              <span className="auth-panel-icon">
                <UserOutlined />
              </span>
              <span>
                <Text strong>{activeModeTitle}</Text>
                <Text type="secondary">
                  {mode === 'login' ? '已注册用户可直接登录。' : '填写账号、密码和手机号。'}
                </Text>
              </span>
            </div>

            <div hidden={mode !== 'login'}>
              <LoginForm form={loginForm} isPending={isLoginPending} onSubmit={onLoginSubmit} />
            </div>

            <div hidden={mode !== 'register'}>
              <RegisterForm
                form={registerForm}
                isPending={isRegisterPending}
                onSubmit={onRegisterSubmit}
              />
            </div>
          </section>

          <aside className="auth-modal-guidance-panel">
            <div className="auth-workflow-strip" aria-label="登录注册步骤">
              {[
                { detail: '已有账号直接登录', label: '登录' },
                { detail: '没有账号先注册', label: '注册' },
                { detail: '登录后即可创建订单', label: '购票' },
              ].map((item, index) => (
                <div className="auth-workflow-item" key={item.label}>
                  <span className="auth-workflow-index">{index + 1}</span>
                  <Text strong>{item.label}</Text>
                  <Text type="secondary">{item.detail}</Text>
                </div>
              ))}
            </div>

            <Alert
              className="auth-security-alert"
              icon={<SafetyCertificateOutlined />}
              showIcon
              title={mode === 'login' ? '登录后可继续购票' : '注册后会自动登录'}
              type="info"
              description="账号用于查看订单和继续支付，订单操作会校验当前游客身份。"
            />

            <div className="auth-boundary-note">
              <CheckCircleOutlined />
              <Text>注册只需要账号、密码和手机号。</Text>
            </div>
          </aside>
        </div>

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
      </Space>
    </Modal>
  )
}
