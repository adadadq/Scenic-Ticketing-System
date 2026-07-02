import { Button, Checkbox, Form, Input } from 'antd'
import type { FormInstance } from 'antd'
import { isValidIdCard, normalizeIdCard } from '../idCard'
import type { RegisterFormValues } from '../types'
import { normalizePhone } from '../utils'

type RegisterFormProps = {
  form: FormInstance<RegisterFormValues>
  isPending: boolean
  isSubmitEnabled: boolean
  onSubmit: (values: RegisterFormValues) => void
}

export function RegisterForm({ form, isPending, isSubmitEnabled, onSubmit }: RegisterFormProps) {
  return (
    <Form
      className="realname-register-form"
      form={form}
      initialValues={{ idType: 'ID_CARD', realNameConfirmed: false }}
      layout="vertical"
      onFinish={onSubmit}
      requiredMark={false}
    >
      <Form.Item
        label="姓名"
        name="visitorName"
        rules={[
          { required: true, message: '请输入姓名' },
          { min: 2, message: '姓名至少 2 个字符' },
        ]}
      >
        <Input placeholder="张三" maxLength={50} />
      </Form.Item>
      <Form.Item hidden name="idType">
        <Input />
      </Form.Item>
      <Form.Item
        label="身份证号"
        name="idNumber"
        rules={[
          { required: true, message: '请输入身份证号' },
          { pattern: /^\d{17}[\dXx]$/, message: '请输入 18 位身份证号' },
          {
            validator: async (_, value: string | undefined) => {
              if (!value || isValidIdCard(value)) {
                return
              }

              throw new Error('身份证日期或校验位不正确')
            },
          },
        ]}
        normalize={(value: string | undefined) => (value ? normalizeIdCard(value) : value)}
      >
        <Input placeholder="11010519491231002X" maxLength={20} />
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
      <Form.Item
        className="realname-confirm-item"
        name="realNameConfirmed"
        rules={[
          {
            validator: async (_, checked: boolean | undefined) => {
              if (checked) {
                return
              }

              throw new Error('请确认实名信息将用于购票和入园核验')
            },
          },
        ]}
        valuePropName="checked"
      >
        <Checkbox className="realname-confirm-checkbox">
          我确认实名信息真实有效，并同意用于购票和入园核验。
        </Checkbox>
      </Form.Item>
      <Button
        block
        className="realname-submit-button"
        disabled={!isSubmitEnabled}
        htmlType="submit"
        loading={isPending}
        type="primary"
      >
        完成实名登记
      </Button>
    </Form>
  )
}
