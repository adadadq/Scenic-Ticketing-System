import { Alert } from 'antd'

type BookingGateAlertProps = {
  canCreateOrder: boolean
  submitHint: string
}

export function BookingGateAlert({ canCreateOrder, submitHint }: BookingGateAlertProps) {
  return <Alert className="summary-alert" showIcon type={canCreateOrder ? 'success' : 'warning'} title={submitHint} />
}
