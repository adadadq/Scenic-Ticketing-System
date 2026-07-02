import { CheckCircleFilled } from '@ant-design/icons'
import { Alert, Button, Card, Divider, Flex, InputNumber, Tag, Typography } from 'antd'
import type { VisitorMe } from '../../../shared/api/types'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'
import type { BookingReadinessItem } from '../bookingFlow'
import type { TimeSlotOption } from '../types'
import { BookingGateAlert } from './BookingGateAlert'
import { BookingReadinessList } from './BookingReadinessList'

const { Text } = Typography

type SummaryRowProps = {
  label: string
  strong?: boolean
  value: string
}

function maskPhone(phone?: string) {
  return phone?.replace(/^(\d{3})\d{4}(\d{4})$/, '$1****$2') ?? ''
}

function SummaryRow({ label, strong, value }: SummaryRowProps) {
  return (
    <div className="summary-row">
      <Text type="secondary">{label}</Text>
      <Text className="summary-row-value breakable-text" strong={strong}>
        {value}
      </Text>
    </div>
  )
}

type OrderSummaryPanelProps = {
  canCreateOrder: boolean
  createOrderError: unknown
  isCreateOrderError: boolean
  isCreatingOrder: boolean
  onPrimaryAction: () => void
  onQuantityChange: (quantity: number) => void
  primaryActionDisabled: boolean
  primaryActionLabel: string
  quantity: number
  readinessItems: BookingReadinessItem[]
  selectedSlot?: TimeSlotOption
  selectedTicketName: string
  selectedVisitDate: string
  submitHint: string
  totalAmount: number
  visitor: VisitorMe | null
}

export function OrderSummaryPanel({
  canCreateOrder,
  createOrderError,
  isCreateOrderError,
  isCreatingOrder,
  onPrimaryAction,
  onQuantityChange,
  primaryActionDisabled,
  primaryActionLabel,
  quantity,
  readinessItems,
  selectedSlot,
  selectedTicketName,
  selectedVisitDate,
  submitHint,
  totalAmount,
  visitor,
}: OrderSummaryPanelProps) {
  const visitDate = selectedSlot?.visitDate ?? selectedVisitDate
  const timeSlotLabel = selectedSlot?.label ?? '未选择时段'
  const contactLabel = visitor ? `${visitor.visitorName} ${maskPhone(visitor.phone)}` : '未登录'

  return (
    <Card className="summary-card booking-summary-card" title="订单摘要">
      <div className="summary-section">
        <Flex align="center" justify="space-between">
          <Text className="summary-section-title">票种与游览</Text>
          <Tag color={selectedSlot ? 'green' : 'default'}>{selectedSlot ? '已选时段' : '待选时段'}</Tag>
        </Flex>
        <SummaryRow label="已选票种" strong value={selectedTicketName} />
        <SummaryRow label="游览日期" value={visitDate} />
        <SummaryRow label="游览时段" value={timeSlotLabel} />
      </div>

      <Divider />

      <div className="summary-section">
        <Flex align="center" justify="space-between">
          <Text className="summary-section-title">游客信息</Text>
          <Tag color={visitor?.isRegistered ? 'green' : visitor ? 'orange' : 'default'}>
            {visitor?.isRegistered ? '实名游客' : visitor ? '临时游客' : '未登录'}
          </Tag>
        </Flex>
        <SummaryRow label="联系人" value={contactLabel} />
      </div>

      <Divider />

      <div className="summary-section summary-total-section">
        <Flex align="center" justify="space-between">
          <Text className="summary-section-title">数量与金额</Text>
          <Flex align="center" gap={8}>
            <InputNumber min={1} max={8} value={quantity} onChange={(value) => onQuantityChange(value ?? 1)} />
            <Text type="secondary">张</Text>
          </Flex>
        </Flex>

        <Flex align="flex-end" justify="space-between">
          <Text>应付金额</Text>
          <Text className="total-price">¥{totalAmount}</Text>
        </Flex>
      </div>

      <BookingReadinessList items={readinessItems} />

      <Button
        block
        className="pay-button"
        disabled={primaryActionDisabled}
        icon={<CheckCircleFilled />}
        loading={isCreatingOrder}
        onClick={onPrimaryAction}
        size="large"
        type="primary"
      >
        {primaryActionLabel}
      </Button>

      <BookingGateAlert canCreateOrder={canCreateOrder} submitHint={submitHint} />

      {isCreateOrderError ? (
        <Alert
          className="summary-alert"
          showIcon
          type="error"
          title="订单创建失败"
          description={(
            <ApiErrorDetails
              error={createOrderError}
              fallback="订单创建失败，请稍后重试。"
              supportingText="如持续失败，请保留错误码和请求编号，便于后端定位库存、实名或会话问题。"
            />
          )}
        />
      ) : null}
    </Card>
  )
}
