import { OrderedListOutlined } from '@ant-design/icons'
import { Button, Space, Typography } from 'antd'
import { useCurrentAnnouncementQuery } from '../../announcements/queries'

const { Text, Title } = Typography

type BookingHeaderProps = {
  onOpenOrders?: () => void
  onOpenService?: () => void
}

export function BookingHeader({ onOpenOrders }: BookingHeaderProps) {
  const announcementQuery = useCurrentAnnouncementQuery()
  const announcement = announcementQuery.data

  return (
    <section className="page-heading booking-heading">
      <div className="booking-heading-copy">
        <Title level={1}>购买门票</Title>
        <Text>遇龙河竹筏漂流，感受山水之美</Text>
        {announcement ? (
          <div className="visitor-announcement-pill">
            <strong>{announcement.title}</strong>
            <span>{announcement.content}</span>
          </div>
        ) : null}
      </div>
      <div className="booking-heading-scene" aria-hidden="true">
        <span className="booking-scene-boat" />
        <span className="booking-scene-pier" />
      </div>
      <Space className="booking-heading-actions" wrap={false}>
        <Button className="booking-heading-action" icon={<OrderedListOutlined />} onClick={onOpenOrders}>
          我的订单
        </Button>
      </Space>
    </section>
  )
}
