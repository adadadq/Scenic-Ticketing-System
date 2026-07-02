import { Alert, Badge, Button, Card, Empty, Space, Table, Tag, Typography } from 'antd'
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
  selectedProduct?: TicketProduct
  usesProductFallback: boolean
  productError: unknown
}

export function TicketSelector({
  isLoading,
  onSelectProduct,
  products,
  productError,
  selectedProduct,
  usesProductFallback,
}: TicketSelectorProps) {
  const hasProducts = products.length > 0

  return (
    <Card title="选择票种" extra={<Button type="link">票种说明</Button>} className="workspace-card booking-selector-card">
      <Table
        className="ticket-table"
        rowSelection={{
          type: 'radio',
          selectedRowKeys: selectedProduct ? [selectedProduct.key] : [],
          onChange: (keys) => onSelectProduct(String(keys[0])),
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
          title="票品接口暂不可用，当前展示演示票种"
          description={(
            <ApiErrorDetails
              error={productError}
              fallback="无法读取真实票品，请稍后重试。"
              supportingText="当前仅可浏览演示数据，不能创建订单；创建订单前需要真实票品接口恢复。"
            />
          )}
        />
      ) : null}

      <div className="ticket-card-list">
        {hasProducts ? (
          products.map((product) => (
            <button
              className={product.key === selectedProduct?.key ? 'ticket-card active' : 'ticket-card'}
              disabled={product.disabled}
              key={product.key}
              onClick={() => onSelectProduct(product.key)}
              type="button"
            >
              <span className="ticket-card-radio" />
              <span className="ticket-card-main">
                <span className="ticket-card-heading">
                  <Text className="ticket-card-title" strong title={product.name}>{product.name}</Text>
                  {product.tag ? (
                    <Tag color={getTagColor(product.tag)}>{product.tag}</Tag>
                  ) : null}
                </span>
                <Text type="secondary">{product.audience}</Text>
                <Text type="secondary">{product.content}</Text>
              </span>
              <Text className="price">¥{product.salePrice}</Text>
            </button>
          ))
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
