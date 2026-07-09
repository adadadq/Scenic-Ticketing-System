import { Button, Form, Input } from 'antd'
import type { FormInstance } from 'antd'
import type { LoginFormValues } from '../types'

type LoginFormProps = {
  form: FormInstance<LoginFormValues>
  isPending: boolean
  onSubmit: (values: LoginFormValues) => void
}

export function LoginForm({ form, isPending, onSubmit }: LoginFormProps) {
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
        <Input autoComplete="username" placeholder="demo_visitor" maxLength={32} />
      </Form.Item>
      <Form.Item
        label="密码"
        name="password"
        rules={[
          { required: true, message: '请输入密码' },
          { min: 6, message: '密码至少 6 位' },
        ]}
      >
        <Input.Password autoComplete="current-password" placeholder="请输入密码" maxLength={72} />
      </Form.Item>
      <Button block htmlType="submit" loading={isPending} type="primary">
        登录
      </Button>
    </Form>
  )
}
