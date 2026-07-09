# 后台撤销核销 API 设计

日期：2026-06-30

## 1. 问题

后台已经支持单张核销、批量核销和核销审计。现场运营中偶尔会出现误扫、误输入票码或重复演练造成的误核销。当前系统只能把 `UNUSED` 票项改为 `USED`，无法在仍然安全的业务范围内恢复票项状态。

本切片增加最小撤销核销能力，让管理员可以把已核销票码恢复为未使用，并把时段核销量回退，同时在现有核销审计日志中留下撤销动作。

## 2. 范围

本切片只做：

- 新增 `POST /api/admin/check-ins/{ticket_code}/undo`。
- 只允许撤销当前 `item_status = USED` 的票码。
- 只允许订单仍处于有效支付态：`payment_status = PAID` 或 `PARTIAL_REFUND`，且 `order_status = PAID` 或 `COMPLETED`。
- 成功后票项从 `USED` 恢复为 `UNUSED`。
- 成功后 `time_slot_quota.quota_checked_in` 减 1，并保证不会小于 0。
- 如果订单原本是 `COMPLETED`，撤销后回退为 `PAID`；原本是 `PAID` 则保持 `PAID`。
- 在 `check_in_audit_log` 写入 `UNDO_CHECK_IN` 动作。
- 返回专用 `AdminUndoCheckInDTO`，供前端展示撤销结果。

本切片不做：

- 批量撤销核销已由后续切片单独建模。
- 撤销原因、审批流或二次确认状态。
- 失败尝试审计。
- 撤销退款、改签、补票或真实支付渠道同步。
- 前端页面或扫码设备集成。

## 3. API

```text
POST /api/admin/check-ins/{ticket_code}/undo
```

请求体为空；票码来自 path。

成功响应 `AdminUndoCheckInDTO`：

- `orderNo`
- `itemNo`
- `ticketCode`
- `orderStatus`
- `itemStatus`
- `undoneAt`

## 4. 状态机

允许：

```text
item_status = USED
order_status = PAID 或 COMPLETED
payment_status = PAID 或 PARTIAL_REFUND
```

成功后：

```text
item_status: USED -> UNUSED
time_slot_quota.quota_checked_in -= 1
如果 order_status = COMPLETED:
  order_status: COMPLETED -> PAID
如果 order_status = PAID:
  order_status 保持 PAID
```

拒绝：

- 票码不存在：`404 TICKET_NOT_FOUND`，消息“票码不存在”。
- 票码不是已核销状态：`409 TICKET_NOT_CHECKED_IN`，消息“票码未核销”。
- 订单或支付状态不允许撤销：`409 TICKET_UNDO_NOT_ALLOWED`，消息“当前票码不可撤销核销”。

## 5. 权限与 CSRF

- 只接受管理员 session。
- 未登录返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是状态变更接口，必须通过 double-submit CSRF。
- 已登录管理员还必须通过 session-bound CSRF。
- 前端不能提交 `adminUserId`、`orderId`、`itemStatus`、库存字段、撤销时间或审计动作。

## 6. 数据与并发

- repository 在事务内锁定目标 `ticket_order_item` 和对应 `ticket_order`。
- 更新票项时带条件 `item_status = 'USED'`。
- 更新核销量时带条件 `quota_checked_in - 1 >= 0`。
- 成功撤销与写入 `UNDO_CHECK_IN` 审计日志在同一事务内完成。
- 撤销失败不写审计副作用。
- 审计日志 DTO 和 CSV 继续只返回安全字段，不返回完整手机号、证件号、session、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## 7. 验收

目标测试：

```bash
.venv/bin/pytest backend/tests/test_admin_check_in_api.py backend/tests/test_schema_contract.py backend/tests/test_openapi_contract.py -q
```

提交前验收：

```bash
scripts/verify-integration.sh
```

必须覆盖：

- 管理员携带 CSRF 可撤销已核销票码。
- 撤销后票项恢复为 `UNUSED`，核销量减 1，`COMPLETED` 订单回退为 `PAID`。
- 匿名、游客 session、缺 CSRF 或缺 session-bound CSRF 不能撤销。
- 未核销、缺失、退款/取消等不可撤销状态返回稳定错误码。
- 撤销成功写入 `UNDO_CHECK_IN` 审计日志，失败不写审计日志。
- OpenAPI 声明撤销 POST 响应 DTO 和必需 CSRF header。
- `database/schema.sql` 允许 `CHECK_IN` 和 `UNDO_CHECK_IN` 两类核销审计动作。
