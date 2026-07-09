import {
  ArrowLeftOutlined,
  AppstoreAddOutlined,
  AuditOutlined,
  DashboardOutlined,
  FileSearchOutlined,
  OrderedListOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { Button, ConfigProvider, Layout, Menu, Typography } from 'antd'
import type { ReactNode } from 'react'
import type { AdminMe } from '../shared/api/types'
import { appTheme } from '../shared/theme/theme'
import type { AdminPage } from './types'

const { Content, Header, Sider } = Layout
const { Text } = Typography

const adminNavItems: Array<{ icon: ReactNode; key: string; label: string; page: AdminPage }> = [
  { icon: <DashboardOutlined />, key: 'admin', label: '工作台', page: 'admin' },
  { icon: <AppstoreAddOutlined />, key: 'tickets', label: '票种管理', page: 'tickets' },
  { icon: <FileSearchOutlined />, key: 'reports', label: '报表管理', page: 'reports' },
  { icon: <OrderedListOutlined />, key: 'orders', label: '订单管理', page: 'orders' },
  { icon: <AuditOutlined />, key: 'audit', label: '审计日志', page: 'audit' },
  { icon: <SettingOutlined />, key: 'settings', label: '系统设置', page: 'settings' },
]

type AdminAppShellProps = {
  activePage: AdminPage
  admin?: AdminMe
  children: ReactNode
  isLogoutPending?: boolean
  logout?: () => void
  onOpenVisitor: () => void
  onPageChange: (page: AdminPage) => void
}

export function AdminAppShell({
  activePage,
  admin,
  children,
  isLogoutPending,
  logout,
  onOpenVisitor,
  onPageChange,
}: AdminAppShellProps) {
  return (
    <ConfigProvider theme={appTheme}>
      <Layout className={`app-shell admin-shell admin-shell-${activePage}`}>
        <Sider className="app-sider admin-sider" width={284} breakpoint="lg" collapsedWidth={0}>
          <div className="brand admin-brand">
            <div className="brand-mark admin-brand-mark" aria-hidden="true">
              <svg viewBox="0 0 64 64" role="img">
                <circle cx="32" cy="32" r="30" />
                <path d="M14 42h36M18 35l10-17 9 14 5-8 7 11" />
                <path d="M22 45c7 4 15 4 22 0" />
              </svg>
            </div>
            <div>
              <Text className="brand-title">遇龙河票务系统</Text>
              <Text className="brand-subtitle">运营后台</Text>
            </div>
          </div>
          <Menu
            className="side-menu admin-side-menu"
            mode="inline"
            onClick={({ key }) => onPageChange(adminNavItems.find((item) => item.key === key)?.page ?? 'admin')}
            selectedKeys={[activePage]}
            items={adminNavItems.map((item) => ({
              icon: item.icon,
              key: item.key,
              label: item.label,
            }))}
          />
          <div className="admin-sider-spacer" />
          {admin ? (
            <div className="admin-sider-account">
              <div className="admin-sider-account-main">
                <div className="admin-sider-avatar" aria-hidden="true">
                  <span />
                </div>
                <div>
                  <Text strong>{admin.displayName || admin.username || '管理员'}</Text>
                  <Text className="admin-role-pill">{admin.role === 'SUPER_ADMIN' ? '超级管理员' : admin.role}</Text>
                  <Text type="secondary">@{admin.username}</Text>
                </div>
              </div>
              <Button
                block
                icon={<ArrowLeftOutlined />}
                loading={isLogoutPending}
                type="text"
                onClick={logout}
              >
                退出登录
              </Button>
            </div>
          ) : (
            <div className="sider-note admin-sider-note">
              <SafetyCertificateOutlined />
              <span>后台端只面向授权管理员。</span>
            </div>
          )}
        </Sider>

        <Layout className="app-main admin-main">
          <Header className="app-header admin-app-header">
            <Button icon={<ArrowLeftOutlined />} onClick={onOpenVisitor}>
              返回游客端
            </Button>
          </Header>

          <Content className="app-content admin-content">{children}</Content>
          <nav className="admin-mobile-tabbar" aria-label="管理端移动导航">
            {adminNavItems.map((item) => (
              <button
                className={activePage === item.page ? 'is-active' : undefined}
                key={item.label}
                type="button"
                onClick={() => onPageChange(item.page)}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}
