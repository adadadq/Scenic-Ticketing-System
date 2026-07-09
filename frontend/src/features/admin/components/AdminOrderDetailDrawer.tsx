import { Alert, Button, Drawer, Empty, Space, Typography } from 'antd'
import type {
  AdminCheckIn,
  AdminOrderDetail,
  AdminPartialRefund,
  AdminRefund,
  AdminRefundAuditLog,
} from '../../../shared/api/types'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'
import { amountLabel } from '../adminOrderDisplay'
import { AdminOrderDetailSummary } from './AdminOrderDetailSummary'
import {
  AdminCheckInErrorDetails,
  AdminPartialRefundErrorDetails,
  AdminRefundErrorDetails,
} from './AdminOrderDetailErrorDetails'
import { AdminOrderItemsTable } from './AdminOrderItemsTable'
import { AdminOrderRefundPanels } from './AdminOrderRefundPanels'
import { AdminRefundAuditPanel } from './AdminRefundAuditPanel'

const { Text } = Typography

export function AdminOrderDetailDrawer({
  checkInError,
  checkInResult,
  detail,
  error,
  isCheckingIn,
  isPartialRefunding,
  isRefunding,
  isLoading,
  isOpen,
  onClose,
  onCheckIn,
  onFullRefund,
  onPartialRefund,
  onPartialRefundItemNosChange,
  onPartialRefundReasonChange,
  onRefundLogsRetry,
  onRetry,
  pendingTicketCode,
  partialRefundError,
  partialRefundItemNos,
  partialRefundReason,
  partialRefundResult,
  refundError,
  refundLogs,
  refundLogsError,
  refundLogsLoading,
  refundReason,
  refundResult,
  onRefundReasonChange,
}: {
  checkInError: unknown
  checkInResult?: AdminCheckIn
  detail?: AdminOrderDetail | null
  error: unknown
  isCheckingIn: boolean
  isPartialRefunding: boolean
  isRefunding: boolean
  isLoading: boolean
  isOpen: boolean
  onClose: () => void
  onCheckIn: (ticketCode: string) => void
  onFullRefund: () => void
  onPartialRefund: () => void
  onPartialRefundItemNosChange: (itemNos: string[]) => void
  onPartialRefundReasonChange: (reason: string) => void
  onRefundLogsRetry: () => void
  onRetry: () => void
  pendingTicketCode?: string
  partialRefundError: unknown
  partialRefundItemNos: string[]
  partialRefundReason: string
  partialRefundResult?: AdminPartialRefund
  refundError: unknown
  refundLogs: AdminRefundAuditLog[]
  refundLogsError: unknown
  refundLogsLoading: boolean
  refundReason: string
  refundResult?: AdminRefund
  onRefundReasonChange: (reason: string) => void
}) {
  return (
    <Drawer
      className="admin-order-detail-drawer"
      destroyOnHidden
      open={isOpen}
      onClose={onClose}
      title="订单详情"
      size="large"
    >
      {error ? (
        <Alert
          showIcon
          type="error"
          title="订单详情读取失败"
          description={(
            <ApiErrorDetails
              error={error}
              fallback="后台订单详情暂时无法读取，请稍后重试。"
              supportingText="请保留错误码和请求编号，便于后端定位详情读取或权限问题。"
            />
          )}
          action={(
            <Button size="small" onClick={onRetry}>
              重试
            </Button>
          )}
        />
      ) : isLoading ? (
        <Text type="secondary">订单详情加载中...</Text>
      ) : detail ? (
        <Space className="admin-card-stack" orientation="vertical" size={16}>
          <AdminOrderDetailSummary detail={detail} />
          {checkInResult ? (
            <Alert
              className="admin-check-in-result"
              showIcon
              type="success"
              title="票码核验成功"
              description={`票项 ${checkInResult.itemNo} 已核验，订单状态 ${checkInResult.orderStatus}。`}
            />
          ) : null}
          {refundResult ? (
            <Alert
              className="admin-refund-result"
              showIcon
              type="success"
              title="整单退款成功"
              description={`订单 ${refundResult.orderNo} 已退款 ${amountLabel(refundResult.refundedAmount)}，票项 ${refundResult.refundedItemCount} 张。`}
            />
          ) : null}
          {partialRefundResult ? (
            <Alert
              className="admin-partial-refund-result"
              showIcon
              type="success"
              title="部分退款成功"
              description={`订单 ${partialRefundResult.orderNo} 已部分退款 ${amountLabel(partialRefundResult.refundedAmount)}，票项 ${partialRefundResult.refundedItemCount} 张。`}
            />
          ) : null}
          {checkInError ? (
            <Alert
              showIcon
              type="error"
              title="票码核验失败"
              description={<AdminCheckInErrorDetails error={checkInError} />}
            />
          ) : null}
          {refundError ? (
            <Alert
              showIcon
              type="error"
              title="整单退款失败"
              description={<AdminRefundErrorDetails error={refundError} />}
            />
          ) : null}
          {partialRefundError ? (
            <Alert
              showIcon
              type="error"
              title="部分退款失败"
              description={<AdminPartialRefundErrorDetails error={partialRefundError} />}
            />
          ) : null}
          <AdminOrderItemsTable
            detail={detail}
            isCheckingIn={isCheckingIn}
            onCheckIn={onCheckIn}
            pendingTicketCode={pendingTicketCode}
          />
          <AdminOrderRefundPanels
            detail={detail}
            isPartialRefunding={isPartialRefunding}
            isRefunding={isRefunding}
            onFullRefund={onFullRefund}
            onPartialRefund={onPartialRefund}
            onPartialRefundItemNosChange={onPartialRefundItemNosChange}
            onPartialRefundReasonChange={onPartialRefundReasonChange}
            onRefundReasonChange={onRefundReasonChange}
            partialRefundItemNos={partialRefundItemNos}
            partialRefundReason={partialRefundReason}
            refundReason={refundReason}
          />
          <AdminRefundAuditPanel
            onRetry={onRefundLogsRetry}
            refundLogs={refundLogs}
            refundLogsError={refundLogsError}
            refundLogsLoading={refundLogsLoading}
          />
        </Space>
      ) : (
        <Empty description="选择订单后查看详情" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      )}
    </Drawer>
  )
}
