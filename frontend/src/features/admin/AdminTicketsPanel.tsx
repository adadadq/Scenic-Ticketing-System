import {
  CloseOutlined,
  DeleteOutlined,
  DownOutlined,
  EditOutlined,
  PlusOutlined,
  SearchOutlined,
  SunOutlined,
} from '@ant-design/icons'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Empty, Form, Input, InputNumber, Popconfirm, Radio, Select, Tag, Typography, message } from 'antd'
import { useEffect, useMemo, useState } from 'react'
import { adminTicketsApi } from '../../shared/api/endpoints'
import { formatApiError } from '../../shared/api/errors'
import type { AdminTicket, AdminTicketSaveRequest, AdminTicketSlotQuota, AdminTicketStatus } from '../../shared/api/types'
import { AdminNoticeButton } from './components/AdminNoticeButton'

const { Text, Title } = Typography

type TicketFormValues = {
  dateFrom?: string
  dateTo?: string
  description?: string
  name: string
  route: string
  salePrice: number
  slotQuota: number
  slotQuotas: AdminTicketSlotQuota[]
  status: TicketStatus
  stock: number
  type: string
}

const typeOptions = ['竹筏漂流票', '景区优惠票']
const routeOptions = ['遇龙河竹筏漂流（精华段）', '金龙桥至旧县成人票', '遇龙河经典竹筏漂流线路']
const scenicImage = '/admin-login-landscape.png'
type TicketStatus = AdminTicketStatus
type TicketEditorMode = 'idle' | 'create' | 'edit'
const defaultSlotQuotas: AdminTicketSlotQuota[] = [
  { slotStartTime: '08:30', slotEndTime: '10:30', quota: 40 },
  { slotStartTime: '10:30', slotEndTime: '12:30', quota: 40 },
  { slotStartTime: '12:30', slotEndTime: '13:30', quota: 40 },
  { slotStartTime: '13:30', slotEndTime: '15:30', quota: 40 },
  { slotStartTime: '15:30', slotEndTime: '17:30', quota: 40 },
  { slotStartTime: '17:30', slotEndTime: '18:30', quota: 40 },
]

function slotQuotasFrom(slotQuota: number, slotQuotas?: AdminTicketSlotQuota[]) {
  const quotaByTime = new Map(slotQuotas?.map((slot) => [`${slot.slotStartTime}-${slot.slotEndTime}`, slot.quota]))
  return defaultSlotQuotas.map((slot) => ({
    ...slot,
    quota: quotaByTime.get(`${slot.slotStartTime}-${slot.slotEndTime}`) ?? slotQuota,
  }))
}

const seedTickets: AdminTicket[] = [
  {
    allocatedQuota: 4860,
    dateFrom: new Date().toISOString().slice(0, 10),
    dateTo: new Date(Date.now() + 6 * 86400000).toISOString().slice(0, 10),
    description: '适用于18周岁（含）以上游客，含竹筏漂流与沿途风景游览。',
    id: 10,
    name: '成人票',
    route: routeOptions[0],
    salePrice: '128.00',
    slotQuota: 40,
    slotQuotas: slotQuotasFrom(40),
    status: 'ON_SALE',
    stock: 5000,
    type: '竹筏漂流票',
  },
  {
    allocatedQuota: 2890,
    dateFrom: new Date().toISOString().slice(0, 10),
    dateTo: new Date(Date.now() + 6 * 86400000).toISOString().slice(0, 10),
    description: '适用于儿童游客，需与成人同行并携带有效证件。',
    id: 11,
    name: '儿童票',
    route: routeOptions[0],
    salePrice: '68.00',
    slotQuota: 20,
    slotQuotas: slotQuotasFrom(20),
    status: 'ON_SALE',
    stock: 3000,
    type: '竹筏漂流票',
  },
  {
    allocatedQuota: 0,
    dateFrom: new Date().toISOString().slice(0, 10),
    dateTo: new Date(Date.now() + 6 * 86400000).toISOString().slice(0, 10),
    description: '适用于符合优待规则的游客，窗口核验证件后使用。',
    id: 12,
    name: '优惠票',
    route: routeOptions[1],
    salePrice: '98.00',
    slotQuota: 18,
    slotQuotas: slotQuotasFrom(18),
    status: 'OFF_SALE',
    stock: 2000,
    type: '景区优惠票',
  },
  {
    allocatedQuota: 3720,
    dateFrom: new Date().toISOString().slice(0, 10),
    dateTo: new Date(Date.now() + 6 * 86400000).toISOString().slice(0, 10),
    description: '适用于遇龙河经典竹筏漂流线路，按预约时段核验。',
    id: 13,
    name: '竹筏漂流',
    route: routeOptions[2],
    salePrice: '256.00',
    slotQuota: 35,
    slotQuotas: slotQuotasFrom(35),
    status: 'ON_SALE',
    stock: 4000,
    type: '竹筏漂流票',
  },
]

function toFormValues(ticket: AdminTicket): TicketFormValues {
  return {
    description: ticket.description ?? undefined,
    dateFrom: ticket.dateFrom ?? undefined,
    dateTo: ticket.dateTo ?? undefined,
    name: ticket.name,
    route: ticket.route,
    salePrice: Number(ticket.salePrice),
    slotQuota: ticket.slotQuota,
    slotQuotas: slotQuotasFrom(ticket.slotQuota, ticket.slotQuotas),
    status: ticket.status,
    stock: ticket.stock,
    type: ticket.type,
  }
}

function today(offset = 0) {
  return new Date(Date.now() + offset * 86400000).toISOString().slice(0, 10)
}

function audienceFor(ticket: AdminTicket) {
  if (ticket.name.includes('儿童')) return '6周岁（含）- 18周岁（不含）'
  if (ticket.name.includes('优惠')) return '符合景区优待规则'
  return '18周岁（含）以上'
}

function tagsFor(ticket: AdminTicket) {
  return ticket.type === '竹筏漂流票' ? ['竹筏漂流', '风景游览'] : ['优待票']
}

export function AdminTicketsPanel() {
  const [form] = Form.useForm<TicketFormValues>()
  const [messageApi, messageContext] = message.useMessage()
  const queryClient = useQueryClient()
  const ticketsQuery = useQuery({ queryKey: ['admin-tickets'], queryFn: adminTicketsApi.list })
  const saveTicketMutation = useMutation({
    mutationFn: ({ id, values }: { action: 'save' | 'toggle'; id?: number; values: AdminTicketSaveRequest }) =>
      id ? adminTicketsApi.update(id, values) : adminTicketsApi.create(values),
    onSuccess: (ticket, variables) => {
      setEditingTicket(ticket)
      setEditorMode('edit')
      messageApi.success(variables.action === 'toggle' ? '票种状态已更新' : '票种保存成功')
      queryClient.invalidateQueries({ queryKey: ['admin-tickets'] })
      queryClient.invalidateQueries({ queryKey: ['booking'] })
    },
    onError: (error, variables) => {
      const fallback = variables.action === 'toggle'
        ? '票种状态更新失败，请确认管理员登录状态后重试。'
        : '票种保存失败，请确认管理员登录状态后重试。'
      messageApi.error(formatApiError(error, fallback))
    },
  })
  const deleteTicketMutation = useMutation({
    mutationFn: adminTicketsApi.delete,
    onSuccess: () => {
      setEditingTicket(null)
      setEditorMode('idle')
      messageApi.success('票种已删除')
      queryClient.invalidateQueries({ queryKey: ['admin-tickets'] })
      queryClient.invalidateQueries({ queryKey: ['booking'] })
    },
    onError: (error) => {
      messageApi.error(formatApiError(error, '票种删除失败，请稍后重试。'))
    },
  })
  const tickets = ticketsQuery.isSuccess ? ticketsQuery.data : seedTickets
  const [editingTicket, setEditingTicket] = useState<AdminTicket | null>(null)
  const [editorMode, setEditorMode] = useState<TicketEditorMode>('idle')
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<TicketStatus | 'ALL'>('ALL')

  useEffect(() => {
    if (editorMode === 'edit' && editingTicket && ticketsQuery.data?.length && !ticketsQuery.data.some((ticket) => ticket.id === editingTicket.id)) {
      setEditingTicket(null)
      setEditorMode('idle')
    }
  }, [editingTicket, editorMode, ticketsQuery.data])

  useEffect(() => {
    if (editorMode === 'edit' && editingTicket) {
      form.setFieldsValue(toFormValues(editingTicket))
      return
    }

    if (editorMode !== 'create') return

    form.setFieldsValue({
      description: '',
      dateFrom: today(),
      dateTo: today(6),
      name: '',
      route: routeOptions[0],
      salePrice: 128,
      slotQuota: 40,
      slotQuotas: slotQuotasFrom(40),
      status: 'ON_SALE',
      stock: 5000,
      type: typeOptions[0],
    })
  }, [editingTicket, editorMode, form])

  const filteredTickets = useMemo(() => {
    const keyword = query.trim()
    return tickets.filter((ticket) =>
      (!keyword || ticket.name.includes(keyword) || ticket.type.includes(keyword) || ticket.route.includes(keyword)) &&
      (statusFilter === 'ALL' || ticket.status === statusFilter)
    )
  }, [query, statusFilter, tickets])

  function openCreateEditor() {
    setEditingTicket(null)
    setEditorMode('create')
  }

  function openEditEditor(ticket: AdminTicket) {
    setEditingTicket(ticket)
    setEditorMode('edit')
  }

  function closeEditor() {
    setEditingTicket(null)
    setEditorMode('idle')
  }

  function saveTicket(values: TicketFormValues) {
    const slotQuotas = slotQuotasFrom(values.slotQuota, values.slotQuotas)
    saveTicketMutation.mutate({
      action: 'save',
      id: editorMode === 'edit' ? editingTicket?.id : undefined,
      values: {
        ...values,
        dateFrom: values.dateFrom,
        dateTo: values.dateTo,
        description: values.description ?? '',
        slotQuota: slotQuotas[0]?.quota ?? values.slotQuota,
        slotQuotas,
      },
    })
  }

  function toggleStatus(ticket: AdminTicket) {
    saveTicketMutation.mutate({
      action: 'toggle',
      id: ticket.id,
      values: {
        dateFrom: ticket.dateFrom ?? today(),
        dateTo: ticket.dateTo ?? today(6),
        description: ticket.description ?? '',
        name: ticket.name,
        route: ticket.route,
        salePrice: Number(ticket.salePrice),
        slotQuota: ticket.slotQuota,
        slotQuotas: slotQuotasFrom(ticket.slotQuota, ticket.slotQuotas),
        status: ticket.status === 'ON_SALE' ? 'OFF_SALE' : 'ON_SALE',
        stock: ticket.stock,
        type: ticket.type,
      },
    })
  }

  function deleteTicket(ticket: AdminTicket) {
    deleteTicketMutation.mutate(ticket.id)
  }

  return (
    <section className="admin-ticket-page">
      {messageContext}
      <div className="admin-ticket-hero">
        <div className="admin-ticket-hero-copy">
          <Title level={1}>票种管理</Title>
          <Text>管理景区所有票种信息，设置价格、库存及销售状态</Text>
          <span className="admin-ticket-hero-mark" />
        </div>
        <div className="admin-dashboard-top-actions">
          <div className="admin-weather-card">
            <SunOutlined />
            <span>晴 26°C</span>
            <Text>2026-06-28 16:04</Text>
          </div>
          <AdminNoticeButton />
          <button className="admin-profile-button" type="button">
            <span className="admin-profile-avatar" />
            <strong>演示管理员</strong>
            <DownOutlined />
          </button>
        </div>
      </div>

      <div className="admin-ticket-workspace">
        <div className="admin-ticket-list-card">
          {ticketsQuery.isError ? (
            <Alert showIcon type="warning" message="票种接口暂不可用，当前显示本地示例数据。" />
          ) : null}
          {saveTicketMutation.isError || deleteTicketMutation.isError ? (
            <Alert showIcon type="error" message="票种保存失败，请确认管理员登录状态后重试。" />
          ) : null}
          <div className="admin-ticket-toolbar" aria-label="票种筛选">
            <Input
              allowClear
              className="admin-ticket-search"
              placeholder="搜索票种"
              prefix={<SearchOutlined />}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <Select
              className="admin-ticket-filter"
              value={statusFilter}
              options={[
                { label: '全部状态', value: 'ALL' },
                { label: '上架中', value: 'ON_SALE' },
                { label: '已下架', value: 'OFF_SALE' },
              ]}
              onChange={setStatusFilter}
            />
            <Button className="admin-ticket-create-action" icon={<PlusOutlined />} type="primary" onClick={openCreateEditor}>
              新增票种
            </Button>
          </div>

          <div className="admin-ticket-table">
            <div className="admin-ticket-table-head">
              <span>票种信息</span>
              <span>价格</span>
              <span>库存</span>
              <span>状态</span>
              <span>剩余配额</span>
              <span>操作</span>
            </div>
            {filteredTickets.map((ticket) => (
              <div className="admin-ticket-row" key={ticket.id}>
                <div className="admin-ticket-info">
                  <img alt="" src={scenicImage} />
                  <div>
                    <Text strong>{ticket.name}</Text>
                    <Text type="secondary">{audienceFor(ticket)}</Text>
                    <div className="admin-ticket-tags">
                      {tagsFor(ticket).map((tag) => <Tag key={tag}>{tag}</Tag>)}
                    </div>
                  </div>
                </div>
                <div className="admin-ticket-price">¥{Number(ticket.salePrice).toFixed(0)}<Text>/ 人</Text></div>
                <div><Text>{ticket.stock}</Text><Text type="secondary">张</Text></div>
                <div>
                  <Tag className={ticket.status === 'ON_SALE' ? 'is-ticket-on' : 'is-ticket-off'}>
                    {ticket.status === 'ON_SALE' ? '上架中' : '已下架'}
                  </Tag>
                </div>
                <div><Text>{ticket.allocatedQuota}</Text><Text type="secondary">张</Text></div>
                <div className="admin-ticket-actions">
                  <Button icon={<EditOutlined />} onClick={() => openEditEditor(ticket)}>编辑</Button>
                  <Button className={ticket.status === 'ON_SALE' ? 'is-off-action' : 'is-on-action'} onClick={() => toggleStatus(ticket)}>
                    {ticket.status === 'ON_SALE' ? '下架' : '上架'}
                  </Button>
                  <Popconfirm title="确认删除这个票种？" okText="删除" cancelText="取消" onConfirm={() => deleteTicket(ticket)}>
                    <Button danger icon={<DeleteOutlined />} aria-label="删除票种" />
                  </Popconfirm>
                </div>
              </div>
            ))}
          </div>

          <div className="admin-ticket-pagination">
            <Text>共 {filteredTickets.length} 条</Text>
            <div>
              <Select size="small" value="10" options={[{ label: '10条/页', value: '10' }]} />
              <Button size="small" disabled>‹</Button>
              <Button size="small" type="primary">1</Button>
              <Button size="small">›</Button>
              <Text>前往</Text>
              <Input size="small" value="1" readOnly />
              <Text>页</Text>
            </div>
          </div>
        </div>

        <aside className="admin-ticket-editor">
          {editorMode === 'idle' ? (
            <div className="admin-ticket-editor-empty">
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description={
                  <span>
                    请选择票种后点击编辑
                    <br />
                    或新增一个票种
                  </span>
                }
              />
            </div>
          ) : (
            <>
              <div className="admin-ticket-editor-head">
                <Title level={2}>{editorMode === 'edit' ? '编辑票种' : '新增票种'}</Title>
                <Button icon={<CloseOutlined />} type="text" onClick={closeEditor} />
              </div>
              <Form form={form} layout="vertical" requiredMark onFinish={saveTicket}>
                <Form.Item label="票种名称" name="name" rules={[{ required: true, message: '请输入票种名称' }]}>
                  <Input maxLength={20} showCount placeholder="成人票" />
                </Form.Item>
                <Form.Item label="票种类型" name="type" rules={[{ required: true, message: '请选择票种类型' }]}>
                  <Select options={typeOptions.map((type) => ({ label: type, value: type }))} />
                </Form.Item>
                <Form.Item label="价格（元）" name="salePrice" rules={[{ required: true, type: 'number', min: 0.01, message: '价格必须大于 0' }]}>
                  <InputNumber min={0.01} precision={2} />
                </Form.Item>
                <Form.Item label="库存（张）" name="stock" rules={[{ required: true, type: 'number', min: 0, message: '请输入库存' }]}>
                  <InputNumber min={0} precision={0} />
                </Form.Item>
                <Form.Item label="可售开始日期" name="dateFrom" rules={[{ required: true, message: '请选择开始日期' }]}>
                  <Input type="date" />
                </Form.Item>
                <Form.Item label="可售结束日期" name="dateTo" rules={[{ required: true, message: '请选择结束日期' }]}>
                  <Input type="date" />
                </Form.Item>
                <Form.Item hidden name="slotQuota">
                  <InputNumber min={0} precision={0} />
                </Form.Item>
                <Form.Item label="时段库存调度" required>
                  <div className="admin-ticket-slot-editor">
                    {defaultSlotQuotas.map((slot, index) => (
                      <div className="admin-ticket-slot-quota" key={`${slot.slotStartTime}-${slot.slotEndTime}`}>
                        <span>{slot.slotStartTime}-{slot.slotEndTime}</span>
                        <Form.Item hidden name={['slotQuotas', index, 'slotStartTime']} initialValue={slot.slotStartTime}>
                          <Input />
                        </Form.Item>
                        <Form.Item hidden name={['slotQuotas', index, 'slotEndTime']} initialValue={slot.slotEndTime}>
                          <Input />
                        </Form.Item>
                        <Form.Item
                          name={['slotQuotas', index, 'quota']}
                          rules={[{ required: true, type: 'number', min: 0, message: '请输入库存' }]}
                        >
                          <InputNumber min={0} precision={0} addonAfter="张" />
                        </Form.Item>
                      </div>
                    ))}
                  </div>
                </Form.Item>
                <Form.Item label="票种描述" name="description">
                  <Input.TextArea maxLength={200} rows={4} showCount />
                </Form.Item>
                <Form.Item label="适用路线" name="route" rules={[{ required: true, message: '请选择适用路线' }]}>
                  <Select options={routeOptions.map((route) => ({ label: route, value: route }))} />
                </Form.Item>
                <Form.Item label="状态" name="status" rules={[{ required: true, message: '请选择状态' }]}>
                  <Radio.Group>
                    <Radio value="ON_SALE">上架中</Radio>
                    <Radio value="OFF_SALE">已下架</Radio>
                  </Radio.Group>
                </Form.Item>
                <div className="admin-ticket-editor-footer">
                  <Button onClick={closeEditor}>取消</Button>
                  <Button type="primary" htmlType="submit" loading={saveTicketMutation.isPending}>
                    {editorMode === 'edit' ? '保存修改' : '保存票种'}
                  </Button>
                </div>
              </Form>
            </>
          )}
        </aside>
      </div>
    </section>
  )
}
