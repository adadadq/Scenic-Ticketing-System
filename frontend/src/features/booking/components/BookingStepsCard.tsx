import { Card, Steps } from 'antd'

type BookingStepItem = {
  content: string
  title: string
}

type BookingStepsCardProps = {
  currentStep: number
  currentStepLabel: string
  items: BookingStepItem[]
}

export function BookingStepsCard({ currentStep, currentStepLabel, items }: BookingStepsCardProps) {
  return (
    <Card className="step-card booking-step-card">
      <Steps
        className="booking-steps"
        current={0}
        data-current-step={currentStep}
        data-current-step-label={currentStepLabel}
        responsive
        items={items}
      />
    </Card>
  )
}
