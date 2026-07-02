import { ConfigProvider, Layout } from 'antd'
import type { ReactNode } from 'react'
import { AuthStatus, type AuthMode } from '../features/auth/AuthStatus'
import { appTheme } from '../shared/theme/theme'
import { SideNav } from './SideNav'
import { StatusStrip } from './StatusStrip'
import type { AppPage } from './types'

const { Header, Content } = Layout

type AppShellProps = {
  activePage: AppPage
  authDialogRequest?: {
    mode: AuthMode
    requestId: number
  }
  children: ReactNode
  onPageChange: (page: AppPage) => void
}

export function AppShell({ activePage, authDialogRequest, children, onPageChange }: AppShellProps) {
  return (
    <ConfigProvider theme={appTheme}>
      <Layout className="app-shell">
        <SideNav activePage={activePage} onPageChange={onPageChange} />

        <Layout className="app-main">
          <Header className="app-header">
            <StatusStrip />
            <AuthStatus dialogRequest={authDialogRequest} />
          </Header>

          <Content className="app-content">{children}</Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}
