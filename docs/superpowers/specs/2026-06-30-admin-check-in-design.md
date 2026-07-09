# 后台票码核销 API 设计

日期：2026-06-30

## 1. 问题

游客购票闭环已经能生成票码，后台订单只读 API 已经能让管理员查看订单和票码。但真实运营工作流还需要现场核销：工作人员扫描或输入票码后，把已支付未使用的票标记为已使用，并把时段已核销量增加。

核销是第二阶段第一个订单状态变更能力，必须显式定义状态机、权限、CSRF 和失败边界。

## 2. 范围

本切片只做：

- 管理员按票码核销单张票。
- `ticket_order_item.item_status` 从 `UNUSED` 变为 `USED`。
- `time_slot_quota.quota_checked_in` 增加 1。
- 当订单下所有明细都为 `USED` 时，订单从 `PAID` 变为 `COMPLETED`。
- 返回后台核销 DTO，供前端展示核销结果。

本切片不做：

- 批量核销。
- 退款、撤销核销、改签、补票。
- 审计日志表。
- 角色权限细分；`SUPER_ADMIN` 与 `OPERATOR` 都可核销。
- 前端扫码页面或 React 组件。

## 3. API

```text
POST /api/admin/check-ins
```

请求体：

```json
{
  "ticketCode": "TKRANDOMABC123"
}
```

成功响应 `AdminCheckInDTO`：

- `orderNo`
- `itemNo`
- `ticketCode`
- `orderStatus`
- `itemStatus`
- `checkedInAt`

## 4. 状态机

允许：

```text
order_status = PAID
payment_status = PAID 或 PARTIAL_REFUND
item_status = UNUSED
ticket_code = 请求 ticketCode
```

成功后：

```text
item_status: UNUSED -> USED
time_slot_quota.quota_checked_in += 1
如果订单没有剩余非 USED 明细：
  order_status: PAID -> COMPLETED
否则：
  order_status 保持 PAID
```

已退款明细视为不再可核销，也不阻塞“剩余可用票项全部核销后订单完成”的判断。

拒绝：

- 票码不存在：`404 TICKET_NOT_FOUND`，消息“票码不存在”。
- 明细已核销：`409 TICKET_ALREADY_USED`，消息“票码已核销”。
- 订单或明细状态不允许核销：`409 TICKET_NOT_CHECKABLE`，消息“当前票码不可核销”。

## 5. 权限与 CSRF

- 只接受管理员 session。
- 未登录返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是状态变更接口，必须通过 double-submit CSRF。
- 已登录管理员还必须通过 session-bound CSRF。
- 请求体拒绝额外字段；前端不能提交 `adminUserId`、`orderId`、`itemStatus` 或库存字段。

## 6. 数据与并发

- repository 在事务内锁定目标 `ticket_order_item` 和对应 `ticket_order`。
- 只有当前状态为 `UNUSED` 且订单为 `PAID + PAID` 时才更新。
- `quota_checked_in` 增加 1，受数据库约束 `quota_checked_in <= quota_sold` 保护。
- 重复提交同一票码不能重复增加 `quota_checked_in`。
- 响应不返回完整手机号、证件号、session、CSRF token、密码 hash、数据库内部 id 或审计字段。

## 7. 验收

目标测试：

```bash
.venv/bin/pytest backend/tests/test_admin_check_in_api.py backend/tests/test_openapi_contract.py -q
```

提交前验收：

```bash
scripts/verify-backend.sh
scripts/verify-integration.sh
```

必须覆盖：

- 管理员携带 CSRF 可核销 `UNUSED` 票码。
- 缺 CSRF、匿名、游客 session 不能核销。
- 重复核销返回 `TICKET_ALREADY_USED`，不重复增加 `quota_checked_in`。
- 未支付、取消、已退款或无票码明细不能核销。
- 部分退款后剩余 `UNUSED` 票码仍可核销。
- 订单所有未退款明细核销后变为 `COMPLETED`。
- OpenAPI 声明 POST 响应 DTO 和必需 CSRF header。
