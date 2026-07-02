import { CalendarOutlined } from '@ant-design/icons'
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
        {visitDateOptions.map((day) => (
          <button
            className={day.value === selectedVisitDate ? 'date-chip active' : 'date-chip'}
            key={day.value}
            onClick={() => onSelectVisitDate(day.value)}
            type="button"
          >
            <CalendarOutlined />
            <span>{day.label}</span>
          </button>
        ))}
      </Flex>

      {hasTimeSlots ? (
        <div className="slot-grid">
          {timeSlots.map((slot) => {
            const isSelectedSlot = selectedSlot ? slotKey(slot) === slotKey(selectedSlot) : false

            return (
              <button
                className={`slot-card ${slot.tone} ${isSelectedSlot ? 'active' : ''}`}
                disabled={slot.tone === 'sold-out'}
                key={slotKey(slot)}
                onClick={() => onSelectSlot(slotKey(slot))}
                type="button"
              >
                <span>{slot.label}</span>
                <small>{slot.status}</small>
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
          title="时段接口暂不可用，当前展示演示时段"
          description={(
            <ApiErrorDetails
              error={timeSlotError}
              fallback="无法读取真实时段，请稍后重试。"
              supportingText="当前仅可浏览演示数据，不能创建订单；创建订单前需要真实时段与余票接口恢复。"
            />
          )}
        />
      ) : null}

      <Alert
        showIcon
        type="info"
        title="温馨提示"
        description="请提前预约购票，游览当日请携带有效身份证件入园。"
      />
    </Card>
  )
}
