import {
  CheckCircleFilled,
  ClockCircleFilled,
  ExclamationCircleFilled,
} from '@ant-design/icons'
import { Flex, Tag, Typography } from 'antd'
import type { BookingReadinessItem, BookingReadinessStatus } from '../bookingFlow'

const { Text } = Typography

const readinessMeta: Record<BookingReadinessStatus, { label: string, tone: string }> = {
  active: { label: '待完成', tone: 'processing' },
  blocked: { label: '不可下单', tone: 'warning' },
  done: { label: '已完成', tone: 'success' },
}

function ReadinessIcon({ status }: { status: BookingReadinessStatus }) {
  if (status === 'done') {
    return <CheckCircleFilled />
  }

  if (status === 'blocked') {
    return <ExclamationCircleFilled />
  }

  return <ClockCircleFilled />
}

type BookingReadinessListProps = {
  items: BookingReadinessItem[]
}

export function BookingReadinessList({ items }: BookingReadinessListProps) {
  return (
    <div className="booking-readiness">
      <Flex align="center" justify="space-between">
        <Text className="summary-section-title">下单前确认</Text>
        <Text type="secondary">确认信息后再提交</Text>
      </Flex>

      <div className="booking-readiness-list">
        {items.map((item) => {
          const meta = readinessMeta[item.status]

          return (
            <div className={`booking-readiness-item is-${item.status}`} key={item.key}>
              <span className="booking-readiness-icon" aria-hidden="true">
                <ReadinessIcon status={item.status} />
              </span>
              <div className="booking-readiness-copy">
                <Flex align="center" justify="space-between" gap={8}>
                  <Text strong>{item.label}</Text>
                  <Tag color={meta.tone}>{meta.label}</Tag>
                </Flex>
                <Text className="breakable-text" type="secondary">
                  {item.detail}
                </Text>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
