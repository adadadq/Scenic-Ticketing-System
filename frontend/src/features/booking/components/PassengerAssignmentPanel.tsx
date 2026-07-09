import { DeleteOutlined, EditOutlined, PlusOutlined, UserAddOutlined } from '@ant-design/icons'
import { Alert, Button, Card, Empty, Form, Input, List, Modal, Select, Space, Typography, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { formatApiError } from '../../../shared/api/client'
import type { PassengerTemplate, PassengerTemplateRequest } from '../../../shared/api/types'
import type { BookingPassengerDraft, BookingPassengerLine } from '../bookingFlow'

const { Text } = Typography

type PassengerAssignmentPanelProps = {
  drafts: Record<string, BookingPassengerDraft>
  isTemplateLoading: boolean
  lines: BookingPassengerLine[]
  onCreateTemplate: (body: PassengerTemplateRequest) => Promise<unknown>
  onDeleteTemplate: (templateId: number) => Promise<unknown>
  onDraftChange: (lineKey: string, draft: BookingPassengerDraft) => void
  onUpdateTemplate: (templateId: number, body: PassengerTemplateRequest) => Promise<unknown>
  templates: PassengerTemplate[]
}

const defaultDraft: BookingPassengerDraft = {
  idNumber: '',
  idType: 'ID_CARD',
  passengerName: '',
  phone: '',
}

function toDraft(template: PassengerTemplate): BookingPassengerDraft {
  return {
    idNumber: template.idNumber,
    idType: template.idType,
    passengerName: template.passengerName,
    phone: template.phone,
    templateId: template.templateId,
  }
}

export function PassengerAssignmentPanel({
  drafts,
  isTemplateLoading,
  lines,
  onCreateTemplate,
  onDeleteTemplate,
  onDraftChange,
  onUpdateTemplate,
  templates,
}: PassengerAssignmentPanelProps) {
  const [isManagerOpen, setIsManagerOpen] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<PassengerTemplate | null>(null)
  const [form] = Form.useForm<PassengerTemplateRequest>()
  const [messageApi, messageContext] = message.useMessage()
  const templateOptions = useMemo(
    () => templates.map((template) => ({
      label: `${template.passengerName} ${template.idNumber.slice(-4)}`,
      value: template.templateId,
    })),
    [templates],
  )

  useEffect(() => {
    if (editingTemplate) {
      form.setFieldsValue({
        idNumber: editingTemplate.idNumber,
        idType: editingTemplate.idType,
        passengerName: editingTemplate.passengerName,
        phone: editingTemplate.phone,
      })
    } else {
      form.setFieldsValue(defaultDraft)
    }
  }, [editingTemplate, form])

  function updateLine(lineKey: string, patch: Partial<BookingPassengerDraft>) {
    const current = drafts[lineKey] ?? defaultDraft
    onDraftChange(lineKey, {
      ...current,
      ...patch,
      templateId: patch.templateId ?? undefined,
    })
  }

  async function handleTemplateSubmit(values: PassengerTemplateRequest) {
    try {
      if (editingTemplate) {
        await onUpdateTemplate(editingTemplate.templateId, values)
      } else {
        await onCreateTemplate(values)
      }
      messageApi.success(editingTemplate ? '出行人已更新' : '出行人已新增')
      setEditingTemplate(null)
      form.resetFields()
    } catch (error) {
      messageApi.error(formatApiError(error, '保存失败，请检查姓名、证件号码和手机号。'))
    }
  }

  return (
    <>
      {messageContext}
      <Card
        className="workspace-card booking-passenger-card"
        extra={<Button icon={<UserAddOutlined />} onClick={() => setIsManagerOpen(true)} type="link">常用出行人</Button>}
        title="出行人信息"
      >
      {lines.length === 0 ? (
        <Empty description="选择票种后填写出行人" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <div className="passenger-line-list">
          {lines.map((line) => {
            const draft = drafts[line.key] ?? defaultDraft

            return (
              <div className="passenger-line" key={line.key}>
                <div className="passenger-line-title">
                  <Text strong>{line.label}</Text>
                  <Select
                    allowClear
                    className="passenger-template-select"
                    loading={isTemplateLoading}
                    onChange={(templateId) => {
                      const template = templates.find((item) => item.templateId === templateId)
                      onDraftChange(line.key, template ? toDraft(template) : defaultDraft)
                    }}
                    options={templateOptions}
                    placeholder="选择常用出行人"
                    value={draft.templateId}
                  />
                </div>
                <div className="passenger-field-grid">
                  <Input
                    aria-label={`${line.label}姓名`}
                    onChange={(event) => updateLine(line.key, { passengerName: event.target.value })}
                    placeholder="姓名"
                    value={draft.passengerName}
                  />
                  <Input
                    aria-label={`${line.label}身份证号`}
                    onChange={(event) => updateLine(line.key, { idNumber: event.target.value })}
                    placeholder="身份证号"
                    value={draft.idNumber}
                  />
                  <Input
                    aria-label={`${line.label}手机号`}
                    maxLength={11}
                    onChange={(event) => updateLine(line.key, { phone: event.target.value })}
                    placeholder="手机号"
                    value={draft.phone}
                  />
                </div>
              </div>
            )
          })}
        </div>
      )}

      <Alert
        className="passenger-helper"
        showIcon
        type="info"
        message="同一出行人在同一票种和时段只能购买一次，新填写的信息会在提交订单时保存为常用出行人。"
      />

      <Modal
        footer={null}
        onCancel={() => setIsManagerOpen(false)}
        open={isManagerOpen}
        title="常用出行人"
        width={720}
      >
        <div className="passenger-template-manager">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleTemplateSubmit}
            onFinishFailed={({ errorFields }) => {
              messageApi.warning(errorFields[0]?.errors[0] ?? '请补全出行人信息')
            }}
          >
            <div className="passenger-template-form-grid">
              <Form.Item label="姓名" name="passengerName" rules={[{ required: true, message: '请输入姓名' }]}>
                <Input placeholder="姓名" />
              </Form.Item>
              <Form.Item label="证件类型" name="idType" rules={[{ required: true }]}>
                <Select options={[{ label: '身份证', value: 'ID_CARD' }]} />
              </Form.Item>
              <Form.Item
                label="证件号码"
                name="idNumber"
                rules={[
                  { required: true, message: '请输入证件号码' },
                  { min: 6, message: '证件号码至少 6 位' },
                ]}
              >
                <Input placeholder="证件号码" />
              </Form.Item>
              <Form.Item
                label="手机号"
                name="phone"
                rules={[
                  { required: true, message: '请输入手机号' },
                  { pattern: /^1\d{10}$/, message: '请输入 11 位手机号' },
                ]}
              >
                <Input maxLength={11} placeholder="手机号" />
              </Form.Item>
            </div>
            <Space>
              <Button htmlType="submit" icon={<PlusOutlined />} type="primary">
                {editingTemplate ? '保存修改' : '新增出行人'}
              </Button>
              {editingTemplate ? <Button onClick={() => setEditingTemplate(null)}>取消编辑</Button> : null}
            </Space>
          </Form>

          <List
            className="passenger-template-list"
            dataSource={templates}
            loading={isTemplateLoading}
            locale={{ emptyText: '暂无常用出行人' }}
            renderItem={(template) => (
              <List.Item
                actions={[
                  <Button icon={<EditOutlined />} key="edit" onClick={() => setEditingTemplate(template)} type="text" />,
                  <Button danger icon={<DeleteOutlined />} key="delete" onClick={() => onDeleteTemplate(template.templateId)} type="text" />,
                ]}
              >
                <List.Item.Meta
                  title={template.passengerName}
                  description={`${template.idNumber} / ${template.phone}`}
                />
              </List.Item>
            )}
          />
        </div>
      </Modal>
      </Card>
    </>
  )
}
