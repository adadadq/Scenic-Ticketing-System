# 后台订单只读 API 设计

日期：2026-06-30

## 1. 问题

管理员认证基座已经完成，但后台页面还没有订单数据面。前端管理台如果直接复用游客订单接口，会遇到两个问题：

- 游客接口只允许当前游客查看自己的订单，不适合后台跨订单检索。
- 游客 `OrderMeDTO` 会按游客场景组织字段，无法表达后台列表的筛选、分页和运营摘要。

本切片先补后台订单只读 API，为后续核销、退款和报表提供安全的查询基础。

## 2. 范围

本切片只做：

- 管理员订单列表查询。
- 管理员订单详情查询。
- 管理员订单只读 DTO。
- 订单状态、支付状态、订单号、手机号和分页查询参数。
- OpenAPI、API 契约、安全清单、测试证据同步。

本切片不做：

- 核销、退款、改价、补票、关闭订单或任何订单状态变更。
- 管理端页面、React 组件或样式。
- 导出报表。
- 管理员角色细分权限矩阵。

## 3. API

```text
GET /api/admin/orders
GET /api/admin/orders/{order_no}
```

`GET /api/admin/orders` 支持查询参数：

- `status`：可选订单状态，允许 `CREATED`、`PAID`、`CANCELLED`、`COMPLETED`、`REFUNDING`、`REFUNDED`。
- `paymentStatus`：可选支付状态，允许 `UNPAID`、`PAID`、`PARTIAL_REFUND`、`REFUNDED`、`FAILED`。
- `orderNo`：可选订单号模糊匹配，1 到 64 字符。
- `buyerPhone`：可选手机号查询，允许完整手机号或后四位，前后空白会去掉。
- `page`：默认 1，最小 1。
- `pageSize`：默认 20，范围 1 到 100。

## 4. DTO

后台 DTO 单独定义，不复用游客 `OrderMeDTO`。

`AdminOrderListDTO`：

- `items: AdminOrderSummaryDTO[]`
- `total`
- `page`
- `pageSize`

`AdminOrderSummaryDTO`：

- `orderNo`
- `visitorId`
- `buyerName`
- `buyerPhoneMasked`
- `orderStatus`
- `paymentStatus`
- `totalAmount`
- `payableAmount`
- `orderTime`
- `itemCount`

`AdminOrderDetailDTO`：

- 包含 summary 的核心字段。
- `items: AdminOrderItemDTO[]`

`AdminOrderItemDTO`：

- `itemNo`
- `productId`
- `ticketTypeId`
- `productName`
- `ticketName`
- `timeSlotId`
- `visitDate`
- `slotStartTime`
- `slotEndTime`
- `originalPrice`
- `finalPrice`
- `itemStatus`
- `ticketCode`

## 5. 权限与安全

- 两个接口都只接受管理员 session。
- 未登录返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 访问返回 `403 ADMIN_FORBIDDEN`。
- 两个接口都是 GET，只读，不要求 CSRF。
- 响应不返回证件号、session token、CSRF token、密码 hash 或数据库内部审计字段。
- 列表和详情都只返回 `buyerPhoneMasked`，不返回完整手机号；后续如确需完整手机号，应单独做权限和审计设计。
- 查询参数不拼接原始 SQL；repository 使用固定 SQL 片段和参数绑定。

## 6. 错误码

- 非法 `status`：`422 ADMIN_ORDER_STATUS_INVALID`。
- 非法 `paymentStatus`：`422 ADMIN_PAYMENT_STATUS_INVALID`。
- 订单不存在：`404 ADMIN_ORDER_NOT_FOUND`，消息为“订单不存在”。
- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`。
- 游客 session 访问：`403 ADMIN_FORBIDDEN`。

## 7. 验收

目标测试：

```bash
.venv/bin/pytest backend/tests/test_admin_orders_api.py backend/tests/test_openapi_contract.py -q
```

提交前验收：

```bash
scripts/verify-backend.sh
scripts/verify-integration.sh
```

必须覆盖：

- 管理员可以分页查询订单列表，响应不包含完整手机号和敏感字段。
- 管理员可以查看订单详情和票码。
- 未登录、游客 session 不能访问后台订单接口。
- 非法状态筛选返回专用错误码。
- OpenAPI 200 响应声明 `ApiSuccessDTO<AdminOrderListDTO>` 和 `ApiSuccessDTO<AdminOrderDetailDTO>`。
- `docs/api-contract.md` endpoint 清单与后端 OpenAPI 一致。
