# 后台部分模拟退款 API 设计

日期：2026-06-30

## 1. 问题

整单退款只能处理全部未使用票项一起退款的场景。后台运营还需要对同一订单里的部分票项做模拟退款，同时保证订单金额、票项状态和库存售出量不会被客户端篡改。

## 2. 范围

本切片只做：

- 管理员按票项号对已支付订单执行部分模拟退款。
- 请求体只接受 `itemNos` 和可选 `reason`。
- 仅允许订单为 `order_status = PAID`，且 `payment_status` 为 `PAID` 或 `PARTIAL_REFUND`。
- 仅允许订单内非退款票项处于 `UNUSED`，被选中的票项必须是 `UNUSED`。
- 退款金额由后端根据锁定后的订单明细 `final_price` 计算。
- 成功后所选明细变为 `REFUNDED`，按所选票项回补 `quota_sold`。
- 若订单仍有未退款票项，订单保持 `PAID`，支付状态变为 `PARTIAL_REFUND`。
- 若订单所有票项都已退款，订单和支付状态变为 `REFUNDED`，成功支付记录标记为 `REFUNDED`。

本切片不做：

- 已核销票项退款。
- 退款通知、真实第三方退款或真实财务对账。
- 独立退款审计日志表。
- 前端页面或 React 组件。

## 3. API

```text
POST /api/admin/orders/{order_no}/refund/items
```

请求体：

```json
{
  "itemNos": ["I-202606300001"],
  "reason": "游客只退一张"
}
```

响应 `data` 为 `AdminPartialRefundDTO`：

- `orderNo`
- `orderStatus`
- `paymentStatus`
- `refundedAmount`
- `refundedItemCount`
- `refundedItemNos`
- `refundedAt`

## 4. 权限与错误

- 只允许管理员 session 调用。
- 必须校验 session-bound CSRF。
- 订单不存在返回 `404 ADMIN_ORDER_NOT_FOUND`。
- 订单已退款返回 `409 ORDER_ALREADY_REFUNDED`。
- 票项不属于该订单返回 `409 ORDER_REFUND_ITEMS_INVALID`。
- 状态不可部分退款返回 `409 ORDER_NOT_PARTIALLY_REFUNDABLE`。
- 请求体拒绝额外字段、空票项号和重复票项号。

## 5. 安全与事务

- 客户端不能提交退款金额、订单状态、支付状态或库存数量。
- 仓储层在一个事务内锁定订单、订单明细和成功支付记录。
- SQL 只使用参数传入 `order_no` 和 `itemNos`，动态 SQL 只生成占位符数量，不拼接原始票项号。
- 库存回补使用 `quota_sold - quantity >= quota_checked_in` 条件保护，避免回补到小于已核销量。
- 响应不返回完整手机号、证件号、session、CSRF token、密码 hash、数据库内部 id 或审计字段。

## 6. 验收

```bash
.venv/bin/pytest backend/tests/test_admin_refund_api.py backend/tests/test_openapi_contract.py -q
scripts/verify-integration.sh
```

验收点：

- 管理员携带 CSRF 可按票项部分退款。
- 缺 CSRF、匿名、游客 session 不能部分退款。
- 不存在、已退款、未支付、已核销、票项不属于订单都有稳定错误码。
- DTO 不泄露敏感字段。
- OpenAPI 声明成功 DTO 和必需 CSRF header。
- SQL 层覆盖锁、参数绑定、库存回补和失败前不产生副作用。
