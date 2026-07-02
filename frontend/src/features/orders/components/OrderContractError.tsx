import { Alert } from 'antd'
import type { AlertProps } from 'antd'
import type { ReactNode } from 'react'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'

type OrderContractErrorProps = {
  action?: ReactNode
  error: unknown
  fallback: string
  supportingText?: string
  title: string
  type?: AlertProps['type']
}

export function OrderContractError({
  action,
  error,
  fallback,
  supportingText,
  title,
  type = 'error',
}: OrderContractErrorProps) {
  return (
    <Alert
      action={action}
      className="order-contract-error"
      showIcon
      type={type}
      title={title}
      description={<ApiErrorDetails error={error} fallback={fallback} supportingText={supportingText} />}
    />
  )
}
