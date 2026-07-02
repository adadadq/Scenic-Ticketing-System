import {
  AuditOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
  FileSearchOutlined,
  LockOutlined,
  LoginOutlined,
  LogoutOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, Col, Form, Input, Row, Space, Tag, Typography } from 'antd'
import type { AdminLoginRequest } from '../../shared/api/types'
import { ApiErrorDetails } from '../../shared/components/ApiErrorDetails'
import { useAdminSessionController } from '../admin-auth/useAdminSessionController'
import { AdminCheckInAuditExportPanel } from './AdminCheckInAuditExportPanel'
import { AdminCheckInFailureAuditLogPanel } from './AdminCheckInFailureAuditLogPanel'
import { AdminExportJobsPanel } from './AdminExportJobsPanel'
import { AdminOrdersPanel } from './AdminOrdersPanel'
import { AdminRefundAuditLogPanel } from './AdminRefundAuditLogPanel'
import { AdminReportsPanel } from './AdminReportsPanel'

const { Text, Title } = Typography

const securityItems = [
  { icon: <SafetyCertificateOutlined />, label: 'HTTP-only Cookie', text: '会话凭证仅服务端可读' },
  { icon: <LockOutlined />, label: 'CSRF Header', text: '状态变更请求携带校验' },
  { icon: <UserOutlined />, label: '管理员会话', text: '游客身份不能进入后台' },
  { icon: <AuditOutlined />, label: '审计留痕', text: '关键操作记录可追溯' },
]

const operationBoundaryItems = [
  {
    icon: <FileSearchOutlined />,
    label: '报表只读',
    text: '订单、产品和趋势 read-model 只做 GET 聚合，不展示完整手机号或证件号。',
  },
  {
    icon: <DatabaseOutlined />,
    label: '状态变更',
    text: '核验、撤销核验和退款通过 POST 进入后端，由后端计算状态、金额和库存。',
  },
  {
    icon: <AuditOutlined />,
    label: '审计导出',
    text: '核验、失败核验和退款审计按筛选条件导出，错误态保留错误码和请求编号。',
  },
]

function AdminOperationsBoundaryStrip() {
  return (
    <section className="admin-operations-boundary-strip" aria-label="后台运营边界">
      <div className="admin-operations-boundary-heading">
        <Text className="eyebrow">Operations Boundary</Text>
        <Text strong>后台操作按 read-model、状态变更、审计导出分区推进</Text>
      </div>
      <div className="admin-operations-boundary-grid">
        {operationBoundaryItems.map((item) => (
          <div className="admin-operations-boundary-item" key={item.label}>
            <span className="admin-operations-boundary-icon" aria-hidden="true">
              {item.icon}
            </span>
            <div>
              <Text strong>{item.label}</Text>
              <Text type="secondary">{item.text}</Text>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

export function AdminWorkbench() {
  const [form] = Form.useForm<AdminLoginRequest>()
  const {
    admin,
    authMode,
    isLoginPending,
    isLogoutPending,
    isSessionLoading,
    login,
    loginError,
    logout,
    logoutError,
    sessionError,
  } = useAdminSessionController()
  const activeError = loginError ?? logoutError ?? sessionError
  const sessionLabel = isSessionLoading ? '会话检查中' : admin ? '管理员会话' : '未登录'
  const isAuthenticated = Boolean(admin)

  function submitLogin(values: AdminLoginRequest) {
    login(values, {
      onSuccess: () => form.resetFields(['password']),
    })
  }

  return (
    <>
      <div className="page-heading admin-heading">
        <div className="admin-heading-copy">
          <Text className="eyebrow">Admin Phase 2</Text>
          <Title level={1}>后台运营工作台</Title>
          <Text type="secondary">先用 mock 运营预览验证后台信息架构，再逐步接入核验、退款与报表接口。</Text>
        </div>
        <Space className="admin-heading-status" size={8} wrap>
          <Tag color="green">系统健康</Tag>
          <Tag color={authMode === 'api' ? 'blue' : 'gold'}>{authMode === 'api' ? 'API Auth' : 'Mock Auth'}</Tag>
          <Tag color={admin ? 'cyan' : 'default'}>{sessionLabel}</Tag>
        </Space>
      </div>

      <Row
        className={`admin-workbench-grid${isAuthenticated ? ' is-authenticated' : ''}`}
        align="stretch"
        gutter={[16, 16]}
      >
        <Col xs={24} xl={isAuthenticated ? 24 : 9}>
          <Card className={`workspace-card admin-login-card admin-access-card${isAuthenticated ? ' is-authenticated' : ''}`}>
            {admin ? (
              <div className="admin-access-summary">
                <div className="admin-access-copy">
                  <Text className="eyebrow">Admin Access</Text>
                  <Title level={2}>管理员会话</Title>
                  <Text type="secondary">后台操作只面向授权管理员，状态变更保持 CSRF 与审计边界。</Text>
                </div>
                <div className="admin-session-panel">
                  <CheckCircleOutlined className="admin-session-icon" />
                  <div>
                    <Text strong>{admin.displayName}</Text>
                    <div className="admin-session-meta">
                      <Tag color="cyan">{admin.role}</Tag>
                      <Text type="secondary">@{admin.username}</Text>
                    </div>
                  </div>
                  <Button icon={<LogoutOutlined />} loading={isLogoutPending} onClick={logout}>
                    退出
                  </Button>
                </div>
                <div className="admin-security-grid">
                  {securityItems.map((item) => (
                    <div className="admin-security-item" key={item.label}>
                      {item.icon}
                      <div>
                        <Text strong>{item.label}</Text>
                        <Text type="secondary">{item.text}</Text>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <Space className="admin-card-stack" orientation="vertical" size={18}>
                <div>
                  <Text className="eyebrow">Admin Access</Text>
                  <Title level={2}>管理员登录</Title>
                  <Text type="secondary">后台操作只面向授权管理员，后续会接入真实管理员会话。</Text>
                </div>
                <Form form={form} layout="vertical" onFinish={submitLogin} requiredMark={false}>
                  <Form.Item
                    label="账号"
                    name="username"
                    rules={[{ required: true, message: '请输入管理员账号' }]}
                  >
                    <Input autoComplete="username" prefix={<UserOutlined />} placeholder="admin" />
                  </Form.Item>
                  <Form.Item
                    label="密码"
                    name="password"
                    rules={[{ required: true, message: '请输入管理员密码' }]}
                  >
                    <Input.Password autoComplete="current-password" prefix={<LockOutlined />} placeholder="demo password" />
                  </Form.Item>
                  <Button block htmlType="submit" icon={<LoginOutlined />} loading={isLoginPending} type="primary">
                    登录
                  </Button>
                </Form>

                <Alert
                  showIcon
                  type="info"
                  title="安全边界"
                  description="后台状态变更沿用 CSRF 校验，管理员与游客会话分离。"
                />

                <div className="admin-security-grid">
                  {securityItems.map((item) => (
                    <div className="admin-security-item" key={item.label}>
                      {item.icon}
                      <div>
                        <Text strong>{item.label}</Text>
                        <Text type="secondary">{item.text}</Text>
                      </div>
                    </div>
                  ))}
                </div>
              </Space>
            )}

            {activeError ? (
              <Alert
                showIcon
                className="admin-access-error"
                type="error"
                title="管理员认证失败"
                description={(
                  <ApiErrorDetails
                    error={activeError}
                    fallback="管理员认证失败，请稍后重试。"
                    supportingText="请保留错误码和请求编号，便于后端定位管理员会话、CSRF 或权限边界问题。"
                  />
                )}
              />
            ) : null}
          </Card>
        </Col>

        <Col className="admin-operations-col" xs={24} xl={isAuthenticated ? 24 : 15}>
          <Space className="admin-card-stack admin-operations-stack" orientation="vertical" size={16}>
            {admin ? <AdminOperationsBoundaryStrip /> : null}

            <Card className="workspace-card admin-operation-card admin-report-workspace-card">
              {admin ? (
                <AdminReportsPanel />
              ) : (
                <Alert
                  showIcon
                  type="warning"
                  title="请先登录管理员账号"
                  description="后台报表 read-model 只在管理员会话建立后展示，避免未登录状态看到运营聚合数据。"
                />
              )}
            </Card>

            <Row className="admin-secondary-grid" gutter={[16, 16]}>
              <Col xs={24} lg={15}>
                <Card className="workspace-card admin-operation-card admin-orders-workspace-card">
                  {admin ? (
                    <AdminOrdersPanel />
                  ) : (
                    <Alert
                      showIcon
                      type="warning"
                      title="请先登录管理员账号"
                      description="后台订单 read-model 只在管理员会话建立后展示，避免游客或未登录状态看到运营数据。"
                    />
                  )}
                </Card>
              </Col>

              <Col xs={24} lg={9}>
                <Card className="workspace-card admin-operation-card admin-audit-workspace-card">
                  {admin ? (
                    <Space className="admin-card-stack" orientation="vertical" size={18}>
                      <AdminExportJobsPanel />
                      <AdminCheckInAuditExportPanel />
                      <AdminCheckInFailureAuditLogPanel />
                      <AdminRefundAuditLogPanel />
                    </Space>
                  ) : (
                    <Alert
                      showIcon
                      type="warning"
                      title="请先登录管理员账号"
                      description="退款审计日志只在管理员会话建立后展示，避免未登录状态看到退款金额、操作人和请求编号。"
                    />
                  )}
                </Card>
              </Col>
            </Row>
          </Space>
        </Col>
      </Row>
    </>
  )
}
