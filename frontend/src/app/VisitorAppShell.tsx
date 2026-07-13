import { CloseOutlined, CustomerServiceOutlined, EnvironmentOutlined, MenuOutlined, OrderedListOutlined, ShoppingCartOutlined } from '@ant-design/icons'
import { Button, ConfigProvider, Layout, Menu, Typography } from 'antd'
import { useState, type ReactNode } from 'react'
import { AuthStatus, type AuthMode } from '../features/auth/AuthStatus'
import { appTheme } from '../shared/theme/theme'
import type { VisitorPage } from './types'

const { Content, Header, Sider } = Layout
const { Text } = Typography

function ScenicLogo() {
  return (
    <svg aria-hidden="true" viewBox="0 0 64 44" className="scenic-logo-mark">
      <path d="M4 30c9-11 14-18 19-18 4 0 7 6 10 12 3-5 6-9 10-9 5 0 9 8 17 17" />
      <path d="M11 34c9 4 32 4 43 0" />
      <path d="M21 28c5 3 16 3 22 0" />
    </svg>
  )
}

type VisitorAppShellProps = {
  activePage: VisitorPage
  authDialogRequest?: {
    mode: AuthMode
    requestId: number
  }
  children: ReactNode
  onPageChange: (page: VisitorPage) => void
}

export function VisitorAppShell({
  activePage,
  authDialogRequest,
  children,
  onPageChange,
}: VisitorAppShellProps) {
  const [isNavigationCollapsed, setIsNavigationCollapsed] = useState(
    () => window.matchMedia('(max-width: 991px)').matches,
  )

  function openPage(page: VisitorPage) {
    onPageChange(page)
    if (window.matchMedia('(max-width: 991px)').matches) {
      setIsNavigationCollapsed(true)
    }
  }

  return (
    <ConfigProvider theme={appTheme}>
      <Layout className={`app-shell visitor-shell visitor-shell-${activePage}`}>
        <Button
          aria-controls="visitor-navigation"
          aria-expanded={!isNavigationCollapsed}
          aria-label={isNavigationCollapsed ? '打开游客导航' : '关闭游客导航'}
          className="visitor-mobile-nav-trigger"
          icon={isNavigationCollapsed ? <MenuOutlined /> : <CloseOutlined />}
          onClick={() => setIsNavigationCollapsed((collapsed) => !collapsed)}
          type="primary"
        />
        <Sider
          breakpoint="lg"
          className="app-sider visitor-sider"
          collapsed={isNavigationCollapsed}
          collapsedWidth={0}
          id="visitor-navigation"
          onBreakpoint={setIsNavigationCollapsed}
          trigger={null}
          width={256}
        >
          <div className="brand">
            <div className="brand-mark visitor-brand-mark"><ScenicLogo /></div>
            <div>
              <Text className="brand-title">遇龙河票务系统</Text>
              <Text className="brand-subtitle">遇见山水 · 遇见美好</Text>
            </div>
          </div>
          <Menu
            className="side-menu"
            mode="inline"
            onClick={({ key }) => openPage(key as VisitorPage)}
            selectedKeys={[activePage]}
            items={[
              { key: 'booking', icon: <ShoppingCartOutlined />, label: '游客购票' },
              { key: 'orders', icon: <OrderedListOutlined />, label: '我的订单' },
              { key: 'service', icon: <CustomerServiceOutlined />, label: '游客服务' },
            ]}
          />
          <div className="visitor-support-card">
            <EnvironmentOutlined />
            <span>
              <Text className="visitor-support-title">遇龙河景区</Text>
              <Text className="visitor-support-line">国家AAAA级旅游景区</Text>
              <Text className="visitor-support-time">山水如画 · 竹筏漂流</Text>
            </span>
          </div>
          <div className="visitor-sider-river" aria-hidden="true" />
        </Sider>

        <Layout className="app-main">
          <Header className="app-header visitor-header">
            <AuthStatus dialogRequest={authDialogRequest} />
          </Header>

          <Content className="app-content visitor-content">{children}</Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}
