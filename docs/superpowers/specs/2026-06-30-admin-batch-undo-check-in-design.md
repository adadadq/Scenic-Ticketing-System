# 后台批量撤销核销 API 设计

日期：2026-06-30

## 1. 问题

后台已经支持单张撤销核销和批量核销。现场运营如果发现一批误扫票码，目前只能逐张调用撤销接口；前端也无法一次展示一批撤销的成功和失败结果。

本切片在单张撤销状态机上增加批量入口，让前端提交一组票码并得到逐票结果，同时继续复用单张撤销的权限、CSRF、库存核销量回退和审计边界。

## 2. 范围

本切片只做：

- 新增 `POST /api/admin/check-ins/batch/undo`。
- 请求体接收 `ticketCodes`，至少 1 个、最多 50 个。
- 去除每个票码首尾空白，拒绝空票码、重复票码和额外字段。
- 每张票独立执行现有单张撤销核销规则。
- 返回逐票结果，业务失败不影响同批其他票码。
- 成功票码继续写入 `check_in_audit_log`，动作仍为 `UNDO_CHECK_IN`。

本切片不做：

- 撤销原因、审批流或二次确认状态。
- 失败撤销尝试审计。
- 异步任务、导入文件、扫码设备集成或批量任务历史。
- 撤销退款、改签、补票或真实支付渠道同步。
- 前端页面或扫码交互实现。

## 3. API

```text
POST /api/admin/check-ins/batch/undo
```

请求体：

```json
{
  "ticketCodes": ["TK001", "TK002"]
}
```

成功响应 `AdminBatchUndoCheckInDTO`：

- `totalCount`
- `successCount`
- `failureCount`
- `results[]`

`results[]` 中每项为 `AdminBatchUndoCheckInResultDTO`：

- `ticketCode`
- `success`
- `undoCheckIn`：成功时为 `AdminUndoCheckInDTO`。
- `code`：失败时为业务错误码。
- `message`：失败时为业务错误信息。

## 4. 状态机

每个票码复用单张撤销允许条件：

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

业务失败进入当前票码结果，不中断同批其他票码：

- 票码不存在：`TICKET_NOT_FOUND`
- 票码未核销：`TICKET_NOT_CHECKED_IN`
- 订单或支付状态不允许撤销：`TICKET_UNDO_NOT_ALLOWED`

未知异常、数据库连接失败或非业务错误仍走统一失败响应，不返回逐票成功壳。

## 5. 权限与 CSRF

- 只接受管理员 session。
- 未登录返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是状态变更接口，必须通过 double-submit CSRF。
- 已登录管理员还必须通过 session-bound CSRF。
- 请求体拒绝额外字段；前端不能提交 `adminUserId`、`orderId`、`itemStatus`、库存字段、撤销时间或审计动作。

## 6. 数据与并发

- 每张票码调用现有 repository 单张撤销路径。
- 单张撤销路径继续在事务内锁定目标票项和订单，并用条件更新保护 `quota_checked_in` 不会小于 0。
- 同一批请求中重复票码在 DTO 层拒绝，避免重复回退核销量。
- 跨请求重复撤销沿用单张撤销的 `TICKET_NOT_CHECKED_IN` 保护。
- 响应不返回完整手机号、证件号、session、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## 7. 验收

目标测试：

```bash
.venv/bin/pytest backend/tests/test_admin_check_in_api.py backend/tests/test_openapi_contract.py -q
```

提交前验收：

```bash
scripts/verify-integration.sh
```

必须覆盖：

- 管理员携带 CSRF 可批量撤销多张 `USED` 票码。
- 同批业务失败逐票返回，不影响其他票码成功。
- 缺 CSRF、匿名、游客 session 不能批量撤销。
- 请求体拒绝重复票码、空票码和额外字段。
- 重复撤销不能重复减少 `quota_checked_in`。
- 成功票码写入现有核销审计日志。
- 系统异常不会被转换为逐票业务结果。
- OpenAPI 声明批量撤销 POST 响应 DTO 和必需 CSRF header。
