import { Alert, Button, Flex, Skeleton, Tag, Typography } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import type { AdminPaymentReconciliation, AdminReportParams } from '../../../shared/api/types'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'
import { amountLabel, metricLabel } from '../adminReportDisplay'

const { Text, Title } = Typography

type AdminPaymentReconciliationPanelProps = {
  error?: unknown
  isCsvExporting: boolean
  isXlsxExporting: boolean
  isLoading: boolean
  onExportCsv: () => void
  onExportXlsx: () => void
  reconciliation?: AdminPaymentReconciliation
  reportParams: AdminReportParams
}

function rangeLabel(reportParams: AdminReportParams, reconciliation?: AdminPaymentReconciliation) {
  const dateFrom = reconciliation?.dateFrom ?? reportParams.dateFrom ?? '全部'
  const dateTo = reconciliation?.dateTo ?? reportParams.dateTo ?? '全部'
  return `${dateFrom} 至 ${dateTo}`
}

export function AdminPaymentReconciliationPanel({
  error,
  isCsvExporting,
  isXlsxExporting,
  isLoading,
  onExportCsv,
  onExportXlsx,
  reconciliation,
  reportParams,
}: AdminPaymentReconciliationPanelProps) {
  return (
    <section className="admin-payment-reconciliation-panel" aria-label="支付对账摘要">
      <Flex align="flex-start" gap={12} justify="space-between" wrap>
        <div>
          <Title level={3}>支付对账</Title>
          <Text type="secondary">只读对账：订单净收款、支付捕获金额与退款审计金额按同一日期范围核对。</Text>
        </div>
        <Flex gap={8} wrap>
          <Button
            className="admin-payment-reconciliation-csv-export-action"
            icon={<DownloadOutlined />}
            loading={isCsvExporting}
            onClick={onExportCsv}
          >
            导出对账 CSV
          </Button>
          <Button
            className="admin-payment-reconciliation-xlsx-export-action"
            icon={<DownloadOutlined />}
            loading={isXlsxExporting}
            onClick={onExportXlsx}
          >
            导出对账 XLSX
          </Button>
        </Flex>
      </Flex>

      {error ? (
        <Alert
          showIcon
          type="error"
          title="支付对账读取失败"
          description={(
            <ApiErrorDetails
              error={error}
              fallback="支付对账摘要暂时无法读取，请稍后重试。"
              supportingText="请保留错误码和请求编号，便于后端定位管理员会话、报表日期范围或支付记录聚合问题。"
            />
          )}
        />
      ) : null}

      {isLoading ? (
        <Skeleton active paragraph={{ rows: 3 }} title={false} />
      ) : !reconciliation ? (
        <Alert
          className="admin-payment-reconciliation-empty"
          showIcon
          type="info"
          message="暂无支付对账数据"
          description={`范围：${rangeLabel(reportParams)}。请调整日期范围或稍后重试。`}
        />
      ) : (
        <>
          <Flex className="admin-payment-reconciliation-status" align="center" gap={8} wrap>
            <Tag color={reconciliation.reconciled ? 'green' : 'orange'}>
              {reconciliation.reconciled ? '已对平' : '存在差异'}
            </Tag>
            <Text type="secondary">范围：{rangeLabel(reportParams, reconciliation)}</Text>
          </Flex>

          <div className="admin-payment-reconciliation-grid">
            <div>
              <Text type="secondary">订单净收款</Text>
              <strong>{amountLabel(reconciliation?.orderNetPaidAmount ?? '0.00')}</strong>
            </div>
            <div>
              <Text type="secondary">支付捕获金额</Text>
              <strong>{amountLabel(reconciliation?.capturedPaymentAmount ?? '0.00')}</strong>
            </div>
            <div>
              <Text type="secondary">退款审计金额</Text>
              <strong>{amountLabel(reconciliation?.refundAuditAmount ?? '0.00')}</strong>
            </div>
            <div>
              <Text type="secondary">预期净额</Text>
              <strong>{amountLabel(reconciliation?.expectedNetAmount ?? '0.00')}</strong>
            </div>
            <div>
              <Text type="secondary">未对账差额</Text>
              <strong className={reconciliation?.reconciled ? undefined : 'is-warning'}>
                {amountLabel(reconciliation?.unreconciledAmount ?? '0.00')}
              </strong>
            </div>
            <div>
              <Text type="secondary">支付 / 退款记录</Text>
              <strong>
                {metricLabel(reconciliation?.capturedPaymentCount)} / {metricLabel(reconciliation?.refundAuditLogCount)}
              </strong>
            </div>
          </div>

          <Text className="admin-payment-reconciliation-footnote" type="secondary">
            对账摘要不展示支付流水号、渠道交易号、完整手机号、证件号、会话凭据、防伪令牌、内部查询语句或审计明细。
          </Text>
        </>
      )}
    </section>
  )
}
