import {
  CheckCircleFilled,
  ClockCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import { Alert, Button, Flex, Popconfirm, Result, Tag, Typography } from 'antd'
import { useId, type ReactNode } from 'react'
import type { OrderDetail, OrderListItem } from '../types'
import { formatCurrency, formatPaymentDeadline, orderStatusColor } from '../utils'

const { Text } = Typography

type OrderDetailHeaderProps = {
  order: OrderListItem
}

export function OrderDetailHeader({ order }: OrderDetailHeaderProps) {
  return (
    <Flex className="order-detail-header" align="center" justify="space-between">
      <Text copyable strong>
        {order.orderNo}
      </Text>
      <Tag color={orderStatusColor(order.orderStatusTone)}>
        {order.orderStatusLabel}
      </Tag>
    </Flex>
  )
}

type OrderDetailFactsProps = {
  detail?: OrderDetail | null
  order: OrderListItem
}

type OrderDetailRowProps = {
  label: string
  strong?: boolean
  value: ReactNode
}

function OrderDetailRow({ label, strong, value }: OrderDetailRowProps) {
  return (
    <div className="order-detail-row">
      <Text className="order-detail-row-label" type="secondary">
        {label}
      </Text>
      <Text className="breakable-text order-detail-row-value" strong={strong}>
        {value}
      </Text>
    </div>
  )
}

export function OrderDetailFacts({ detail, order }: OrderDetailFactsProps) {
  const contactText = `${detail?.contactName ?? '详情加载中'} ${detail?.contactPhoneMasked ?? ''}`.trim()
  const sectionTitleId = useId()
  const tripTitleId = `${sectionTitleId}-trip`
  const contactTitleId = `${sectionTitleId}-contact`

  return (
    <div className="order-detail-facts">
      <section className="order-detail-section" aria-labelledby={tripTitleId}>
        <Text className="order-detail-section-title" id={tripTitleId}>
          票品与游览
        </Text>
        <OrderDetailRow label="票品" value={detail?.productName ?? '详情加载中'} strong />
        <OrderDetailRow label="票种" value={detail?.ticketName ?? '详情加载中'} />
        <OrderDetailRow label="游览日期" value={order.visitDate || '详情中查看'} />
        <OrderDetailRow label="游览时段" value={order.timeSlotLabel} />
      </section>

      <section className="order-detail-section" aria-labelledby={contactTitleId}>
        <Text className="order-detail-section-title" id={contactTitleId}>
          联系人与下单
        </Text>
        <OrderDetailRow label="联系人" value={contactText} />
        <OrderDetailRow label="数量" value={`${order.itemCount} 张`} />
        <OrderDetailRow label="下单时间" value={order.orderTime} />
      </section>
    </div>
  )
}

type OrderDetailStateCardProps = {
  canCancel: boolean
  canPay: boolean
  isPaymentBlocked: boolean
  order: OrderListItem
  paymentSucceeded: boolean
  ticketCodes: string[]
}

function getOrderDetailStateCard({
  canCancel,
  canPay,
  isPaymentBlocked,
  order,
  paymentSucceeded,
  ticketCodes,
}: OrderDetailStateCardProps) {
  if (paymentSucceeded || ticketCodes.length > 0) {
    return {
      detail: '入园时出示下方票码；已支付订单不再显示取消入口。',
      icon: <CheckCircleFilled />,
      label: '票码可用',
      tag: '看票码',
      tone: 'success',
    }
  }

  if (isPaymentBlocked) {
    return {
      detail: '订单状态可能已更新，请刷新后再继续操作。',
      icon: <InfoCircleOutlined />,
      label: '状态待刷新',
      tag: '需确认',
      tone: 'warning',
    }
  }

  if (order.orderStatus === 'CANCELLED') {
    return {
      detail: '订单已取消，只能查看记录；已取消订单不会生成入园票码。',
      icon: <CloseCircleOutlined />,
      label: '只读订单',
      tag: '不可操作',
      tone: 'default',
    }
  }

  if (canPay || canCancel) {
    return {
      detail: '可继续支付，或在支付前取消订单；余票以支付结果为准。',
      icon: <ClockCircleOutlined />,
      label: '待支付处理',
      tag: '可操作',
      tone: 'processing',
    }
  }

  if (order.paymentStatus === 'PAID') {
    return {
      detail: '订单已支付，票码生成后可在详情中查看。',
      icon: <CheckCircleFilled />,
      label: '已支付',
      tag: '只读',
      tone: 'success',
    }
  }

  return {
    detail: '订单状态以页面显示为准，如有疑问请联系客服。',
    icon: <InfoCircleOutlined />,
    label: '详情只读',
    tag: '只读',
    tone: 'default',
  }
}

export function OrderDetailStateCard(props: OrderDetailStateCardProps) {
  const stateCard = getOrderDetailStateCard(props)

  return (
    <section className={`order-detail-state-card is-${stateCard.tone}`} aria-label="订单详情状态">
      <span className="order-detail-state-icon" aria-hidden="true">
        {stateCard.icon}
      </span>
      <div className="order-detail-state-copy">
        <Flex align="center" justify="space-between" gap={8}>
          <Text strong>{stateCard.label}</Text>
          <Tag color={stateCard.tone}>{stateCard.tag}</Tag>
        </Flex>
        <Text type="secondary">{stateCard.detail}</Text>
      </div>
    </section>
  )
}

type OrderPaymentSummaryProps = {
  canPay: boolean
  order: OrderListItem
}

export function OrderPaymentSummary({ canPay, order }: OrderPaymentSummaryProps) {
  return (
    <section className="order-payment-summary" aria-label="订单金额">
      <Flex align="flex-end" justify="space-between" gap={12}>
        <Text>应付金额</Text>
        <Text className="total-price">{formatCurrency(order.payableAmount)}</Text>
      </Flex>

      {canPay ? (
        <div className="payment-deadline-note">
          <ClockCircleOutlined />
          <Text>{formatPaymentDeadline(order.orderTime)}</Text>
        </div>
      ) : null}
    </section>
  )
}

type OrderTicketCodeSectionProps = {
  canPay: boolean
  order: OrderListItem
  paymentSucceeded: boolean
  ticketCodes: string[]
}

function getTicketEmptyState(canPay: boolean, order: OrderListItem) {
  if (canPay) {
    return {
      description: '完成支付后会生成票码。',
      title: '订单待支付',
      type: 'warning' as const,
    }
  }

  if (order.orderStatus === 'CANCELLED') {
    return {
      description: '已取消订单不会生成入园票码，可保留订单号用于客服查询。',
      title: '订单已取消',
      type: 'info' as const,
    }
  }

  if (order.paymentStatus === 'PAID') {
    return {
      description: '当前已支付订单暂未返回可出示票码，请刷新订单或联系码头。',
      title: '暂无可出示票码',
      type: 'info' as const,
    }
  }

  return {
    description: '只有已支付且已出票的订单会在这里展示入园凭证。',
    title: '暂无票码',
    type: 'info' as const,
  }
}

export function OrderTicketCodeSection({ canPay, order, paymentSucceeded, ticketCodes }: OrderTicketCodeSectionProps) {
  const emptyState = getTicketEmptyState(canPay, order)

  return (
    <>
      {paymentSucceeded ? (
        <Result
          className="payment-success-result"
          status="success"
          subTitle="请在入园时出示下方票码。"
          title="支付成功，票码已生成"
        />
      ) : null}

      {ticketCodes.length > 0 ? (
        <div className="ticket-code-list">
          <span className="ticket-code-qr" aria-hidden="true" />
          <div className="ticket-code-copy">
            <Text className="order-detail-section-title">入园票码（凭此码入园）</Text>
            {ticketCodes.map((code) => (
              <Tag color="green" key={code}>
                <span className="ticket-code-text">{code}</span>
              </Tag>
            ))}
            <Text type="secondary">有效期：{order.visitDate || '游玩当日'} {order.timeSlotLabel}</Text>
          </div>
        </div>
      ) : (
        <Alert
          showIcon
          type={emptyState.type}
          title={emptyState.title}
          description={emptyState.description}
        />
      )}
    </>
  )
}

type OrderDetailActionBarProps = {
  canCancel: boolean
  canPay: boolean
  canSubmitPayment: boolean
  isCanceling: boolean
  isPaying: boolean
  isPaymentBlocked: boolean
  onCancelOrder: () => void
  onPayOrder: () => void
}

export function OrderDetailActionBar({
  canCancel,
  canPay,
  canSubmitPayment,
  isCanceling,
  isPaying,
  isPaymentBlocked,
  onCancelOrder,
  onPayOrder,
}: OrderDetailActionBarProps) {
  return (
    <Flex className="order-detail-actions" gap={10} wrap>
      <Button
        disabled={!canSubmitPayment || isCanceling}
        icon={canSubmitPayment ? <CheckCircleFilled /> : <ClockCircleOutlined />}
        loading={isPaying}
        onClick={onPayOrder}
        size="large"
        type="primary"
      >
        {isPaymentBlocked ? '不可支付' : canPay ? '继续支付' : '无需支付'}
      </Button>
      <Popconfirm
        cancelText="先不取消"
        disabled={!canCancel}
        getPopupContainer={(triggerNode) => triggerNode.parentElement ?? document.body}
        okButtonProps={{ danger: true }}
        okText="确认取消"
        onConfirm={onCancelOrder}
        title="确认取消这笔待支付订单？"
      >
        <Button
          danger
          disabled={!canCancel || isPaying}
          icon={<CloseCircleOutlined />}
          loading={isCanceling}
          size="large"
        >
          取消订单
        </Button>
      </Popconfirm>
    </Flex>
  )
}
