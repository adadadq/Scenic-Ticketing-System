import { ReloadOutlined } from '@ant-design/icons'
import { Button, Typography } from 'antd'

const { Text, Title } = Typography

type OrdersHeaderProps = {
  isRefreshing: boolean
  onRefresh: () => void
}

export function OrdersHeader({ isRefreshing, onRefresh }: OrdersHeaderProps) {
  return (
    <section className="page-heading orders-heading">
      <div className="orders-heading-copy">
        <Text className="eyebrow">My Orders</Text>
        <Title level={1}>我的订单</Title>
        <Text type="secondary">查看当前会话下的订单，待支付订单可继续模拟支付。</Text>
      </div>
      <Button className="orders-heading-action" icon={<ReloadOutlined />} loading={isRefreshing} onClick={onRefresh}>
        刷新
      </Button>
    </section>
  )
}
