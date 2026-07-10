import {
  CalendarOutlined,
  CheckCircleOutlined,
  DownOutlined,
  DownloadOutlined,
  ExclamationCircleOutlined,
  FileSearchOutlined,
  ReloadOutlined,
  SearchOutlined,
  SunOutlined,
} from '@ant-design/icons'
import { Alert, Button, Input, Select, Spin, Typography } from 'antd'
import type { MouseEvent } from 'react'
import type {
  AdminOrderDetail,
  AdminOrderListParams,
  AdminOrderStatusFilter,
  AdminOrderSummary,
} from '../../shared/api/types'
import { ApiErrorDetails } from '../../shared/components/ApiErrorDetails'
import { scenicTicketName } from '../../shared/display/scenicText'
import { useEffect, useMemo, useState } from 'react'
import {
  useAdminCheckInMutation,
  useAdminFullRefundMutation,
  useAdminOrderDetailQuery,
  useAdminOrdersQuery,
} from '../admin-orders/queries'
import {
  amountLabel,
  canCheckInItem,
  canFullRefundOrder,
  orderStatusOptions,
  raftLabel,
  statusTag,
} from './adminOrderDisplay'
import { AdminNoticeButton } from './components/AdminNoticeButton'
import './adminOrders.css'

const { Text, Title } = Typography
const scenicImage = '/admin-login-landscape.png'

const ticketFilterOptions = [
  { label: '全部票种', value: 'ALL' },
]

const orderMetrics = [
  { icon: '¥', label: '今日订单', tone: 'teal', trend: '+18.75% ↑', value: '256' },
  { icon: <CheckCircleOutlined />, label: '待核验', tone: 'blue', trend: '-8.46% ↓', value: '86' },
  { icon: <ReloadOutlined />, label: '退款申请', tone: 'purple', trend: '+20.00% ↑', value: '12' },
  { icon: <ExclamationCircleOutlined />, label: '异常提醒', tone: 'orange', trend: '-33.33% ↓', value: '2' },
]

type AdminOrdersPanelProps = {
  onOpenProfile?: () => void
}

export function AdminOrdersPanel({ onOpenProfile }: AdminOrdersPanelProps) {
  const [status, setStatus] = useState<AdminOrderStatusFilter | 'ALL'>('ALL')
  const [orderNo, setOrderNo] = useState('')
  const [page, setPage] = useState(1)
  const pageSize = 10
  const [selectedOrderNo, setSelectedOrderNo] = useState<string>()
  const queryParams = useMemo<AdminOrderListParams>(() => {
    const normalizedOrderNo = orderNo.trim()

    return {
      ...(status === 'ALL' ? {} : { status }),
      ...(normalizedOrderNo ? { orderNo: normalizedOrderNo } : {}),
      page,
      pageSize,
    }
  }, [orderNo, page, status])
  const ordersQuery = useAdminOrdersQuery(queryParams)
  const checkInMutation = useAdminCheckInMutation()
  const fullRefundMutation = useAdminFullRefundMutation()
  const orders = ordersQuery.data?.items ?? []
  const detailQuery = useAdminOrderDetailQuery(selectedOrderNo)
  const selectedDetail = detailQuery.data ?? null
  const selectedSummary = orders.find((order) => order.orderNo === selectedOrderNo) ?? orders[0]
  const total = ordersQuery.data?.total ?? orders.length
  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const hasFilters = status !== 'ALL' || Boolean(orderNo.trim())

  useEffect(() => {
    if (!selectedOrderNo && orders[0]) {
      setSelectedOrderNo(orders[0].orderNo)
      return
    }

    if (selectedOrderNo && orders.length > 0 && !orders.some((order) => order.orderNo === selectedOrderNo)) {
      setSelectedOrderNo(orders[0].orderNo)
    }
  }, [orders, selectedOrderNo])

  function clearFilters() {
    setStatus('ALL')
    setOrderNo('')
    setPage(1)
  }

  function checkInSelectedOrder() {
    const item = selectedDetail?.items.find((candidate) => canCheckInItem(selectedDetail, candidate))

    if (item?.ticketCode) {
      checkInMutation.mutate({ ticketCode: item.ticketCode })
    }
  }

  function refundSelectedOrder() {
    if (!selectedDetail) {
      return
    }

    fullRefundMutation.mutate({ orderNo: selectedDetail.orderNo, reason: '后台发起整单退款' })
  }

  return (
    <section className="admin-order-page">
      <header className="admin-order-hero">
        <div className="admin-order-hero-copy">
          <Title level={1}>订单管理</Title>
          <Text>查看订单、核验状态与退改处理</Text>
          <span aria-hidden="true" />
        </div>
        <div className="admin-dashboard-top-actions">
          <div className="admin-weather-card">
            <SunOutlined />
            <span>晴 26°C</span>
            <Text>2026-06-28 16:04</Text>
          </div>
          <AdminNoticeButton />
          <button className="admin-profile-button" type="button" onClick={onOpenProfile}>
            <span className="admin-profile-avatar" />
            <strong>演示管理员</strong>
            <DownOutlined />
          </button>
        </div>
      </header>

      <div className="admin-order-body">
        <div className="admin-order-toolbar">
          <Input
            allowClear
            className="admin-order-search"
            onChange={(event) => {
              setOrderNo(event.target.value)
              setPage(1)
            }}
            placeholder="搜索订单号"
            prefix={<SearchOutlined />}
            value={orderNo}
          />
          <Input className="admin-order-date" prefix={<CalendarOutlined />} readOnly value="2026/06/26  ~  2026/06/28" />
          <Select
            className="admin-order-select"
            onChange={(nextStatus) => {
              setStatus(nextStatus)
              setPage(1)
            }}
            options={orderStatusOptions.map((option) => ({
              ...option,
              label: option.value === 'ALL' ? '全部状态' : option.label,
            }))}
            value={status}
          />
          <Select className="admin-order-select" disabled options={ticketFilterOptions} value="ALL" />
          <div className="admin-order-toolbar-spacer" />
          <Button icon={<ReloadOutlined />} loading={ordersQuery.isFetching} onClick={() => ordersQuery.refetch()}>
            刷新
          </Button>
          <Button className="admin-order-export" icon={<DownloadOutlined />}>
            导出订单
          </Button>
        </div>

        {ordersQuery.isError ? (
          <Alert
            showIcon
            className="admin-order-alert"
            type="error"
            message="订单暂时读取失败"
            description={(
              <ApiErrorDetails
                error={ordersQuery.error}
                fallback="请稍后重试，或检查管理员会话是否仍然有效。"
              />
            )}
            action={(
              <Button size="small" onClick={() => ordersQuery.refetch()}>
                重试
              </Button>
            )}
          />
        ) : null}

        <div className="admin-order-layout">
          <div className="admin-order-left">
            <section className="admin-order-list-card">
              <div className="admin-order-card-title">订单列表</div>
              <Spin spinning={ordersQuery.isLoading}>
                <div className="admin-order-table-wrap">
                  <table className="admin-order-table">
                    <thead>
                      <tr>
                        <th>订单号</th>
                        <th>游客信息</th>
                        <th>票种类型</th>
                        <th>游览日期/时间</th>
                        <th>数量</th>
                        <th>金额</th>
                        <th>状态</th>
                        <th>操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {orders.length > 0 ? orders.map((order) => (
                        <OrderRow
                          isSelected={order.orderNo === selectedOrderNo}
                          key={order.orderNo}
                          order={order}
                          onSelect={() => setSelectedOrderNo(order.orderNo)}
                        />
                      )) : (
                        <tr>
                          <td colSpan={8}>
                            <div className="admin-order-empty">{hasFilters ? '没有找到匹配订单' : '暂无订单'}</div>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </Spin>
              <div className="admin-order-pagination">
                <Text>共 {Math.max(total, orders.length)} 条</Text>
                <button type="button">10条/页</button>
                <button disabled={page <= 1} type="button" aria-label="上一页" onClick={() => setPage((value) => Math.max(1, value - 1))}>‹</button>
                {visiblePages(page, pageCount).map((pageNumber) => (
                  <button
                    className={pageNumber === page ? 'is-active' : undefined}
                    key={pageNumber}
                    type="button"
                    onClick={() => setPage(pageNumber)}
                  >
                    {pageNumber}
                  </button>
                ))}
                <button disabled={page >= pageCount} type="button" onClick={() => setPage((value) => Math.min(pageCount, value + 1))}>›</button>
                <Text>前往</Text>
                <input
                  aria-label="页码"
                  value={page}
                  onChange={(event) => {
                    const nextPage = Number(event.target.value)
                    if (Number.isInteger(nextPage)) {
                      setPage(Math.min(pageCount, Math.max(1, nextPage)))
                    }
                  }}
                />
                <Text>页</Text>
              </div>
            </section>

            <div className="admin-order-metrics">
              {orderMetrics.map((metric) => (
                <section className={`admin-order-metric is-${metric.tone}`} key={metric.label}>
                  <span>{metric.icon}</span>
                  <div>
                    <Text>{metric.label}</Text>
                    <strong>{metric.value}<em>笔</em></strong>
                    <small>较昨日 {metric.trend}</small>
                  </div>
                </section>
              ))}
            </div>
          </div>

          <OrderDetailPanel
            canClearFilters={hasFilters}
            checkInLoading={checkInMutation.isPending}
            detail={selectedDetail}
            fallback={selectedSummary}
            isLoading={detailQuery.isLoading}
            onCheckIn={checkInSelectedOrder}
            onClearFilters={clearFilters}
            onRefund={refundSelectedOrder}
            refundLoading={fullRefundMutation.isPending}
          />
        </div>
      </div>
    </section>
  )
}

function OrderRow({
  isSelected,
  onSelect,
  order,
}: {
  isSelected: boolean
  onSelect: () => void
  order: AdminOrderSummary
}) {
  return (
    <tr className={isSelected ? 'is-selected' : undefined} onClick={onSelect}>
      <td><strong>{displayOrderNo(order.orderNo)}</strong></td>
      <td>
        <div className="admin-order-guest">
          <strong>{order.buyerName || '游客'}</strong>
          <Text>{order.buyerPhoneMasked}</Text>
        </div>
      </td>
      <td>详情中查看</td>
      <td>
        <div className="admin-order-time">
          <strong>{formatDate(order.orderTime)}</strong>
          <Text>{formatTime(order.orderTime)}</Text>
        </div>
      </td>
      <td>{order.itemCount}</td>
      <td>{amountLabel(order.payableAmount)}</td>
      <td>{statusTag(order.orderStatus)}</td>
      <td>
        <div className="admin-order-row-actions">
          <button type="button" onClick={(event) => selectFromButton(event, onSelect)}>详情</button>
        </div>
      </td>
    </tr>
  )
}

function OrderDetailPanel({
  checkInLoading,
  canClearFilters,
  detail,
  fallback,
  isLoading,
  onCheckIn,
  onClearFilters,
  onRefund,
  refundLoading,
}: {
  canClearFilters: boolean
  checkInLoading: boolean
  detail: AdminOrderDetail | null
  fallback?: AdminOrderSummary
  isLoading: boolean
  onCheckIn: () => void
  onClearFilters: () => void
  onRefund: () => void
  refundLoading: boolean
}) {
  const firstItem = detail?.items[0] ?? null
  const canCheckIn = Boolean(detail?.items.some((item) => canCheckInItem(detail, item)))
  const canRefund = Boolean(detail && canFullRefundOrder(detail))
  const firstTicketCode = detail?.items.find((item) => item.ticketCode)?.ticketCode ?? '--'

  return (
    <aside className="admin-order-detail-card">
      <div className="admin-order-card-title"><FileSearchOutlined />订单详情</div>
      <Spin spinning={isLoading}>
        {detail || fallback ? (
          <>
            <div className="admin-order-detail-head">
              <img src={scenicImage} alt="" />
              <div>
                <strong>{displayOrderNo(detail?.orderNo ?? fallback?.orderNo ?? '')}</strong>
                <Text>下单时间：{formatDateTime(detail?.orderTime ?? fallback?.orderTime)}</Text>
                <Text>支付时间：--</Text>
              </div>
              {statusTag(detail?.orderStatus ?? fallback?.orderStatus ?? 'PAID')}
            </div>

            <div className="admin-order-detail-section">
              <strong>票品信息</strong>
              <DetailLine label={firstItem ? scenicTicketName(firstItem.ticketName) : '详情加载中'} value={firstItem ? `${amountLabel(firstItem.finalPrice)}/人` : '--'} />
              <DetailLine label="游览日期/时间" value={firstItem ? `${firstItem.visitDate}  ${slotRange(firstItem)}` : '--'} />
              <DetailLine label="竹筏安排" value={firstItem ? raftLabel(firstItem) : '--'} />
              <DetailLine label="数量" value={`${detail?.items.length ?? fallback?.itemCount ?? 0} 张`} />
              <DetailLine label="小计" value={amountLabel(detail?.payableAmount ?? fallback?.payableAmount ?? '0.00')} />
            </div>

            <div className="admin-order-detail-section">
              <strong>支付信息</strong>
              <DetailLine className="is-money" label="实付金额" value={amountLabel(detail?.payableAmount ?? fallback?.payableAmount ?? '0.00')} />
              <DetailLine label="支付方式" value="微信支付" />
              <DetailLine label="交易单号" value="--" />
            </div>

            <div className="admin-order-detail-section">
              <strong>游客信息</strong>
              <DetailLine label={detail?.buyerName ?? fallback?.buyerName ?? '游客'} value={detail?.buyerPhoneMasked ?? fallback?.buyerPhoneMasked ?? '--'} />
              <DetailLine label="下单备注" value="--" />
            </div>

            <div className="admin-order-timeline">
              <strong>订单状态跟踪</strong>
              {['下单成功', '支付成功', detail?.orderStatus === 'COMPLETED' ? '已核验' : '待核验'].map((item, index) => (
                <div className="admin-order-timeline-row" key={item}>
                  <span />
                  <Text>{item}</Text>
                  <em>{index === 0 ? formatDateTime(detail?.orderTime ?? fallback?.orderTime) : '--'}</em>
                </div>
              ))}
            </div>

            <div className="admin-order-qr-section">
              <div className="admin-order-qr" aria-label="核验二维码" />
              <div>
                <strong>待核验</strong>
                <Text>请在景区核验后入园</Text>
                <Text>核验码：{firstTicketCode}</Text>
              </div>
            </div>

            <div className="admin-order-detail-actions">
              <Button className="admin-order-check-action" disabled={!canCheckIn} loading={checkInLoading} onClick={onCheckIn}>
                核验入园
              </Button>
              <Button className="admin-order-refund-action" disabled={!canRefund} loading={refundLoading} onClick={onRefund}>
                发起退款
              </Button>
              <Button disabled={!canClearFilters} onClick={onClearFilters}>
                清空筛选
              </Button>
            </div>
          </>
        ) : (
          <div className="admin-order-empty">请选择一笔订单</div>
        )}
      </Spin>
    </aside>
  )
}

function DetailLine({ className, label, value }: { className?: string; label: string; value: string }) {
  return (
    <div className={`admin-order-detail-line ${className ?? ''}`}>
      <Text>{label}</Text>
      <strong>{value}</strong>
    </div>
  )
}

function selectFromButton(event: MouseEvent<HTMLButtonElement>, onSelect: () => void) {
  event.stopPropagation()
  onSelect()
}

function displayOrderNo(orderNo: string) {
  if (!orderNo) {
    return '--'
  }

  return orderNo.startsWith('YT') ? `O20260704${orderNo.slice(-6)}` : orderNo
}

function formatDate(value?: string) {
  return value?.slice(0, 10) ?? '--'
}

function formatTime(value?: string) {
  return value?.slice(11, 16) ?? '--'
}

function formatDateTime(value?: string) {
  if (!value) {
    return '--'
  }

  return value.replace('T', ' ').slice(0, 19)
}

function slotRange(item: { slotStartTime: string; slotEndTime: string }) {
  return `${item.slotStartTime.slice(0, 5)}-${item.slotEndTime.slice(0, 5)}`
}

function visiblePages(page: number, pageCount: number) {
  const start = Math.max(1, Math.min(page - 2, pageCount - 4))
  return Array.from({ length: Math.min(5, pageCount) }, (_, index) => start + index)
}
