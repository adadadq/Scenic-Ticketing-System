import { Alert, Descriptions } from 'antd'
import type { AdminOrderDetail } from '../../../shared/api/types'
import { amountLabel, paymentTag, statusTag } from '../adminOrderDisplay'

type AdminOrderDetailSummaryProps = {
  detail: AdminOrderDetail
}

export function AdminOrderDetailSummary({ detail }: AdminOrderDetailSummaryProps) {
  return (
    <>
      <Alert
        showIcon
        type="info"
        title="只读安全边界"
        description="详情只展示脱敏手机号和票项 read-model；核验提交票码，退款只提交 reason 或 itemNos，状态变更都会校验 CSRF。"
      />
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="订单号">{detail.orderNo}</Descriptions.Item>
        <Descriptions.Item label="游客">{detail.buyerName}</Descriptions.Item>
        <Descriptions.Item label="手机号">{detail.buyerPhoneMasked}</Descriptions.Item>
        <Descriptions.Item label="订单状态">{statusTag(detail.orderStatus)}</Descriptions.Item>
        <Descriptions.Item label="支付状态">{paymentTag(detail.paymentStatus)}</Descriptions.Item>
        <Descriptions.Item label="应付金额">{amountLabel(detail.payableAmount)}</Descriptions.Item>
        <Descriptions.Item label="下单时间">{detail.orderTime}</Descriptions.Item>
      </Descriptions>
    </>
  )
}
