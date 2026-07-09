import { CalendarOutlined, CloseCircleOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons'
import { Button, Flex, Input, Segmented, Typography } from 'antd'
import type { OrderStatusFilterValue } from '../types'

const { Text } = Typography

type OrderStatusFiltersProps = {
  filteredOrderCount: number
  isLoading: boolean
  isRefreshing: boolean
  keyword: string
  onClearFilters: () => void
  onKeywordChange: (keyword: string) => void
  onRefreshOrders: () => void
  onStatusFilterChange: (status: OrderStatusFilterValue) => void
  onVisitDateFilterChange: (visitDate: string) => void
  statusFilter: OrderStatusFilterValue
  statusFilterOptions: Array<{ label: string; value: OrderStatusFilterValue }>
  totalOrderCount: number
  visitDateFilter: string
}

export function OrderStatusFilters({
  filteredOrderCount,
  isLoading,
  isRefreshing,
  keyword,
  onClearFilters,
  onKeywordChange,
  onRefreshOrders,
  onStatusFilterChange,
  onVisitDateFilterChange,
  statusFilter,
  statusFilterOptions,
  totalOrderCount,
  visitDateFilter,
}: OrderStatusFiltersProps) {
  const activeStatusLabel = statusFilterOptions.find((option) => option.value === statusFilter)?.label ?? '全部'
  const hasSearchFilters = Boolean(keyword.trim() || visitDateFilter)
  const resultSummary = isLoading
    ? `当前状态：${activeStatusLabel} · 订单加载中`
    : `当前状态：${activeStatusLabel} · 显示 ${filteredOrderCount} / ${totalOrderCount} 笔订单`

  return (
    <div className="orders-toolbar" aria-label="订单筛选">
      <Flex className="orders-toolbar-row" gap={12} justify="space-between" wrap>
        <Segmented
          className="orders-status-filter"
          options={statusFilterOptions}
          value={statusFilter}
          onChange={(value) => onStatusFilterChange(value as OrderStatusFilterValue)}
        />

        <div className="orders-filter-tools">
          <Input
            allowClear
            className="orders-search"
            onChange={(event) => onKeywordChange(event.target.value)}
            placeholder="搜索订单号"
            prefix={<SearchOutlined />}
            value={keyword}
          />
          <Input
            aria-label="按游览日期筛选"
            className="orders-date-filter"
            onChange={(event) => onVisitDateFilterChange(event.target.value)}
            prefix={<CalendarOutlined />}
            type="date"
            value={visitDateFilter}
          />
          <Button
            className="orders-clear-filters"
            disabled={!hasSearchFilters}
            icon={<CloseCircleOutlined />}
            onClick={onClearFilters}
          >
            清空筛选
          </Button>
          <Button
            className="orders-refresh"
            icon={<ReloadOutlined />}
            loading={isRefreshing}
            onClick={onRefreshOrders}
          >
            刷新
          </Button>
        </div>
      </Flex>

      <Flex className="orders-filter-summary" gap={8} justify="space-between" wrap>
        <Text type="secondary">{resultSummary}</Text>
        <Text className="orders-filter-hint" type="secondary">
          {hasSearchFilters ? '搜索或日期筛选已生效' : '可按订单号或游览日期快速定位'}
        </Text>
      </Flex>
    </div>
  )
}
