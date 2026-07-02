import { CheckCircleFilled } from '@ant-design/icons'
import { Button, Typography } from 'antd'

const { Text } = Typography

type BookingMobileActionBarProps = {
  disabled: boolean
  isLoading: boolean
  label: string
  onPrimaryAction: () => void
  quantity: number
  selectedTicketName: string
  totalAmount: number
}

export function BookingMobileActionBar({
  disabled,
  isLoading,
  label,
  onPrimaryAction,
  quantity,
  selectedTicketName,
  totalAmount,
}: BookingMobileActionBarProps) {
  return (
    <div className="mobile-action-bar">
      <div>
        <Text type="secondary">已选：{selectedTicketName} × {quantity}</Text>
        <Text className="mobile-total">¥{totalAmount}</Text>
      </div>
      <Button
        disabled={disabled}
        icon={<CheckCircleFilled />}
        loading={isLoading}
        onClick={onPrimaryAction}
        size="large"
        type="primary"
      >
        {label}
      </Button>
    </div>
  )
}
