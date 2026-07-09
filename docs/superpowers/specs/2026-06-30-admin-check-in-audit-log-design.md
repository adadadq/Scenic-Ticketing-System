# 后台核销审计日志设计

## 背景

后台已经支持单张票码核销，但核销成功后只改变票项、订单和时段核销量，没有独立操作记录。现场运营排查“谁在什么时候核销了哪张票”时，不能只依赖请求日志或当前票项状态。本切片先补核销成功审计日志，为后续撤销核销、批量核销和核销异常排查提供事实基础。

## 范围

- 新增 `check_in_audit_log` 表。
- `POST /api/admin/check-ins` 成功时，在同一数据库事务内写入一条 `CHECK_IN` 审计日志。
- 新增 `GET /api/admin/check-ins/{ticket_code}/logs`，按票码读取核销审计日志。
- 审计日志字段包含 `orderNo`、`itemNo`、`ticketCode`、`action`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- 操作人只来自当前管理员 session，前端不能提交或覆盖。

## 不做

- 撤销核销。
- 批量核销。
- 全局核销日志检索、分页或 CSV 导出。
- 失败核销尝试审计。
- 更细角色权限矩阵。

## API 契约

`POST /api/admin/check-ins` 保持原有请求和响应；成功事务内新增审计写入。

`GET /api/admin/check-ins/{ticket_code}/logs`：

- 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 票码不存在返回 `404 TICKET_NOT_FOUND`。
- 票码存在但没有核销日志时返回空数组。
- 成功返回 `AdminCheckInAuditLogDTO[]`，按 `createdAt` 倒序排列。

## 安全边界

- 状态变更核销接口继续要求 session-bound CSRF。
- 日志查询是只读 GET，不要求 CSRF。
- 审计响应不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。
- SQL 查询使用参数绑定，不拼接票码。
- 请求日志仍不记录查询参数或请求体；业务审计只记录核销必要字段。

## 数据流

1. Router 对 `POST /api/admin/check-ins` 校验 CSRF。
2. Service 校验管理员 session，生成 `AdminCheckInAuditInput`。
3. Repository 锁定票项和订单，校验状态，更新票项、时段核销量和订单状态。
4. Repository 在同一事务内插入 `check_in_audit_log`。
5. 查询日志时，Repository 先确认票码对应票项存在，再读取日志并按时间倒序返回。

## 验收

- 管理员核销成功后可无 CSRF header 读取该票码核销日志。
- 审计日志包含操作人展示字段和 request id。
- 匿名和游客 session 不能读取日志。
- 缺失票码返回 `TICKET_NOT_FOUND`。
- 核销失败、重复核销或不可核销状态不会写审计日志。
- Postgres 核销成功路径在状态更新后同事务写入 `check_in_audit_log`。
- Postgres 日志查询使用参数绑定并按 `created_at DESC, id DESC` 排序。
- OpenAPI 声明新日志 DTO，安全清单和里程碑文档同步。
