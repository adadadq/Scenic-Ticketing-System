import { Button, Form, Input } from 'antd'
import type { FormInstance } from 'antd'
import type { RegisterFormValues } from '../types'
import { normalizePhone } from '../utils'

type RegisterFormProps = {
  form: FormInstance<RegisterFormValues>
  isPending: boolean
  onSubmit: (values: RegisterFormValues) => void
}

export function RegisterForm({ form, isPending, onSubmit }: RegisterFormProps) {
  return (
    <Form form={form} layout="vertical" onFinish={onSubmit} requiredMark={false}>
      <Form.Item
        label="账号"
        name="username"
        rules={[
          { required: true, message: '请输入账号' },
          { pattern: /^[A-Za-z0-9_]{3,32}$/, message: '账号为 3-32 位字母、数字或下划线' },
        ]}
      >
        <Input autoComplete="username" placeholder="例如 yulong_001" maxLength={32} />
      </Form.Item>
      <Form.Item
        label="密码"
        name="password"
        rules={[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少 6 位' },
        ]}
      >
        <Input.Password autoComplete="new-password" placeholder="至少 6 位" maxLength={72} />
      </Form.Item>
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
        注册
      </Button>
    </Form>
  )
}
