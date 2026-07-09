# 后台全单模拟退款 API 设计

日期：2026-06-30

## 1. 问题

游客支付成功后，后台需要处理运营退款。当前系统已有模拟支付、票码核销和后台订单只读能力，但还没有退款状态机。退款会同时影响订单状态、明细状态、支付状态和库存售出量，因此必须先做一个边界清晰的最小切片。

## 2. 范围

本切片只做：

- 管理员对整单执行模拟退款。
- 仅允许 `order_status = PAID`、`payment_status = PAID` 且所有明细为 `UNUSED` 的订单退款。
- 退款成功后：
  - 明细状态变为 `REFUNDED`。
  - 订单 `order_status` 与 `payment_status` 变为 `REFUNDED`。
  - `paid_amount` 归零。
  - 对应时段 `quota_sold` 按票数回补。
  - 相关成功支付记录标记为 `REFUNDED`。
- 返回后台退款 DTO。

本切片不做：

- 部分退款。
- 已核销票退款。
- 撤销核销。
- 真实第三方退款回调。
- 退款审计日志表。
- 前端页面或 React 组件。

## 3. API

```text
POST /api/admin/orders/{order_no}/refund
```

请求体：

```json
{
  "reason": "游客申请退款"
}
```

`reason` 可选，最多 100 个字符；当前只进入请求契约，不写入数据库审计表。

成功响应 `AdminRefundDTO`：

- `orderNo`
- `orderStatus`
- `paymentStatus`
- `refundedAmount`
- `refundedItemCount`
- `refundedAt`

## 4. 状态机

允许：

```text
order_status = PAID
payment_status = PAID
所有 item_status = UNUSED
存在 payment_record.payment_status = SUCCESS
```

成功后：

```text
ticket_order_item.item_status: UNUSED -> REFUNDED
ticket_order.order_status: PAID -> REFUNDED
ticket_order.payment_status: PAID -> REFUNDED
ticket_order.paid_amount: paid_amount -> 0
payment_record.payment_status: SUCCESS -> REFUNDED
time_slot_quota.quota_sold -= 对应票数
```

拒绝：

- 订单不存在：`404 ADMIN_ORDER_NOT_FOUND`，消息“订单不存在”。
- 订单已退款：`409 ORDER_ALREADY_REFUNDED`，消息“订单已退款”。
- 订单状态或明细状态不可退款：`409 ORDER_NOT_REFUNDABLE`，消息“当前订单不可退款”。

## 5. 权限与 CSRF

- 只接受管理员 session。
- 未登录返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是状态变更接口，必须通过 double-submit CSRF。
- 已登录管理员还必须通过 session-bound CSRF。
- 请求体拒绝额外字段；前端不能提交 `adminUserId`、`orderStatus`、`paymentStatus`、`paidAmount` 或库存字段。

## 6. 数据与并发

- repository 在事务内锁定订单和订单明细。
- 先确认订单、所有明细和成功支付记录满足退款前置条件，再回补库存。
- `quota_sold` 回补使用条件更新，不能小于 `quota_checked_in`。
- 退款失败时不能更新明细、订单、支付记录或库存。
- 响应不返回完整手机号、证件号、session、CSRF token、密码 hash、数据库内部 id 或审计字段。

## 7. 验收

目标测试：

```bash
.venv/bin/pytest backend/tests/test_admin_refund_api.py backend/tests/test_openapi_contract.py -q
```

提交前验收：

```bash
scripts/verify-backend.sh
scripts/verify-integration.sh
```

必须覆盖：

- 管理员携带 CSRF 可退款整单。
- 缺 CSRF、匿名、游客 session 不能退款。
- 已退款订单不能重复退款。
- 未支付、取消、已核销或部分异常明细不能退款。
- 库存回补条件失败时不能继续更新订单或支付记录。
- OpenAPI 声明 POST 响应 DTO 和必需 CSRF header。
