import { DownloadOutlined } from '@ant-design/icons'
import { Button, Flex, Space, Table, Typography } from 'antd'
import type { AdminProductBreakdown } from '../../../shared/api/types'
import { amountLabel } from '../adminReportDisplay'

const { Text, Title } = Typography

type AdminReportProductPanelProps = {
  isCsvExporting: boolean
  isXlsxExporting: boolean
  isLoading: boolean
  onExportCsv: () => void
  onExportXlsx: () => void
  productRows: AdminProductBreakdown[]
}

export function AdminReportProductPanel({
  isCsvExporting,
  isXlsxExporting,
  isLoading,
  onExportCsv,
  onExportXlsx,
  productRows,
}: AdminReportProductPanelProps) {
  return (
    <div className="admin-report-panel admin-product-panel">
      <Flex align="center" justify="space-between" wrap>
        <div>
          <Title level={3}>产品维度</Title>
          <Text type="secondary">订单数去重，金额按明细口径</Text>
        </div>
        <Flex gap={8} wrap>
          <Button
            className="admin-product-breakdown-csv-export-action"
            icon={<DownloadOutlined />}
            loading={isCsvExporting}
            onClick={onExportCsv}
          >
            导出产品 CSV
          </Button>
          <Button
            className="admin-product-breakdown-xlsx-export-action"
            icon={<DownloadOutlined />}
            loading={isXlsxExporting}
            onClick={onExportXlsx}
          >
            导出产品 XLSX
          </Button>
        </Flex>
      </Flex>
      <Table<AdminProductBreakdown>
        className="admin-report-table"
        columns={[
          {
            key: 'product',
            title: '产品 / 票型',
            render: (_, row) => (
              <Space orientation="vertical" size={0}>
                <Text>{row.productName}</Text>
                <Text type="secondary">{row.ticketName}</Text>
              </Space>
            ),
          },
          { dataIndex: 'orderCount', title: '订单' },
          { dataIndex: 'soldTicketCount', title: '售票' },
          { dataIndex: 'checkedInTicketCount', title: '核验' },
          {
            dataIndex: 'netPaidAmount',
            title: '净收入',
            render: (amount: string) => amountLabel(amount),
          },
        ]}
        dataSource={productRows}
        loading={isLoading}
        pagination={false}
        rowKey={(row) => `${row.productId}-${row.ticketTypeId}`}
        scroll={{ x: 620 }}
        size="small"
      />
    </div>
  )
}
