# 后台撤销核销失败尝试审计设计

日期：2026-07-01

## 问题定义

后台已经记录成功核销、成功撤销核销和核销业务失败尝试。撤销核销失败同样有安全和运营排查价值：重复撤销、尝试撤销未核销票码、或对不可撤销状态的票码做撤销，可能来自误操作、流程培训问题或异常操作尝试。本切片补齐撤销核销业务失败尝试审计，并复用现有失败审计检索能力。

## 边界

本切片实现：

- 复用 `check_in_failure_audit_log` 表，`action` 扩展为 `CHECK_IN` 和 `UNDO_CHECK_IN`。
- 失败码扩展为核销失败码和撤销失败码：`TICKET_NOT_FOUND`、`TICKET_ALREADY_USED`、`TICKET_NOT_CHECKABLE`、`TICKET_NOT_CHECKED_IN`、`TICKET_UNDO_NOT_ALLOWED`。
- 单张撤销 `POST /api/admin/check-ins/{ticket_code}/undo` 在管理员权限和 CSRF 校验通过后，如果失败原因为 `TICKET_NOT_FOUND`、`TICKET_NOT_CHECKED_IN` 或 `TICKET_UNDO_NOT_ALLOWED`，写入失败审计。
- 批量撤销 `POST /api/admin/check-ins/batch/undo` 对每个逐票业务失败写入失败审计。
- 现有 `GET /api/admin/check-in-failure-logs` 返回 `action`，前端可据此区分核销失败和撤销失败。
- 给已有运行库新增幂等迁移，扩展 `check_in_failure_audit_log` 的 action 和 failure_code 约束。

本切片不实现：

- 新增单独的撤销失败日志表或新检索端点。
- 系统异常、数据库异常或上游不可用的失败审计。
- CSV/XLSX 导出、异步导出、失败趋势报表、自动风控或告警。
- 撤销原因、审批流、人工复核流。
- 前端页面或扫码设备集成。

## API 契约

复用现有接口：

```text
GET /api/admin/check-in-failure-logs?failureCode=TICKET_NOT_CHECKED_IN&page=1&pageSize=20
```

成功响应中撤销失败记录示例：

```json
{
  "ticketCode": "TK-UNUSED",
  "action": "UNDO_CHECK_IN",
  "failureCode": "TICKET_NOT_CHECKED_IN",
  "failureMessage": "票码未核销",
  "operatorUsername": "admin",
  "operatorDisplayName": "管理员",
  "requestId": "req-undo-123",
  "createdAt": "2026-07-01T11:00:00Z"
}
```

错误响应保持不变：

- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`
- 游客 session：`403 ADMIN_FORBIDDEN`
- 非法失败码：`422 ADMIN_CHECK_IN_FAILURE_CODE_INVALID`
- `dateFrom > dateTo`：`422 ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID`

## 数据模型

`check_in_failure_audit_log` 继续作为业务失败尝试表：

- `action`：`CHECK_IN` 或 `UNDO_CHECK_IN`。
- `failure_code`：只允许受控业务失败码。
- `failure_message`：后端领域错误消息。
- `operator_admin_user_id`、`operator_username`、`operator_display_name`：来自管理员 session，前端不能提交。
- `request_id`：来自请求上下文，按既有 request id 长度截断规则处理。

迁移要求：

- 新建库 `database/schema.sql` 直接包含扩展后的约束。
- 已有库通过新的 `database/migrations/2026-07-01-extend-check-in-failure-audit-log-for-undo.sql` 幂等更新约束。
- 迁移不得删除既有失败审计数据。

## 安全边界

- 写入：只有管理员 session 和 CSRF 已通过的撤销请求才会记录失败尝试；匿名、游客或 CSRF 失败不会产生业务审计。
- 系统异常：不记录系统异常为失败尝试，避免把数据库错误、上游错误或敏感异常细节固化到业务审计表。
- DTO：检索响应不返回手机号、证件号、session token、CSRF token、密码 hash、内部 id、SQL 或订单内部 id。
- SQL：写入和筛选条件必须参数绑定，不能拼接原始票码、失败码或日期。
- 约束：数据库约束必须和服务层枚举一致，避免服务能写而数据库拒绝，或数据库能接受未建模错误码。

## 数据流

1. Router 继续先执行 CSRF 校验。
2. `AdminCheckInService` 校验管理员 session，并构造审计上下文。
3. Repository 执行既有撤销核销状态机。
4. Service 将 `None` 或可预期领域异常映射为撤销业务失败码，并调用 repository 写入失败审计，`action = UNDO_CHECK_IN`。
5. 原撤销接口仍返回既有错误响应；批量撤销接口仍返回逐票失败结果。
6. 管理员通过现有只读 GET 检索失败尝试。

## 验收

- 单张撤销票码不存在、未核销、不可撤销状态时写入失败审计。
- 批量撤销逐票业务失败时每张失败票写入失败审计，成功票仍只写成功审计。
- 匿名、游客和 CSRF 失败不会写入失败审计。
- 系统异常不写失败审计，也不把异常细节返回前端。
- 失败日志检索支持撤销失败码筛选。
- Postgres 写入和检索 SQL 使用参数绑定，不拼接票码、失败码或日期。
- OpenAPI 记录失败码枚举包含撤销失败码。
- schema 和迁移 SQL 都扩展 action 与 failure_code 约束。
