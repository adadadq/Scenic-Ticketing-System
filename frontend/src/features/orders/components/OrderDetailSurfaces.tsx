import { OrderedListOutlined } from '@ant-design/icons'
import { Card, Col, Drawer, Space } from 'antd'
import type { ReactNode } from 'react'
import type { OrderListItem } from '../types'

type OrderDetailContentProps = {
  children: ReactNode
}

type MobileOrderDetailDrawerProps = OrderDetailContentProps & {
  isOpen: boolean
  onClose: () => void
  selectedOrder?: OrderListItem
}

const detailTitle = (
  <Space>
    <OrderedListOutlined />
    <span>订单详情</span>
  </Space>
)

export function DesktopOrderDetailCard({ children }: OrderDetailContentProps) {
  return (
    <Col className="desktop-order-detail-col orders-detail-col" xs={24} xl={8}>
      <Card className="summary-card order-detail-card orders-detail-card-shell" title={detailTitle}>
        {children}
      </Card>
    </Col>
  )
}

export function MobileOrderDetailDrawer({
  children,
  isOpen,
  onClose,
  selectedOrder,
}: MobileOrderDetailDrawerProps) {
  return (
    <Drawer
      className="mobile-order-detail-drawer"
      onClose={onClose}
      open={isOpen && Boolean(selectedOrder)}
      placement="bottom"
      size="large"
      title={detailTitle}
    >
      {children}
    </Drawer>
  )
}
