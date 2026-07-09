import {
  ArrowLeftOutlined,
  AuditOutlined,
  BarChartOutlined,
  BellOutlined,
  CheckCircleOutlined,
  DollarOutlined,
  DownOutlined,
  DownloadOutlined,
  FileSearchOutlined,
  AppstoreAddOutlined,
  LockOutlined,
  LoginOutlined,
  LogoutOutlined,
  OrderedListOutlined,
  PlusSquareOutlined,
  QrcodeOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  SearchOutlined,
  SunOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { Alert, Button, Card, Col, Drawer, Form, Input, Row, Space, Tag, Typography } from 'antd'
import { useEffect, useState } from 'react'
import type { AdminPage } from '../../app/types'
import type { AdminDailyTrend, AdminLoginRequest, AdminMe, AdminProfileUpdateRequest } from '../../shared/api/types'
import { ApiErrorDetails } from '../../shared/components/ApiErrorDetails'
import type { AdminAuthMode } from '../admin-auth/useAdminSessionController'
import { useAdminDailyTrendQuery } from '../admin-reports/queries'
import { useCurrentAnnouncementQuery, usePublishAnnouncementMutation } from '../announcements/queries'
import { AdminAuditPanel } from './AdminAuditPanel'
import { AdminNoticeButton } from './components/AdminNoticeButton'
import { AdminOrdersPanel } from './AdminOrdersPanel'
import { AdminReportsPanel } from './AdminReportsPanel'
import { AdminSettingsPanel } from './AdminSettingsPanel'
import { AdminTicketsPanel } from './AdminTicketsPanel'

const { Text, Title } = Typography

type DashboardTrendKind = 'revenue' | 'orders' | 'tickets'

const dashboardTrendOptions: Array<{ key: DashboardTrendKind; label: string; field: keyof AdminDailyTrend; unit: string }> = [
  { key: 'revenue', label: '收入趋势', field: 'netPaidAmount', unit: '元' },
  { key: 'orders', label: '订单趋势', field: 'orderCount', unit: '笔' },
  { key: 'tickets', label: '售票趋势', field: 'soldTicketCount', unit: '张' },
]

const dashboardTrendParams = {
  dateFrom: '2026-06-22',
  dateTo: '2026-06-28',
  includeEmpty: true,
}

const adminPageMeta: Record<AdminPage, { eyebrow: string; title: string; subtitle: string }> = {
  admin: {
    eyebrow: '后台二期',
    title: '后台运营工作台',
    subtitle: '先建立管理员会话，再按页面进入票种、报表、订单或审计工作区。',
  },
  tickets: {
    eyebrow: '票务配置',
    title: '票种管理',
    subtitle: '新增票种、调整价格、上下架和删除都必须保留管理员会话与审计边界。',
  },
  reports: {
    eyebrow: '只读报表',
    title: '运营报表',
    subtitle: '聚合查看收入、票数、产品和趋势，不展示游客敏感字段。',
  },
  orders: {
    eyebrow: '订单与状态变更',
    title: '订单运营',
    subtitle: '按订单定位 read-model，在订单详情中执行核验、退款等状态变更。',
  },
  audit: {
    eyebrow: '审计与导出',
    title: '审计导出',
    subtitle: '集中查看导出任务、核验审计、核验失败和退款审计记录。',
  },
  settings: {
    eyebrow: '系统配置',
    title: '系统设置',
    subtitle: '配置账号安全、通知规则、数据维护与系统参数。',
  },
}

const securityItems = [
  { icon: <SafetyCertificateOutlined />, label: '服务端会话', text: '会话凭证仅服务端可读' },
  { icon: <LockOutlined />, label: '防伪请求头', text: '状态变更请求携带校验' },
  { icon: <UserOutlined />, label: '管理员会话', text: '游客身份不能进入后台' },
  { icon: <AuditOutlined />, label: '审计留痕', text: '关键操作记录可追溯' },
]

function AdminLockedPage({ description }: { description: string }) {
  return (
    <Card className="workspace-card admin-operation-card admin-locked-page-card">
      <Alert
        showIcon
        type="warning"
        title="请先登录管理员账号"
        description={description}
      />
    </Card>
  )
}

function trendChartMax(values: number[]) {
  const max = Math.max(...values, 1)
  const step = max >= 1000 ? 10000 : max >= 100 ? 100 : 20

  return Math.max(step, Math.ceil(max / step) * step)
}

function trendAxisLabel(value: number, unit: string) {
  if (unit === '元' && value >= 1000) {
    return `${Math.round(value / 1000)}k`
  }

  return String(value)
}

function AdminTrendChart({ activeTrend, rows }: { activeTrend: DashboardTrendKind; rows: AdminDailyTrend[] }) {
  const option = dashboardTrendOptions.find((item) => item.key === activeTrend) ?? dashboardTrendOptions[0]
  const chartRows = rows.slice(-7)

  if (chartRows.length === 0) {
    return <div className="admin-dashboard-chart-empty">暂无趋势数据</div>
  }

  const values = chartRows.map((row) => Number(row[option.field] ?? 0))
  const max = trendChartMax(values)
  const labels = Array.from({ length: 6 }, (_, index) => Math.round(max - (max / 5) * index))
  const points = chartRows.map((row, index) => {
    const x = 58 + index * 56
    const y = 142 - (Number(row[option.field] ?? 0) / max) * 112

    return { label: row.reportDate.slice(5), value: Number(row[option.field] ?? 0), x, y }
  })
  const linePath = points.map((point, index) => `${index === 0 ? 'M' : 'L'}${point.x} ${point.y}`).join(' ')
  const areaPath = `${linePath} L${points.at(-1)?.x ?? 58} 142 L${points[0]?.x ?? 58} 142 Z`

  return (
    <svg className="admin-dashboard-chart" viewBox="0 0 420 180" role="img" aria-label={option.label}>
      {[0, 1, 2, 3, 4].map((row) => (
        <line
          key={row}
          stroke="#e7edf1"
          strokeDasharray="3 5"
          x1="52"
          x2="400"
          y1={26 + row * 28}
          y2={26 + row * 28}
        />
      ))}
      {labels.map((label, index) => (
        <text fill="#7b8794" fontSize="12" key={label} x="16" y={19 + index * 27}>{trendAxisLabel(label, option.unit)}</text>
      ))}
      {points.map((point) => (
        <text fill="#687385" fontSize="12" key={point.label} textAnchor="middle" x={point.x} y="168">{point.label}</text>
      ))}
      <path d={linePath} fill="none" stroke="#058f8a" strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" />
      <path d={areaPath} fill="url(#adminTrendFill)" opacity="0.55" />
      {points.map((point) => (
        <circle cx={point.x} cy={point.y} fill="#058f8a" key={`${point.label}-${point.value}`} r="4" />
      ))}
      <defs>
        <linearGradient id="adminTrendFill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#49c7bd" stopOpacity="0.28" />
          <stop offset="100%" stopColor="#49c7bd" stopOpacity="0" />
        </linearGradient>
      </defs>
    </svg>
  )
}

function AdminOverviewPage({
  onOpenPage,
  onOpenProfile,
}: {
  onOpenPage: (page: AdminPage) => void
  onOpenProfile: () => void
}) {
  const [announcementForm] = Form.useForm<{ title: string; content: string }>()
  const [activeTrend, setActiveTrend] = useState<DashboardTrendKind>('revenue')
  const [isAnnouncementOpen, setIsAnnouncementOpen] = useState(false)
  const dailyTrendQuery = useAdminDailyTrendQuery(dashboardTrendParams)
  const announcementQuery = useCurrentAnnouncementQuery()
  const publishAnnouncementMutation = usePublishAnnouncementMutation()
  const trendRows = dailyTrendQuery.data ?? []
  const metricCards = [
    { icon: <DollarOutlined />, label: '今日收入（元）', value: '32,568.00', compare: '+12.35% ↗', tone: 'green' },
    { icon: <FileSearchOutlined />, label: '今日订单（笔）', value: '256', compare: '+18.75% ↗', tone: 'blue' },
    { icon: <TeamOutlined />, label: '待核验（笔）', value: '86', compare: '-8.46% ↘', tone: 'orange' },
    { icon: <AppstoreAddOutlined />, label: '今日售票（张）', value: '512', compare: '+15.62% ↗', tone: 'emerald' },
  ]
  const quickActions = [
    { icon: <PlusSquareOutlined />, label: '新增票种', text: '添加新的票种', page: 'tickets' as const },
    { icon: <BellOutlined />, label: '发布公告', text: '通知游客信息', page: 'admin' as const },
    { icon: <SearchOutlined />, label: '订单查询', text: '快速查找订单', page: 'orders' as const },
    { icon: <QrcodeOutlined />, label: '核验管理', text: '票务核验管理', page: 'orders' as const },
    { icon: <ReloadOutlined />, label: '退改处理', text: '处理退订改签', page: 'orders' as const },
    { icon: <DownloadOutlined />, label: '数据导出', text: '导出报表数据', page: 'audit' as const },
  ]
  const entryCards = [
    { icon: <AppstoreAddOutlined />, page: 'tickets' as const, title: '票种管理', text: '管理票种信息、价格、库存及规则设置', action: '立即管理' },
    { icon: <BarChartOutlined />, page: 'reports' as const, title: '运营报表', text: '查看收入、订单、客流等运营数据', action: '查看报表' },
    { icon: <OrderedListOutlined />, page: 'orders' as const, title: '订单处理', text: '处理订单、退款、改签等业务操作', action: '前往处理' },
    { icon: <SafetyCertificateOutlined />, page: 'audit' as const, title: '审计记录', text: '查看系统操作日志与变更记录', action: '查看记录' },
  ]
  const currentAnnouncement = announcementQuery.data

  function closeAnnouncementDrawer() {
    setIsAnnouncementOpen(false)
    publishAnnouncementMutation.reset()
  }

  function publishAnnouncement(values: { title: string; content: string }) {
    publishAnnouncementMutation.mutate(values, {
      onSuccess: () => {
        announcementForm.resetFields()
        closeAnnouncementDrawer()
      },
    })
  }

  return (
    <section className="admin-dashboard" aria-label="运营后台工作台">
      <div className="admin-dashboard-hero">
        <div className="admin-dashboard-hero-copy">
          <Title level={1}>遇龙河票务系统</Title>
          <Text strong>运营后台工作台</Text>
          <Text>遇龙河竹筏漂流，感受山水之美</Text>
        </div>
        <div className="admin-dashboard-top-actions">
          <div className="admin-weather-card">
            <SunOutlined />
            <span>晴 26°C</span>
            <Text>2026-06-28 16:04</Text>
          </div>
          <AdminNoticeButton />
          <button className="admin-profile-button" type="button" onClick={onOpenProfile}>
            <span className="admin-profile-avatar" />
            <strong>管理员</strong>
            <DownOutlined />
          </button>
        </div>
      </div>

      <div className="admin-dashboard-body">
        <section className="admin-dashboard-section">
          <Title level={2}>今日概览</Title>
          <div className="admin-dashboard-metrics">
            {metricCards.map((item) => (
              <div className={`admin-dashboard-metric is-${item.tone}`} key={item.label}>
                <span className="admin-dashboard-metric-icon">{item.icon}</span>
                <div>
                  <Text>{item.label}</Text>
                  <strong>{item.value}</strong>
                  <span>较昨日 <em>{item.compare}</em></span>
                </div>
              </div>
            ))}
          </div>
        </section>

        <div className="admin-dashboard-grid">
          <div className="admin-dashboard-left">
            <Card className="admin-dashboard-card admin-quick-card">
              <Title level={2}>快捷操作</Title>
              <div className="admin-quick-grid">
                {quickActions.map((item) => (
                  <button
                    className="admin-quick-action"
                    key={item.label}
                    type="button"
                    onClick={() => item.label === '发布公告' ? setIsAnnouncementOpen(true) : onOpenPage(item.page)}
                  >
                    {item.icon}
                    <strong>{item.label}</strong>
                    <span>{item.text}</span>
                  </button>
                ))}
              </div>
            </Card>

            <Card className="admin-dashboard-card admin-reminder-card">
              <Title level={2}>系统提醒</Title>
              {currentAnnouncement ? (
                <div className="admin-reminder-row is-green">
                  <span />
                  <Text>{currentAnnouncement.title}：{currentAnnouncement.content}</Text>
                  <em>当前公告</em>
                </div>
              ) : null}
              {[
                ['10:30-12:30 为客流高峰时段，请提前做好核验准备', '2小时前', 'orange'],
                ['3笔订单申请退款，待处理', '3小时前', 'green'],
                ['票种「遇龙河成人票」库存不足，请及时补充', '5小时前', 'blue'],
              ].map(([text, time, tone]) => (
                <div className={`admin-reminder-row is-${tone}`} key={text}>
                  <span />
                  <Text>{text}</Text>
                  <em>{time}</em>
                </div>
              ))}
              <Button type="link">查看全部提醒</Button>
            </Card>
          </div>

          <Card className="admin-dashboard-card admin-trend-card">
            <div className="admin-card-title-row">
              <Title level={2}>关键指标趋势</Title>
            </div>
            <div className="admin-trend-tabs">
              {dashboardTrendOptions.map((option) => (
                <button
                  className={activeTrend === option.key ? 'is-active' : undefined}
                  key={option.key}
                  type="button"
                  onClick={() => setActiveTrend(option.key)}
                >
                  {option.label}
                </button>
              ))}
            </div>
            {dailyTrendQuery.isError ? (
              <Alert showIcon type="warning" message="趋势数据暂时无法读取" />
            ) : (
              <AdminTrendChart activeTrend={activeTrend} rows={trendRows} />
            )}
            <Button type="link" onClick={() => onOpenPage('reports')}>查看完整报表</Button>
          </Card>
        </div>

        <div className="admin-dashboard-entry-grid">
          {entryCards.map((item) => (
            <button className="admin-dashboard-entry" key={item.title} type="button" onClick={() => onOpenPage(item.page)}>
              <span>{item.icon}</span>
              <div>
                <strong>{item.title}</strong>
                <Text>{item.text}</Text>
                <em>{item.action}</em>
              </div>
            </button>
          ))}
        </div>
      </div>
      <Drawer
        className="admin-announcement-drawer"
        destroyOnHidden
        onClose={closeAnnouncementDrawer}
        open={isAnnouncementOpen}
        title="发布公告"
        width={420}
      >
        <Form
          form={announcementForm}
          layout="vertical"
          onFinish={publishAnnouncement}
          initialValues={{ title: '今日开放', content: '遇龙河竹筏漂流正常开放，请按预约时段提前到达码头。' }}
        >
          <Form.Item label="公告标题" name="title" rules={[{ required: true, message: '请输入公告标题' }]}>
            <Input maxLength={40} placeholder="例如：今日开放" />
          </Form.Item>
          <Form.Item label="公告内容" name="content" rules={[{ required: true, message: '请输入公告内容' }]}>
            <Input.TextArea maxLength={200} placeholder="给游客看的简短提示" rows={5} showCount />
          </Form.Item>
          {publishAnnouncementMutation.isError ? (
            <ApiErrorDetails error={publishAnnouncementMutation.error} fallback="公告发布失败，请稍后再试。" />
          ) : null}
          <Space className="admin-announcement-actions">
            <Button onClick={closeAnnouncementDrawer}>取消</Button>
            <Button htmlType="submit" loading={publishAnnouncementMutation.isPending} type="primary">
              发布
            </Button>
          </Space>
        </Form>
      </Drawer>
    </section>
  )
}

function AdminPageContent({
  activePage,
  isAuthenticated,
  onOpenPage,
  onOpenProfile,
}: {
  activePage: AdminPage
  isAuthenticated: boolean
  onOpenPage: (page: AdminPage) => void
  onOpenProfile: () => void
}) {
  if (!isAuthenticated) {
    return (
      <AdminLockedPage description="后台业务页面只在管理员会话建立后展示，避免未登录状态看到运营聚合数据、订单 read-model 或审计记录。" />
    )
  }

  if (activePage === 'reports') {
    return <AdminReportsPanel onOpenProfile={onOpenProfile} />
  }

  if (activePage === 'tickets') {
    return <AdminTicketsPanel />
  }

  if (activePage === 'orders') {
    return <AdminOrdersPanel onOpenProfile={onOpenProfile} />
  }

  if (activePage === 'audit') {
    return <AdminAuditPanel onOpenProfile={onOpenProfile} />
  }

  if (activePage === 'settings') {
    return <AdminSettingsPanel onOpenProfile={onOpenProfile} />
  }

    return <AdminOverviewPage onOpenPage={onOpenPage} onOpenProfile={onOpenProfile} />
}

type AdminWorkbenchProps = {
  activePage: AdminPage
  admin: AdminMe
  authMode: AdminAuthMode
  isLogoutPending: boolean
  isProfileUpdatePending: boolean
  isSessionLoading: boolean
  logout: () => void
  logoutError: unknown
  onOpenPage: (page: AdminPage) => void
  onResetProfileUpdateError: () => void
  onUpdateProfile: (values: AdminProfileUpdateRequest, callbacks?: { onSuccess?: () => void }) => void
  profileUpdateError: unknown
  sessionError: unknown
}

type AdminProfileFormValues = AdminProfileUpdateRequest & {
  confirmPassword?: string
}

type AdminLoginGateProps = {
  activeError: unknown
  authMode: AdminAuthMode
  isLoginPending: boolean
  onOpenVisitor: () => void
  onSubmit: (values: AdminLoginRequest) => void
}

export function AdminLoginGate({
  activeError,
  authMode,
  isLoginPending,
  onOpenVisitor,
  onSubmit,
}: AdminLoginGateProps) {
  const [form] = Form.useForm<AdminLoginRequest>()

  function submitLogin(values: AdminLoginRequest) {
    onSubmit(values)
  }

  return (
    <section className="admin-login-gate" aria-label="运营后台登录">
      <header className="admin-login-topbar">
        <div className="admin-login-brand">
          <div className="admin-login-brand-mark" aria-hidden="true">
            <svg viewBox="0 0 64 64" role="img">
              <circle cx="32" cy="32" r="31" />
              <path d="M15 40h34M18 34l9-15 8 13 5-8 7 10" />
              <path d="M21 43c6 4 15 4 22 0M24 31l3 3 4-5M43 17l2 4 4 1-4 1-2 4-2-4-4-1 4-1z" />
            </svg>
          </div>
          <div>
            <div className="admin-login-brand-title">遇龙河票务系统</div>
            <div className="admin-login-brand-subtitle">运营管理平台</div>
          </div>
        </div>
        <div className="admin-login-gate-status" aria-label="系统状态">
          <span className="admin-login-status-pill"><span className="is-ok" />API 服务正常</span>
          <span className="admin-login-status-pill"><span className="is-ok" />DB 数据库正常</span>
          <span className="admin-login-status-pill" title={authMode === 'api' ? '真实认证模式' : '演示认证模式'}>
            <span className="is-warn" />CSRF 按需校验
          </span>
        </div>
      </header>

      <main className="admin-login-main">
        <Card className="admin-login-gate-card">
          <Space className="admin-card-stack" orientation="vertical" size={28}>
            <div className="admin-login-card-heading">
            <Title level={1}>运营后台登录</Title>
              <Text type="secondary">仅限授权管理员访问</Text>
          </div>
          <Form form={form} layout="vertical" onFinish={submitLogin} requiredMark={false}>
            <Form.Item
              label="管理员账号"
              name="username"
              rules={[{ required: true, message: '请输入管理员账号' }]}
            >
                <Input autoComplete="username" prefix={<UserOutlined />} placeholder="请输入管理员账号" size="large" />
            </Form.Item>
            <Form.Item
              label="密码"
              name="password"
              rules={[{ required: true, message: '请输入管理员密码' }]}
            >
                <Input.Password autoComplete="current-password" prefix={<LockOutlined />} placeholder="请输入密码" size="large" />
            </Form.Item>
            <Button
              block
              className="admin-login-submit-action"
              htmlType="submit"
              icon={<LoginOutlined />}
              loading={isLoginPending}
              size="large"
              type="primary"
            >
              登录后台
            </Button>
          </Form>
            <div className="admin-login-divider"><span />或<span /></div>
            <div className="admin-login-return-row">
              <Button className="admin-login-return-action" icon={<ArrowLeftOutlined />} type="link" onClick={onOpenVisitor}>
                返回游客端
              </Button>
            </div>
          {activeError ? (
            <Alert
              showIcon
              className="admin-access-error admin-login-error"
              type="error"
              message="管理员认证失败"
              description={(
                <ApiErrorDetails
                  error={activeError}
                  fallback="管理员账号或密码错误"
                  showMeta={false}
                />
              )}
            />
          ) : null}
          </Space>
        </Card>
      </main>
      <footer className="admin-login-footer">
        <span><SafetyCertificateOutlined />安全运营 · 数据隔离 · 操作留痕</span>
        <span>遇龙河票务系统运营管理平台</span>
        <span>© 2026 遇龙河票务系统</span>
      </footer>
    </section>
  )
}

export function AdminWorkbench({
  activePage,
  admin,
  authMode,
  isLogoutPending,
  isProfileUpdatePending,
  isSessionLoading,
  logout,
  logoutError,
  onOpenPage,
  onResetProfileUpdateError,
  onUpdateProfile,
  profileUpdateError,
  sessionError,
}: AdminWorkbenchProps) {
  const activeError = logoutError ?? sessionError
  const [isProfileDrawerOpen, setIsProfileDrawerOpen] = useState(false)
  const [profileForm] = Form.useForm<AdminProfileFormValues>()
  const sessionLabel = isSessionLoading ? '会话检查中' : '管理员会话'
  const pageMeta = adminPageMeta[activePage]
  const showAccessCard = false

  useEffect(() => {
    window.scrollTo({ top: 0, left: 0 })
  }, [activePage])

  function openProfileDrawer() {
    profileForm.setFieldsValue({
      confirmPassword: undefined,
      currentPassword: undefined,
      newPassword: undefined,
      username: admin.username,
    })
    onResetProfileUpdateError()
    setIsProfileDrawerOpen(true)
  }

  function closeProfileDrawer() {
    profileForm.resetFields(['currentPassword', 'newPassword', 'confirmPassword'])
    onResetProfileUpdateError()
    setIsProfileDrawerOpen(false)
  }

  function submitProfile(values: AdminProfileFormValues) {
    onUpdateProfile(
      {
        currentPassword: values.currentPassword,
        newPassword: values.newPassword || undefined,
        username: values.username,
      },
      {
        onSuccess: () => {
          profileForm.resetFields(['currentPassword', 'newPassword', 'confirmPassword'])
          setIsProfileDrawerOpen(false)
        },
      },
    )
  }

  return (
    <>
      {activePage !== 'admin' && activePage !== 'tickets' && activePage !== 'reports' && activePage !== 'orders' && activePage !== 'audit' && activePage !== 'settings' ? (
        <div className="page-heading admin-heading" id="admin-top">
          <div className="admin-heading-copy">
            <Text className="eyebrow">{pageMeta.eyebrow}</Text>
            <Title level={1}>{pageMeta.title}</Title>
            <Text type="secondary">{pageMeta.subtitle}</Text>
          </div>
          <Space className="admin-heading-status" size={8} wrap>
            <Tag color="green">系统健康</Tag>
            <Tag color={authMode === 'api' ? 'blue' : 'gold'}>{authMode === 'api' ? '真实认证' : '演示认证'}</Tag>
            <Tag color={admin ? 'cyan' : 'default'}>{sessionLabel}</Tag>
          </Space>
        </div>
      ) : null}

      {activeError ? (
        <Alert
          showIcon
          className="admin-session-error"
          type="error"
          message="管理员会话异常"
          description="请稍后重试，或退出后重新登录。"
        />
      ) : null}

      <Row
        className="admin-workbench-grid is-authenticated"
        align="stretch"
        gutter={[16, 16]}
      >
        {showAccessCard ? (
        <Col xs={24} xl={24}>
          <Card className="workspace-card admin-login-card admin-access-card is-authenticated">
              <div className="admin-access-summary">
                <div className="admin-access-copy">
                  <Text className="eyebrow">后台权限</Text>
                  <Title level={2}>管理员会话</Title>
                  <Text type="secondary">后台操作只面向授权管理员，状态变更保持防伪校验与审计边界。</Text>
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
                  <Button icon={<LockOutlined />} onClick={openProfileDrawer}>
                    修改账号密码
                  </Button>
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

            {activeError ? (
              <Alert
                showIcon
                className="admin-access-error"
                type="error"
                message="管理员认证失败"
                description={(
                  <ApiErrorDetails
                    error={activeError}
                    fallback="管理员账号或密码错误"
                    showMeta={false}
                  />
                )}
              />
            ) : null}
          </Card>
        </Col>
        ) : null}

        <Col className="admin-operations-col" xs={24} xl={24}>
          <AdminPageContent
            activePage={activePage}
            isAuthenticated
            onOpenPage={onOpenPage}
            onOpenProfile={openProfileDrawer}
          />
        </Col>
      </Row>
      <Drawer
        destroyOnHidden
        open={isProfileDrawerOpen}
        size="default"
        title="修改账号和密码"
        onClose={closeProfileDrawer}
      >
        <Form form={profileForm} layout="vertical" requiredMark={false} onFinish={submitProfile}>
          <Form.Item
            label="管理员账号"
            name="username"
            rules={[{ required: true, message: '请输入管理员账号' }]}
          >
            <Input autoComplete="username" prefix={<UserOutlined />} placeholder="请输入新账号" />
          </Form.Item>
          <Form.Item
            label="当前密码"
            name="currentPassword"
            rules={[{ required: true, message: '请输入当前密码' }]}
          >
            <Input.Password autoComplete="current-password" prefix={<LockOutlined />} placeholder="请输入当前密码" />
          </Form.Item>
          <Form.Item
            label="新密码"
            name="newPassword"
            rules={[{ min: 6, message: '密码至少 6 位' }]}
          >
            <Input.Password autoComplete="new-password" prefix={<LockOutlined />} placeholder="不修改则留空" />
          </Form.Item>
          <Form.Item
            dependencies={['newPassword']}
            label="确认新密码"
            name="confirmPassword"
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  const nextPassword = getFieldValue('newPassword')
                  if (!nextPassword || value === nextPassword) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('两次输入的新密码不一致'))
                },
              }),
            ]}
          >
            <Input.Password autoComplete="new-password" prefix={<LockOutlined />} placeholder="再次输入新密码" />
          </Form.Item>
          {profileUpdateError ? (
            <Alert
              showIcon
              className="admin-access-error"
              type="error"
              title="修改失败"
              description={<ApiErrorDetails error={profileUpdateError} fallback="修改失败，请稍后重试。" />}
            />
          ) : null}
          <Button block htmlType="submit" loading={isProfileUpdatePending} type="primary">
            保存修改
          </Button>
        </Form>
      </Drawer>
    </>
  )
}
