import { Button, Form, Input } from 'antd'
import type { FormInstance } from 'antd'
import type { LoginFormValues } from '../types'
import { normalizePhone } from '../utils'

type LoginFormProps = {
  form: FormInstance<LoginFormValues>
  isPending: boolean
  onSubmit: (values: LoginFormValues) => void
}

export function LoginForm({ form, isPending, onSubmit }: LoginFormProps) {
  return (
    <Form form={form} layout="vertical" onFinish={onSubmit} requiredMark={false}>
      <Form.Item
        label="手机号"
        name="phone"
        rules={[
          { required: true, message: '请输入手机号' },
          { pattern: /^1[3-9]\d{9}$/, message: '请输入 11 位中国大陆手机号' },
        ]}
        normalize={normalizePhone}
      >
        <Input placeholder="13911112222" inputMode="tel" maxLength={20} />
      </Form.Item>
      <Button block htmlType="submit" loading={isPending} type="primary">
        登录为临时游客
      </Button>
    </Form>
  )
}
