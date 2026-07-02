import { OrderedListOutlined } from '@ant-design/icons'
import { Button, Typography } from 'antd'

const { Text, Title } = Typography

type BookingHeaderProps = {
  onOpenOrders?: () => void
}

export function BookingHeader({ onOpenOrders }: BookingHeaderProps) {
  return (
    <section className="page-heading booking-heading">
      <div className="booking-heading-copy">
        <Text className="eyebrow">Visitor Booking</Text>
        <Title level={1}>游客购票工作台</Title>
        <Text type="secondary">按照票种、时段、实名信息和订单摘要一步步完成购票。</Text>
      </div>
      <Button className="booking-heading-action" icon={<OrderedListOutlined />} onClick={onOpenOrders}>
        我的订单
      </Button>
    </section>
  )
}
