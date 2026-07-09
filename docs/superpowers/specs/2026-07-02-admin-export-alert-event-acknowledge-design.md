# 后台异步导出告警事件确认设计

## 问题

异步导出最终失败已经会写入 `admin_export_job_alert_event`，管理员也能通过只读 API 查询这些本地告警事实。但当前事件没有“已处理”状态，运营人员无法区分哪些失败已经人工排查过，也无法留下最小处理记录。

## 范围

- 为 `admin_export_job_alert_event` 增加确认字段：确认时间、确认管理员 id、用户名、展示名和可选备注。
- 告警事件列表 DTO 增加 `eventId` 与确认字段，为后续前端列表操作提供稳定目标。
- 新增 `POST /api/admin/export-job-alert-events/{event_id}/acknowledge`，仅管理员可调用，必须携带 CSRF header。
- 确认操作采用“第一次确认获胜”：已确认事件再次确认时返回既有记录，不覆盖原处理人和备注。

## 非目标

- 不发送 email、Slack、Webhook 或短信告警。
- 不实现告警关闭、重开、删除、静默、去重、升级策略或通知模板。
- 不把 `filters`、`storage_key`、本机路径、SQL、异常栈、Cookie、session 或 CSRF token 暴露到告警事件 DTO。
- 不新增前端页面，本切片只提供后端契约。

## API 与 DTO

- `GET /api/admin/export-job-alert-events` 保持只读 GET，不要求 CSRF；响应项新增 `eventId`、`acknowledgedAt`、`acknowledgedByUsername`、`acknowledgedByDisplayName`、`acknowledgeNote`。
- `POST /api/admin/export-job-alert-events/{event_id}/acknowledge`：
  - 路径参数 `event_id` 必须为正整数。
  - 请求体只允许可选 `note`，最大 200 字符，空白归一化为 `null`。
  - 成功返回同一个 `AdminExportJobAlertEventDTO`。
  - 未登录管理员返回 `401 ADMIN_AUTH_REQUIRED`，游客返回 `403 ADMIN_FORBIDDEN`。
  - 找不到事件返回 `404 ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND`。
  - 非法备注返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_ACK_INVALID`。

## 数据与安全

- 新增迁移只追加 nullable 字段，兼容已有事件。
- Repository 更新确认时使用参数绑定，不拼接 `note`、管理员身份或 `event_id`。
- SQL 更新使用 `CASE WHEN acknowledged_at IS NULL THEN ... ELSE ... END`，避免并发重复确认覆盖第一次确认。
- DTO 只返回确认展示字段，不返回内部管理员 session、请求头、完整 filters 或文件存储信息。

## 测试

- API 测试覆盖管理员带 CSRF 确认、重复确认不覆盖、匿名/游客拒绝、缺少 CSRF 拒绝和事件不存在。
- Repository 测试覆盖确认 SQL 参数绑定、查询字段不包含敏感列。
- Schema 测试覆盖新增列和索引迁移。
- OpenAPI 测试覆盖 POST 响应 DTO 和 CSRF header。
- 文档测试更新里程碑、安全清单和接口契约。
