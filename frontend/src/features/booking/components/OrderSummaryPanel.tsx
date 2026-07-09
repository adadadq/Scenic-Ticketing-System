import { CheckCircleFilled } from '@ant-design/icons'
import { Alert, Button, Card, Divider, Flex, Tag, Typography } from 'antd'
import type { VisitorMe } from '../../../shared/api/types'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'
import type { BookingReadinessItem, BookingTicketSelection } from '../bookingFlow'
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
  onQuantityChange: (productKey: string, quantity: number) => void
  primaryActionDisabled: boolean
  primaryActionLabel: string
  readinessItems: BookingReadinessItem[]
  selectedTicketSelections: BookingTicketSelection[]
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
  readinessItems,
  selectedTicketSelections,
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
    <Card className="summary-card booking-summary-card" title="订单信息">
      <div className="summary-ticket-preview">
        <img src="/admin-login-landscape.png" alt="" />
        <span>
          <Text strong>{selectedTicketSelections.length > 1 ? `${selectedTicketSelections.length}种票` : selectedTicketName}</Text>
          <Text type="secondary">竹筏漂流 + 风景游览</Text>
        </span>
      </div>
      <div className="summary-section">
        <SummaryRow label="游览日期" value={visitDate} />
        <SummaryRow label="游览时段" value={timeSlotLabel} />
        <div className="summary-ticket-lines">
          {selectedTicketSelections.map(({ product, quantity }) => (
            <Flex align="center" className="summary-quantity-control" justify="space-between" key={product.key}>
              <span>
                <Text strong>{product.name}</Text>
                <Text type="secondary">¥ {product.salePrice}/人</Text>
              </span>
              <span className="summary-qty-stepper">
                <button disabled={quantity <= 0} onClick={() => onQuantityChange(product.key, quantity - 1)} type="button">-</button>
                <span>{quantity}</span>
                <button disabled={quantity >= 8} onClick={() => onQuantityChange(product.key, quantity + 1)} type="button">+</button>
              </span>
            </Flex>
          ))}
        </div>
      </div>

      <Divider />

      <div className="summary-section summary-total-section">
        <Flex align="flex-end" justify="space-between">
          <Text className="summary-section-title">订单金额</Text>
          <Text className="total-price">¥{totalAmount}</Text>
        </Flex>
      </div>

      <div className="summary-hidden-flow" aria-hidden="true">
        <div className="summary-section">
          <Flex align="center" justify="space-between">
            <Text className="summary-section-title">票种与游览</Text>
            <Tag color={selectedSlot ? 'green' : 'default'}>{selectedSlot ? '已选时段' : '待选时段'}</Tag>
          </Flex>
          <SummaryRow label="已选票种" strong value={selectedTicketName} />
        </div>

        <div className="summary-section">
          <Flex align="center" justify="space-between">
            <Text className="summary-section-title">游客信息</Text>
            <Tag color={visitor?.isRegistered ? 'green' : visitor ? 'orange' : 'default'}>
              {visitor?.isRegistered ? '已登录' : visitor ? '未注册' : '未登录'}
            </Tag>
          </Flex>
          <SummaryRow label="联系人" value={contactLabel} />
        </div>

        <SummaryRow label="游览日期" value={visitDate} />
        <SummaryRow label="游览时段" value={timeSlotLabel} />
        <BookingReadinessList items={readinessItems} />
      </div>

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
        <span className="pay-button-visual-label">{primaryActionLabel}</span>
      </Button>

      <div className="summary-hidden-flow">
        <BookingGateAlert canCreateOrder={canCreateOrder} submitHint={submitHint} />
      </div>

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
              supportingText="如多次失败，请联系客服并提供页面上的问题编号。"
            />
          )}
        />
      ) : null}
    </Card>
  )
}
