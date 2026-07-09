# 后台异步导出告警事件关闭和重开设计

## 问题

告警事件已经支持分页查询、汇总和确认。确认表达“这条告警已经被某位管理员处理过”，但前端管理台还需要一个更明确的生命周期动作：把不再需要展示在活跃告警里的事件关闭，并在误关闭或需要继续排查时重开。

## 范围

- 新增管理员 `POST /api/admin/export-job-alert-events/{event_id}/close`。
- 新增管理员 `POST /api/admin/export-job-alert-events/{event_id}/reopen`。
- close 请求体只允许可选 `note`，最大 200 字符，空白归一化为 `null`。
- close 第一次关闭获胜；重复 close 返回既有关闭记录，不覆盖原关闭人和备注。
- reopen 清空关闭字段；未关闭事件重复 reopen 返回当前事件。
- `AdminExportJobAlertEventDTO` 增加 `closedAt`、`closedByUsername`、`closedByDisplayName`、`closeNote`。

## 非目标

- 不发送 email、Slack、Webhook、短信或站内信。
- 不新增关闭筛选、关闭汇总、删除、静默、去重或升级策略。
- 不改变 `acknowledged*` 字段语义；确认和关闭可以独立存在。
- 不新增前端页面。

## 安全边界

- close/reopen 都是状态变更 `POST`，必须要求管理员 session 和 session-bound CSRF。
- DTO 不返回 `closed_by_admin_user_id`。
- 响应不得包含 `filters`、`storage_key`、本机路径、SQL、堆栈、原始异常、session 或 CSRF token。
- SQL 使用参数绑定；备注不能拼进 SQL 字符串。

## 数据设计

在 `admin_export_job_alert_event` 增加：

- `closed_at TIMESTAMP`
- `closed_by_admin_user_id BIGINT REFERENCES admin_user(id)`
- `closed_by_username VARCHAR(64)`
- `closed_by_display_name VARCHAR(100)`
- `close_note VARCHAR(200)`

新增 `idx_admin_export_job_alert_event_closed_created`，支持后续按关闭状态和时间查询。

## 验收

- 管理员带 CSRF 可以关闭事件，响应返回关闭展示字段。
- 重复关闭不覆盖第一次关闭人或备注。
- 管理员带 CSRF 可以重开事件，响应清空关闭字段。
- 匿名、游客和缺 CSRF 请求被拒绝。
- 不存在事件返回 `404 ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND`。
- 非法 close note 返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_CLOSE_INVALID`。
- schema、迁移、OpenAPI、文档和 SQL 参数绑定测试覆盖。
