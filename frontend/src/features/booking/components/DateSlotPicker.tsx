import { LeftOutlined, RightOutlined } from '@ant-design/icons'
import { Alert, Card, Empty, Flex } from 'antd'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'
import type { TimeSlotOption } from '../types'
import { slotKey } from '../utils'

type VisitDateOption = {
  label: string
  value: string
}

type DateSlotPickerProps = {
  isLoading: boolean
  onSelectSlot: (slotKey: string) => void
  onSelectVisitDate: (visitDate: string) => void
  selectedSlot?: TimeSlotOption
  selectedVisitDate: string
  timeSlotError: unknown
  timeSlots: TimeSlotOption[]
  usesTimeSlotFallback: boolean
  visitDateOptions: VisitDateOption[]
}

export function DateSlotPicker({
  isLoading,
  onSelectSlot,
  onSelectVisitDate,
  selectedSlot,
  selectedVisitDate,
  timeSlotError,
  timeSlots,
  usesTimeSlotFallback,
  visitDateOptions,
}: DateSlotPickerProps) {
  const hasTimeSlots = timeSlots.length > 0

  return (
    <Card title="选择游览日期和时段" className="workspace-card booking-slot-card">
      <Flex className="date-strip" gap={10} wrap>
        <button className="date-nav-chip" type="button" aria-label="上一组日期">
          <LeftOutlined />
        </button>
        {visitDateOptions.map((day) => (
          <button
            className={day.value === selectedVisitDate ? 'date-chip active' : 'date-chip'}
            key={day.value}
            onClick={() => onSelectVisitDate(day.value)}
            type="button"
          >
            <span>{day.label}</span>
          </button>
        ))}
        <button className="date-nav-chip" type="button" aria-label="下一组日期">
          <RightOutlined />
        </button>
      </Flex>

      {hasTimeSlots ? (
        <div className="slot-grid">
          {timeSlots.map((slot) => {
            const isSelectedSlot = selectedSlot ? slotKey(slot) === slotKey(selectedSlot) : false
            const statusText = 'remainingQuota' in slot && slot.remainingQuota
              ? `余票 ${slot.remainingQuota}`
              : slot.status

            return (
              <button
                className={`slot-card ${slot.tone} ${isSelectedSlot ? 'active' : ''}`}
                disabled={slot.tone === 'sold-out'}
                key={slotKey(slot)}
                onClick={() => onSelectSlot(slotKey(slot))}
                type="button"
              >
                <span>{slot.label}</span>
                <small>{statusText}</small>
              </button>
            )
          })}
        </div>
      ) : (
        <div className="booking-empty-panel">
          <Empty
            description={isLoading ? '时段加载中' : '当前日期暂无可预约时段，请换一天查看'}
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </div>
      )}

      {usesTimeSlotFallback ? (
        <Alert
          className="catalog-alert"
          showIcon
          type="warning"
          title="暂时无法提交订单"
          description={(
            <ApiErrorDetails
              error={timeSlotError}
              fallback="预约时段暂时不稳定，请稍后重试。"
              supportingText="当前可先查看时段，提交订单请稍后再试。"
            />
          )}
        />
      ) : null}

      <Alert
        className="booking-tip-alert"
        showIcon
        type="info"
        title="温馨提示：竹筏漂流请提前30分钟到达码头，带好身份证或可核验证件，注意防晒和安全。"
      />
    </Card>
  )
}
