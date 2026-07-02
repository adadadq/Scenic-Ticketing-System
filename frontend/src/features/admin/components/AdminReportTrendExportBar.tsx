import { DownloadOutlined } from '@ant-design/icons'
import { Button, Flex, Space, Typography } from 'antd'
import type { AdminTrendCsvKind } from '../../admin-reports/exportCsv'

const { Text } = Typography

type AdminReportTrendExportBarProps = {
  isAnyTrendExporting: boolean
  isTrendCsvExporting: AdminTrendCsvKind | null
  isTrendXlsxExporting: AdminTrendCsvKind | null
  onExportCsv: (kind: AdminTrendCsvKind) => void
  onExportXlsx: (kind: AdminTrendCsvKind) => void
}

export function AdminReportTrendExportBar({
  isAnyTrendExporting,
  isTrendCsvExporting,
  isTrendXlsxExporting,
  onExportCsv,
  onExportXlsx,
}: AdminReportTrendExportBarProps) {
  return (
    <Flex className="admin-report-trend-export-bar" gap={12} justify="space-between" wrap>
      <Text type="secondary">趋势 CSV/XLSX 导出跟随当前日期范围和补零口径。</Text>
      <Space size={8} wrap>
        <Button
          className="admin-report-daily-trend-csv-export-action"
          disabled={isAnyTrendExporting}
          icon={<DownloadOutlined />}
          loading={isTrendCsvExporting === 'daily'}
          onClick={() => onExportCsv('daily')}
        >
          导出日趋势 CSV
        </Button>
        <Button
          className="admin-report-hourly-trend-csv-export-action"
          disabled={isAnyTrendExporting}
          icon={<DownloadOutlined />}
          loading={isTrendCsvExporting === 'hourly'}
          onClick={() => onExportCsv('hourly')}
        >
          导出小时趋势 CSV
        </Button>
        <Button
          className="admin-report-monthly-trend-csv-export-action"
          disabled={isAnyTrendExporting}
          icon={<DownloadOutlined />}
          loading={isTrendCsvExporting === 'monthly'}
          onClick={() => onExportCsv('monthly')}
        >
          导出月趋势 CSV
        </Button>
        <Button
          className="admin-report-daily-trend-xlsx-export-action"
          disabled={isAnyTrendExporting}
          icon={<DownloadOutlined />}
          loading={isTrendXlsxExporting === 'daily'}
          onClick={() => onExportXlsx('daily')}
        >
          导出日趋势 XLSX
        </Button>
        <Button
          className="admin-report-hourly-trend-xlsx-export-action"
          disabled={isAnyTrendExporting}
          icon={<DownloadOutlined />}
          loading={isTrendXlsxExporting === 'hourly'}
          onClick={() => onExportXlsx('hourly')}
        >
          导出小时趋势 XLSX
        </Button>
        <Button
          className="admin-report-monthly-trend-xlsx-export-action"
          disabled={isAnyTrendExporting}
          icon={<DownloadOutlined />}
          loading={isTrendXlsxExporting === 'monthly'}
          onClick={() => onExportXlsx('monthly')}
        >
          导出月趋势 XLSX
        </Button>
      </Space>
    </Flex>
  )
}
