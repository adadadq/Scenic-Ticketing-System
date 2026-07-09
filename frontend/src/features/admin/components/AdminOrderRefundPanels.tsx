import { FieldTimeOutlined, UndoOutlined } from '@ant-design/icons'
import { Button, Checkbox, Flex, Input, Popconfirm, Space, Tag, Typography } from 'antd'
import type { AdminOrderDetail } from '../../../shared/api/types'
import { scenicTicketName } from '../../../shared/display/scenicText'
import {
  amountLabel,
  canFullRefundOrder,
  canPartialRefundItem,
  canPartialRefundOrder,
  itemStatusLabel,
} from '../adminOrderDisplay'

const { Text, Title } = Typography

function canSubmitPartialRefundItems(detail: AdminOrderDetail, itemNos: string[]) {
  return (
    itemNos.length > 0 &&
    itemNos.every((itemNo) => {
      const item = detail.items.find((candidate) => candidate.itemNo === itemNo)
      return item ? canPartialRefundItem(detail, item) : false
    })
  )
}

function RefundStatePath({
  isEligible,
  steps,
}: {
  isEligible: boolean
  steps: string[]
}) {
  return (
    <div className="admin-refund-state-path" aria-label="退款状态机路径">
      {steps.map((step, index) => (
        <span className={isEligible ? 'is-ready' : 'is-blocked'} key={step}>
          {step}
          {index < steps.length - 1 ? <Text type="secondary">→</Text> : null}
        </span>
      ))}
    </div>
  )
}

type AdminOrderRefundPanelsProps = {
  detail: AdminOrderDetail
  isPartialRefunding: boolean
  isRefunding: boolean
  onFullRefund: () => void
  onPartialRefund: () => void
  onPartialRefundItemNosChange: (itemNos: string[]) => void
  onPartialRefundReasonChange: (reason: string) => void
  onRefundReasonChange: (reason: string) => void
  partialRefundItemNos: string[]
  partialRefundReason: string
  refundReason: string
}

export function AdminOrderRefundPanels({
  detail,
  isPartialRefunding,
  isRefunding,
  onFullRefund,
  onPartialRefund,
  onPartialRefundItemNosChange,
  onPartialRefundReasonChange,
  onRefundReasonChange,
  partialRefundItemNos,
  partialRefundReason,
  refundReason,
}: AdminOrderRefundPanelsProps) {
  const canFullRefund = canFullRefundOrder(detail)
  const canPartialRefund = canPartialRefundOrder(detail)
  const canSubmitPartialRefund = canPartialRefundOrder(detail) &&
    canSubmitPartialRefundItems(detail, partialRefundItemNos) &&
    !isRefunding &&
    !isPartialRefunding

  return (
    <>
      <div className="admin-refund-action-panel">
        <Flex align="center" justify="space-between" wrap>
          <div>
            <Title level={3}>整单退款</Title>
            <Text type="secondary">状态变更只提交退款原因；退款金额、票项和库存回补由后端计算。</Text>
          </div>
          <Tag color={canFullRefund ? 'orange' : 'default'}>
            {canFullRefund ? '可整单退款' : '当前不可退款'}
          </Tag>
        </Flex>
        <RefundStatePath
          isEligible={canFullRefund}
          steps={['已支付订单', '全部未使用', '符合退款规则']}
        />
        <Input.TextArea
          className="admin-refund-reason-input"
          maxLength={100}
          onChange={(event) => onRefundReasonChange(event.target.value)}
          placeholder="退款原因，选填，最多 100 字"
          rows={2}
          showCount
          value={refundReason}
        />
        <Flex gap={8} justify="end" wrap>
          <Popconfirm
            cancelText="取消"
            disabled={!canFullRefund || isRefunding || isPartialRefunding}
            okText="确认退款"
            onConfirm={onFullRefund}
            title="确认对这笔订单执行整单退款？"
          >
            <Button
              className="admin-full-refund-action"
              disabled={!canFullRefund || isRefunding || isPartialRefunding}
              icon={<UndoOutlined />}
              loading={isRefunding}
            >
              整单退款
            </Button>
          </Popconfirm>
          {!canFullRefund ? (
            <Button className="admin-detail-disabled-action" disabled icon={<FieldTimeOutlined />}>
              退款不可用
            </Button>
          ) : null}
        </Flex>
      </div>

      <div className="admin-partial-refund-action-panel">
        <Flex align="center" justify="space-between" wrap>
          <div>
            <Title level={3}>部分退款</Title>
            <Text type="secondary">状态变更只提交选中的票项和退款原因；金额、状态和库存由后端计算。</Text>
          </div>
          <Tag color={canPartialRefund ? 'orange' : 'default'}>
            {canPartialRefund ? '可部分退款' : '当前不可部分退款'}
          </Tag>
        </Flex>
        <RefundStatePath
          isEligible={canPartialRefund}
          steps={['选择未使用票项', '提交 itemNos', '后端计算金额']}
        />
        <Checkbox.Group
          className="admin-partial-refund-items"
          onChange={(values) => onPartialRefundItemNosChange(values.map(String))}
          value={partialRefundItemNos}
        >
          {detail.items.map((item) => {
            const refundable = canPartialRefundItem(detail, item)

            return (
              <Checkbox
                className="admin-partial-refund-item"
                disabled={!refundable || isRefunding || isPartialRefunding}
                key={item.itemNo}
                value={item.itemNo}
              >
                <Space orientation="vertical" size={0}>
                  <Text>{item.itemNo}</Text>
                  <Text type="secondary">
                    {scenicTicketName(item.ticketName)} · {amountLabel(item.finalPrice)} · {itemStatusLabel(item.itemStatus)}
                  </Text>
                </Space>
              </Checkbox>
            )
          })}
        </Checkbox.Group>
        <Input.TextArea
          className="admin-partial-refund-reason-input"
          maxLength={100}
          onChange={(event) => onPartialRefundReasonChange(event.target.value)}
          placeholder="部分退款原因，选填，最多 100 字"
          rows={2}
          showCount
          value={partialRefundReason}
        />
        <Flex gap={8} justify="end" wrap>
          <Popconfirm
            cancelText="取消"
            disabled={!canSubmitPartialRefund}
            okText="确认部分退款"
            onConfirm={onPartialRefund}
            title="确认对选中票项执行部分退款？"
          >
            <Button
              className="admin-partial-refund-action"
              disabled={!canSubmitPartialRefund}
              icon={<UndoOutlined />}
              loading={isPartialRefunding}
            >
              部分退款
            </Button>
          </Popconfirm>
        </Flex>
      </div>
    </>
  )
}
