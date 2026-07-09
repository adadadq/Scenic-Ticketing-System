# 后台批量核销 API 设计

日期：2026-06-30

## 1. 问题

后台已经支持单张票码核销、核销审计日志、全局检索和 CSV 导出。现场运营如果连续扫码多张票，目前只能逐次调用单张接口；前端无法一次展示一批票码的成功和失败结果。

本切片在现有单张核销状态机上增加批量入口，让前端可以提交一组票码并得到逐票结果，同时继续复用单张核销的权限、CSRF、库存计数和审计边界。

## 2. 范围

本切片只做：

- 新增 `POST /api/admin/check-ins/batch`。
- 请求体接收 `ticketCodes`，最多 50 个。
- 去除每个票码首尾空白，拒绝空票码和重复票码。
- 每张票独立执行现有单张核销规则。
- 返回逐票结果，业务失败不影响同批其他票码。
- 成功票码继续写入 `check_in_audit_log`，动作仍为 `CHECK_IN`。

本切片不做：

- 撤销核销。
- 批量任务、异步队列、导入文件或扫码设备集成。
- 失败核销尝试审计。
- 角色权限细分。
- 前端页面或扫码交互实现。

## 3. API

```text
POST /api/admin/check-ins/batch
```

请求体：

```json
{
  "ticketCodes": ["TK001", "TK002"]
}
```

成功响应 `AdminBatchCheckInDTO`：

- `totalCount`
- `successCount`
- `failureCount`
- `results[]`

`results[]` 中每项为 `AdminBatchCheckInResultDTO`：

- `ticketCode`
- `success`
- `checkIn`：成功时为 `AdminCheckInDTO`。
- `code`：失败时为业务错误码。
- `message`：失败时为业务错误信息。

## 4. 状态机

每个票码复用单张核销允许条件：

```text
order_status = PAID
payment_status = PAID 或 PARTIAL_REFUND
item_status = UNUSED
ticket_code = 当前票码
```

成功后：

```text
item_status: UNUSED -> USED
time_slot_quota.quota_checked_in += 1
如果订单没有剩余非 USED/REFUNDED 明细：
  order_status: PAID -> COMPLETED
否则：
  order_status 保持 PAID
```

业务失败进入当前票码结果，不中断同批其他票码：

- 票码不存在：`TICKET_NOT_FOUND`
- 明细已核销：`TICKET_ALREADY_USED`
- 订单或明细状态不允许核销：`TICKET_NOT_CHECKABLE`

未知异常、数据库连接失败或非业务错误仍走统一失败响应，不返回逐票成功壳。

## 5. 权限与 CSRF

- 只接受管理员 session。
- 未登录返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是状态变更接口，必须通过 double-submit CSRF。
- 已登录管理员还必须通过 session-bound CSRF。
- 请求体拒绝额外字段；前端不能提交 `adminUserId`、`orderId`、`itemStatus`、库存字段或每票操作人。

## 6. 数据与并发

- 每张票码调用现有 repository 单张核销路径。
- 单张核销路径继续在事务内锁定目标票项和订单，并用条件更新保护 `quota_checked_in <= quota_sold`。
- 同一批请求中重复票码在 DTO 层拒绝，避免重复增加核销量。
- 跨请求重复票码沿用单张核销的 `TICKET_ALREADY_USED` 保护。
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

- 管理员携带 CSRF 可批量核销多张 `UNUSED` 票码。
- 同批业务失败逐票返回，不影响其他票码成功。
- 缺 CSRF、匿名、游客 session 不能批量核销。
- 请求体拒绝重复票码、空票码和额外字段。
- 重复票码不能重复增加 `quota_checked_in`。
- 成功票码写入现有核销审计日志。
- OpenAPI 声明批量 POST 响应 DTO 和必需 CSRF header。
