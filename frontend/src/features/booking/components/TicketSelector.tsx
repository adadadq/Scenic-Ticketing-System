import { Alert, Badge, Button, Card, Empty, Space, Table, Tag, Typography } from 'antd'
import { CustomerServiceOutlined, SmileOutlined } from '@ant-design/icons'
import type { TableProps } from 'antd'
import { ApiErrorDetails } from '../../../shared/components/ApiErrorDetails'
import type { TicketProduct } from '../types'

const { Text } = Typography

function getTagColor(tag: string) {
  if (tag === '推荐') {
    return 'green'
  }

  if (tag === '售罄' || tag === '暂停') {
    return 'red'
  }

  return 'orange'
}

function getReferenceAudience(product: TicketProduct) {
  if (product.name.includes('成人')) {
    return '18周岁（含）以上'
  }

  if (product.name.includes('儿童')) {
    return '6周岁（含）- 18周岁（不含）'
  }

  return product.audience
}

function getReferenceTicketClass(product: TicketProduct) {
  return product.name.includes('儿童') ? 'child' : product.name.includes('成人') ? 'adult' : product.key
}

const columns: TableProps<TicketProduct>['columns'] = [
  {
    title: '票种名称',
    dataIndex: 'name',
    render: (name: string, row) => (
      <Space>
        <Badge status={row.key === 'adult' ? 'processing' : 'default'} />
        <Text strong>{name}</Text>
        {row.tag ? <Tag color={getTagColor(row.tag)}>{row.tag}</Tag> : null}
      </Space>
    ),
  },
  {
    title: '适用范围',
    dataIndex: 'audience',
    responsive: ['md'],
  },
  {
    title: '包含内容',
    dataIndex: 'content',
    responsive: ['lg'],
  },
  {
    title: '优惠价',
    dataIndex: 'salePrice',
    align: 'right',
    render: (price: number) => <Text className="price">¥{price}</Text>,
  },
]

type TicketSelectorProps = {
  isLoading: boolean
  onSelectProduct: (productKey: string) => void
  products: TicketProduct[]
  selectedProductQuantities: Record<string, number>
  usesProductFallback: boolean
  productError: unknown
}

export function TicketSelector({
  isLoading,
  onSelectProduct,
  products,
  productError,
  selectedProductQuantities,
  usesProductFallback,
}: TicketSelectorProps) {
  const hasProducts = products.length > 0
  const selectedProductKeys = Object.keys(selectedProductQuantities)

  return (
    <Card title="选择票种" extra={<Button type="link">票种说明</Button>} className="workspace-card booking-selector-card">
      <Table
        className="ticket-table"
        rowSelection={{
          selectedRowKeys: selectedProductKeys,
          onSelect: (product) => onSelectProduct(product.key),
          getCheckboxProps: (product) => ({ disabled: product.disabled }),
        }}
        columns={columns}
        dataSource={products}
        locale={{
          emptyText: (
            <Empty
              description={isLoading ? '票种加载中' : '暂无可售票种'}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ),
        }}
        loading={isLoading}
        pagination={false}
      />

      {usesProductFallback ? (
        <Alert
          className="catalog-alert"
          showIcon
          type="warning"
          title="暂时无法提交订单"
          description={(
            <ApiErrorDetails
              error={productError}
              fallback="票务服务暂时不稳定，请稍后重试。"
              supportingText="当前可先查看票种，提交订单请稍后再试。"
            />
          )}
        />
      ) : null}

      <div className="ticket-card-list" role="group" aria-label="选择票种">
        {hasProducts ? (
          products.map((product) => {
            const isSelected = Boolean(selectedProductQuantities[product.key])

            return (
              <button
                aria-checked={isSelected}
                className={`${isSelected ? 'ticket-card active' : 'ticket-card'} ticket-card-${getReferenceTicketClass(product)}`}
                disabled={product.disabled}
                key={product.key}
                onClick={() => onSelectProduct(product.key)}
                role="checkbox"
                type="button"
              >
                <span className="ticket-card-radio" />
                <span className="ticket-card-art" aria-hidden="true" />
                <span className="ticket-card-main">
                  <span className="ticket-card-heading">
                    <Text className="ticket-card-title" strong title={product.name}>{product.name}</Text>
                    {product.tag ? (
                      <Tag color={getTagColor(product.tag)}>{product.tag}</Tag>
                    ) : null}
                  </span>
                  <Text type="secondary">{getReferenceAudience(product)}</Text>
                  <span className="ticket-card-feature-row">
                    <span><CustomerServiceOutlined />竹筏漂流</span>
                    <span><SmileOutlined />风景游览</span>
                  </span>
                </span>
                <Text className="ticket-card-price price">¥{product.salePrice}<small>/人</small></Text>
              </button>
            )
          })
        ) : (
          <div className="booking-empty-panel">
            <Empty
              description={isLoading ? '票种加载中' : '暂无可售票种'}
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </div>
        )}
      </div>
    </Card>
  )
}
