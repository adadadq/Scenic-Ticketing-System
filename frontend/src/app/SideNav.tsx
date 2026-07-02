import {
  DashboardOutlined,
  OrderedListOutlined,
  SafetyCertificateOutlined,
  ShoppingCartOutlined,
} from '@ant-design/icons'
import { Layout, Menu, Typography } from 'antd'
import type { AppPage } from './types'

const { Sider } = Layout
const { Text } = Typography

type SideNavProps = {
  activePage: AppPage
  onPageChange: (page: AppPage) => void
}

export function SideNav({ activePage, onPageChange }: SideNavProps) {
  return (
    <Sider className="app-sider" width={248} breakpoint="lg" collapsedWidth={0}>
      <div className="brand">
        <div className="brand-mark">遇</div>
        <div>
          <Text className="brand-title">遇龙河票务</Text>
          <Text className="brand-subtitle">票务与码头运营系统</Text>
        </div>
      </div>
      <Menu
        className="side-menu"
        mode="inline"
        onClick={({ key }) => onPageChange(key as AppPage)}
        selectedKeys={[activePage]}
        items={[
          { key: 'booking', icon: <ShoppingCartOutlined />, label: '游客购票' },
          { key: 'orders', icon: <OrderedListOutlined />, label: '我的订单' },
          { key: 'admin', icon: <DashboardOutlined />, label: '后台管理' },
        ]}
      />
      <div className="sider-note">
        <SafetyCertificateOutlined />
        <span>游客侧默认从会话读取身份，状态变更接口校验 CSRF。</span>
      </div>
    </Sider>
  )
}
