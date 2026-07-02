import { CloseCircleOutlined, FieldTimeOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import { Alert, Button, Flex, Input, Select, Space, Table, Tag, Typography } from 'antd'
import type { AdminOrderListParams, AdminOrderSummary, AdminOrderStatusFilter, AdminPaymentStatusFilter } from '../../shared/api/types'
import { ApiErrorDetails } from '../../shared/components/ApiErrorDetails'
import { useMemo, useState } from 'react'
import {
  adminOrdersMode,
  useAdminBatchCheckInMutation,
  useAdminBatchUndoCheckInMutation,
  useAdminCheckInMutation,
  useAdminFullRefundMutation,
  useAdminOrderDetailQuery,
  useAdminOrdersQuery,
  useAdminPartialRefundMutation,
  useAdminRefundAuditLogsQuery,
} from '../admin-orders/queries'
import {
  amountLabel,
  normalizeAdminPhoneFilter,
  orderStatusOptions,
  paymentStatusOptions,
  paymentTag,
  statusTag,
} from './adminOrderDisplay'
import { AdminOrderDetailDrawer } from './components/AdminOrderDetailDrawer'
import { AdminBatchCheckInPanel } from './components/AdminBatchCheckInPanel'
import { AdminBatchUndoCheckInPanel } from './components/AdminBatchUndoCheckInPanel'

const { Text, Title } = Typography

export function AdminOrdersPanel() {
  const [status, setStatus] = useState<AdminOrderStatusFilter | 'ALL'>('ALL')
  const [paymentStatus, setPaymentStatus] = useState<AdminPaymentStatusFilter | 'ALL'>('ALL')
  const [orderNo, setOrderNo] = useState('')
  const [buyerPhone, setBuyerPhone] = useState('')
  const [selectedOrderNo, setSelectedOrderNo] = useState<string>()
  const [partialRefundItemNos, setPartialRefundItemNos] = useState<string[]>([])
  const [partialRefundReason, setPartialRefundReason] = useState('')
  const [refundReason, setRefundReason] = useState('')
  const queryParams = useMemo<AdminOrderListParams>(() => {
    const normalizedBuyerPhone = normalizeAdminPhoneFilter(buyerPhone)
    const normalizedOrderNo = orderNo.trim()

    return {
      ...(status === 'ALL' ? {} : { status }),
      ...(paymentStatus === 'ALL' ? {} : { paymentStatus }),
      ...(normalizedOrderNo ? { orderNo: normalizedOrderNo } : {}),
      ...(normalizedBuyerPhone ? { buyerPhone: normalizedBuyerPhone } : {}),
      page: 1,
      pageSize: 20,
    }
  }, [buyerPhone, orderNo, paymentStatus, status])
  const ordersQuery = useAdminOrdersQuery(queryParams)
  const detailQuery = useAdminOrderDetailQuery(selectedOrderNo)
  const refundLogsQuery = useAdminRefundAuditLogsQuery(selectedOrderNo)
  const batchCheckInMutation = useAdminBatchCheckInMutation()
  const batchUndoCheckInMutation = useAdminBatchUndoCheckInMutation()
  const checkInMutation = useAdminCheckInMutation()
  const fullRefundMutation = useAdminFullRefundMutation()
  const partialRefundMutation = useAdminPartialRefundMutation()
  const orders = ordersQuery.data?.items ?? []
  const total = ordersQuery.data?.total ?? 0
  const hasFilters = status !== 'ALL' || paymentStatus !== 'ALL' || Boolean(orderNo.trim() || buyerPhone.trim())

  function clearFilters() {
    setStatus('ALL')
    setPaymentStatus('ALL')
    setOrderNo('')
    setBuyerPhone('')
  }

  function selectOrder(orderNo: string) {
    checkInMutation.reset()
    fullRefundMutation.reset()
    partialRefundMutation.reset()
    setPartialRefundItemNos([])
    setPartialRefundReason('')
    setRefundReason('')
    setSelectedOrderNo(orderNo)
  }

  function closeDetail() {
    checkInMutation.reset()
    fullRefundMutation.reset()
    partialRefundMutation.reset()
    setPartialRefundItemNos([])
    setPartialRefundReason('')
    setRefundReason('')
    setSelectedOrderNo(undefined)
  }

  function submitFullRefund() {
    if (!selectedOrderNo) {
      return
    }

    fullRefundMutation.mutate(
      { orderNo: selectedOrderNo, reason: refundReason },
      {
        onSuccess: () => setRefundReason(''),
      },
    )
  }

  function submitPartialRefund() {
    if (!selectedOrderNo || partialRefundItemNos.length === 0) {
      return
    }

    partialRefundMutation.mutate(
      {
        itemNos: partialRefundItemNos,
        orderNo: selectedOrderNo,
        reason: partialRefundReason,
      },
      {
        onSuccess: () => {
          setPartialRefundItemNos([])
          setPartialRefundReason('')
        },
      },
    )
  }

  return (
    <Space className="admin-card-stack" orientation="vertical" size={14}>
      <div className="admin-section-heading">
        <div>
          <Title level={2}>订单运营列表</Title>
          <Text type="secondary">只读 read-model：先核对订单、票数与脱敏联系方式；核验和整单退款走状态变更 POST。</Text>
        </div>
        <Space size={8} wrap>
          <Tag color={adminOrdersMode === 'api' ? 'blue' : 'gold'}>
            {adminOrdersMode === 'api' ? 'API Orders' : 'Mock Orders'}
          </Tag>
          <Button icon={<ReloadOutlined />} loading={ordersQuery.isFetching} onClick={() => ordersQuery.refetch()}>
            刷新
          </Button>
        </Space>
      </div>

      <AdminBatchCheckInPanel
        error={batchCheckInMutation.error}
        isCheckingIn={batchCheckInMutation.isPending}
        onSubmit={(ticketCodes) => batchCheckInMutation.mutate({ ticketCodes })}
        result={batchCheckInMutation.data}
      />

      <AdminBatchUndoCheckInPanel
        error={batchUndoCheckInMutation.error}
        isUndoing={batchUndoCheckInMutation.isPending}
        onSubmit={(ticketCodes, reason) => batchUndoCheckInMutation.mutate({
          ticketCodes,
          ...(reason.trim() ? { reason: reason.trim() } : {}),
        })}
        result={batchUndoCheckInMutation.data}
      />

      <Flex className="admin-orders-toolbar" gap={10} wrap>
        <Select
          aria-label="订单状态筛选"
          className="admin-order-status-select admin-orders-select"
          classNames={{ popup: { root: 'admin-order-status-popup' } }}
          onChange={setStatus}
          options={orderStatusOptions}
          value={status}
        />
        <Select
          aria-label="支付状态筛选"
          className="admin-order-payment-select admin-orders-select"
          classNames={{ popup: { root: 'admin-order-payment-popup' } }}
          onChange={setPaymentStatus}
          options={paymentStatusOptions}
          value={paymentStatus}
        />
        <Input
          allowClear
          className="admin-orders-search"
          onChange={(event) => setOrderNo(event.target.value)}
          placeholder="搜索订单号"
          prefix={<SearchOutlined />}
          value={orderNo}
        />
        <Input
          allowClear
          className="admin-orders-search"
          onChange={(event) => setBuyerPhone(event.target.value)}
          placeholder="手机号后四位"
          prefix={<SearchOutlined />}
          value={buyerPhone}
        />
        <Button disabled={!hasFilters} icon={<CloseCircleOutlined />} onClick={clearFilters}>
          清空
        </Button>
      </Flex>

      {ordersQuery.isError ? (
        <Alert
          showIcon
          type="error"
          title="后台订单读取失败"
          description={(
            <ApiErrorDetails
              error={ordersQuery.error}
              fallback="后台订单列表暂时无法读取，请稍后重试。"
              supportingText="请保留错误码和请求编号，便于后端定位管理员会话、权限或查询参数问题。"
            />
          )}
          action={(
            <Button size="small" onClick={() => ordersQuery.refetch()}>
              重试
            </Button>
          )}
        />
      ) : null}

      <Table<AdminOrderSummary>
        className="admin-orders-table"
        columns={[
          {
            dataIndex: 'orderNo',
            title: '订单号',
            render: (orderNo: string) => <Text code>{orderNo}</Text>,
          },
          { dataIndex: 'buyerName', title: '游客' },
          { dataIndex: 'buyerPhoneMasked', title: '手机号' },
          {
            dataIndex: 'orderStatus',
            title: '订单状态',
            render: statusTag,
          },
          {
            dataIndex: 'paymentStatus',
            title: '支付状态',
            render: paymentTag,
          },
          {
            dataIndex: 'itemCount',
            title: '票数',
            render: (itemCount: number) => `${itemCount} 张`,
          },
          {
            dataIndex: 'payableAmount',
            title: '应付金额',
            render: (amount: string) => `¥ ${amount}`,
          },
          {
            key: 'actions',
            title: '操作',
            render: () => (
              <Button className="admin-order-future-action" disabled icon={<FieldTimeOutlined />} size="small">
                后续接入
              </Button>
            ),
          },
        ]}
        dataSource={orders}
        locale={{
          emptyText: hasFilters ? '没有匹配的后台订单' : '暂无后台订单',
        }}
        loading={ordersQuery.isLoading}
        onRow={(record) => ({
          onClick: () => selectOrder(record.orderNo),
        })}
        pagination={false}
        rowKey="orderNo"
        scroll={{ x: 860 }}
        size="small"
      />
      <ul className="admin-orders-mobile-list">
        {orders.length > 0 ? orders.map((order) => (
          <li key={order.orderNo}>
            <button className="admin-order-mobile-card" type="button" onClick={() => selectOrder(order.orderNo)}>
              <Flex align="flex-start" gap={8} justify="space-between">
                <Space orientation="vertical" size={2}>
                  <Text code>{order.orderNo}</Text>
                  <Text type="secondary">{order.buyerName} · {order.buyerPhoneMasked}</Text>
                </Space>
                {paymentTag(order.paymentStatus)}
              </Flex>
              <Flex align="center" gap={8} justify="space-between" wrap>
                {statusTag(order.orderStatus)}
                <Text type="secondary">{order.itemCount} 张 · {amountLabel(order.payableAmount)}</Text>
              </Flex>
            </button>
          </li>
        )) : (
          <li className="admin-orders-mobile-empty">{hasFilters ? '没有匹配的后台订单' : '暂无后台订单'}</li>
        )}
      </ul>

      <Text className="admin-orders-footnote" type="secondary">
        当前读取 {orders.length} / {total} 笔订单，列表只展示脱敏手机号。
      </Text>

      <AdminOrderDetailDrawer
        checkInError={checkInMutation.error}
        checkInResult={checkInMutation.data}
        detail={detailQuery.data}
        error={detailQuery.error}
        isCheckingIn={checkInMutation.isPending}
        isPartialRefunding={partialRefundMutation.isPending}
        isRefunding={fullRefundMutation.isPending}
        isLoading={detailQuery.isLoading}
        isOpen={Boolean(selectedOrderNo)}
        onCheckIn={(ticketCode) => checkInMutation.mutate({ ticketCode })}
        onClose={closeDetail}
        onFullRefund={submitFullRefund}
        onPartialRefund={submitPartialRefund}
        onPartialRefundItemNosChange={setPartialRefundItemNos}
        onPartialRefundReasonChange={setPartialRefundReason}
        onRefundLogsRetry={() => refundLogsQuery.refetch()}
        onRetry={() => detailQuery.refetch()}
        pendingTicketCode={checkInMutation.variables?.ticketCode}
        partialRefundError={partialRefundMutation.error}
        partialRefundItemNos={partialRefundItemNos}
        partialRefundReason={partialRefundReason}
        partialRefundResult={partialRefundMutation.data}
        refundError={fullRefundMutation.error}
        refundLogs={refundLogsQuery.data ?? []}
        refundLogsError={refundLogsQuery.error}
        refundLogsLoading={refundLogsQuery.isLoading}
        refundReason={refundReason}
        refundResult={fullRefundMutation.data}
        onRefundReasonChange={setRefundReason}
      />
    </Space>
  )
}
