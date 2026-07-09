import { CustomerServiceOutlined } from '@ant-design/icons'
import { Button, Typography } from 'antd'

const { Text, Title } = Typography

type OrdersHeaderProps = {
  onOpenService?: () => void
}

export function OrdersHeader({ onOpenService }: OrdersHeaderProps) {
  return (
    <section className="page-heading orders-heading">
      <div className="orders-heading-copy">
        <Title level={1}>我的订单</Title>
        <Text>查看订单、支付状态和入园票码</Text>
        <span className="orders-heading-mark" />
      </div>
      <Button className="orders-heading-action" icon={<CustomerServiceOutlined />} onClick={onOpenService}>
        游客服务
      </Button>
    </section>
  )
}
