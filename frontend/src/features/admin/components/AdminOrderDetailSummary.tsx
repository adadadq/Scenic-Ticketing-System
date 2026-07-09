import { Alert, Descriptions, Space, Typography } from 'antd'
import type { AdminOrderDetail } from '../../../shared/api/types'
import {
  amountLabel,
  canCheckInItem,
  canFullRefundOrder,
  canPartialRefundItem,
  paymentTag,
  statusTag,
} from '../adminOrderDisplay'

const { Text } = Typography

type AdminOrderDetailSummaryProps = {
  detail: AdminOrderDetail
}

export function AdminOrderDetailSummary({ detail }: AdminOrderDetailSummaryProps) {
  const checkableCount = detail.items.filter((item) => canCheckInItem(detail, item)).length
  const refundableCount = detail.items.filter((item) => canPartialRefundItem(detail, item)).length
  const canRefund = canFullRefundOrder(detail) || refundableCount > 0

  return (
    <>
      <Alert
        showIcon
        type="info"
        title="只读安全边界"
        description="详情只展示脱敏手机号和票项只读视图；核验提交票码，退款只提交原因或选中的票项，状态变更都会校验防伪令牌。"
      />
      <div className="admin-order-detail-summary-grid">
        <section className="admin-order-state-card" aria-label="订单状态摘要">
          <Space align="center" size={8} wrap>
            {statusTag(detail.orderStatus)}
            {paymentTag(detail.paymentStatus)}
          </Space>
          <strong>{amountLabel(detail.payableAmount)}</strong>
          <Text type="secondary">订单 {detail.orderNo}</Text>
          <div className="admin-order-state-facts">
            <span>票项 {detail.items.length} 张</span>
            <span>可核验 {checkableCount} 张</span>
            <span>{canRefund ? `可退 ${refundableCount} 张` : '当前不可退款'}</span>
          </div>
        </section>
        <Descriptions className="admin-order-readonly-descriptions" column={1} size="small" bordered>
          <Descriptions.Item label="游客">{detail.buyerName}</Descriptions.Item>
          <Descriptions.Item label="手机号">{detail.buyerPhoneMasked}</Descriptions.Item>
          <Descriptions.Item label="下单时间">{detail.orderTime}</Descriptions.Item>
          <Descriptions.Item label="订单总额">{amountLabel(detail.totalAmount)}</Descriptions.Item>
          <Descriptions.Item label="应付金额">{amountLabel(detail.payableAmount)}</Descriptions.Item>
        </Descriptions>
      </div>
    </>
  )
}
