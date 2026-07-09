# 后台核销失败尝试审计设计

日期：2026-07-01

## 问题定义

后台已经记录成功核销和成功撤销核销的审计日志，但现场扫码失败同样有安全价值：连续扫不存在票码、重复扫已核销票码、或尝试核销不可核销状态的票，可能代表误操作、票码泄露、撞库式猜码或流程培训问题。本切片补齐核销业务失败尝试的审计和检索能力。

## 边界

本切片实现：

- 新增 `check_in_failure_audit_log` 表，只记录核销业务失败尝试。
- 单张核销 `POST /api/admin/check-ins` 在管理员权限和 CSRF 校验通过后，如果失败原因为 `TICKET_NOT_FOUND`、`TICKET_ALREADY_USED` 或 `TICKET_NOT_CHECKABLE`，写入失败审计。
- 批量核销 `POST /api/admin/check-ins/batch` 对每个逐票业务失败写入失败审计。
- 新增 `GET /api/admin/check-in-failure-logs` 管理员只读检索接口。
- 检索支持 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo`、`page`、`pageSize`。

本切片不实现：

- 撤销核销失败审计。
- 系统异常、数据库异常或上游不可用的失败审计。
- CSV/XLSX 导出、异步导出或失败趋势报表。
- 失败尝试自动风控、封禁、告警或短信通知。
- 把失败记录混入既有 `check_in_audit_log` 成功审计表。

## API 契约

```text
GET /api/admin/check-in-failure-logs?ticketCode=TK&failureCode=TICKET_NOT_FOUND&page=1&pageSize=20
```

成功响应：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "ticketCode": "TK-MISSING",
        "action": "CHECK_IN",
        "failureCode": "TICKET_NOT_FOUND",
        "failureMessage": "票码不存在",
        "operatorUsername": "admin",
        "operatorDisplayName": "管理员",
        "requestId": "req-123",
        "createdAt": "2026-07-01T10:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "pageSize": 20
  },
  "request_id": "..."
}
```

错误响应：

- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`
- 游客 session：`403 ADMIN_FORBIDDEN`
- 非法失败码：`422 ADMIN_CHECK_IN_FAILURE_CODE_INVALID`
- `dateFrom > dateTo`：`422 ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID`

## 数据模型

`check_in_failure_audit_log` 字段：

- `ticket_code`：管理员尝试核销的票码，保留原始业务值，最大 64 字符。
- `action`：本切片固定为 `CHECK_IN`。
- `failure_code`：只允许 `TICKET_NOT_FOUND`、`TICKET_ALREADY_USED`、`TICKET_NOT_CHECKABLE`。
- `failure_message`：后端领域错误消息。
- `operator_admin_user_id`、`operator_username`、`operator_display_name`：来自管理员 session，前端不能提交。
- `request_id`：来自请求上下文，按既有 request id 长度截断规则处理。
- `created_at`：服务端写入时间。

不把失败尝试写入 `check_in_audit_log`，因为既有成功审计表包含非空 `order_id`、`order_item_id` 和外键；票码不存在时没有可信订单或票项可以关联。

## 安全边界

- 写入：只有管理员 session 和 CSRF 已通过的核销请求才会记录失败尝试；匿名、游客或 CSRF 失败不会产生业务审计。
- 系统异常：不记录系统异常为失败尝试，避免把数据库错误、上游错误或敏感异常细节固化到业务审计表。
- DTO：检索响应不返回手机号、证件号、session token、CSRF token、密码 hash、内部 id、SQL 或订单内部 id。
- SQL：筛选条件必须参数绑定，不能拼接原始查询字符串。
- 枚举：`failureCode` 只允许业务失败码，避免前端把任意错误码写入或筛选为业务事实。

## 数据流

1. Router 继续先执行 CSRF 校验。
2. `AdminCheckInService` 校验管理员 session，并构造审计上下文。
3. Repository 执行既有核销状态机。
4. Service 将 `None` 或可预期领域异常映射为业务失败码，并调用 repository 写入失败审计。
5. 原核销接口仍返回既有错误响应；批量接口仍返回逐票失败结果。
6. 管理员通过只读 GET 检索失败尝试。

## 验收

- 单张核销票码不存在、已核销、不可核销状态时写入失败审计。
- 批量核销逐票业务失败时每张失败票写入失败审计，成功票仍只写成功审计。
- 匿名、游客和 CSRF 失败不会写入失败审计。
- 系统异常不写失败审计，也不把异常细节返回前端。
- 失败日志检索只允许管理员 session，GET 不要求 CSRF。
- 失败日志检索支持失败码和日期筛选，非法失败码和非法日期范围返回专门错误码。
- Postgres 写入和检索 SQL 使用参数绑定，不拼接票码、失败码或日期。
- OpenAPI 记录失败日志检索端点返回 `ApiSuccessDTO[AdminCheckInFailureAuditLogListDTO]`。
