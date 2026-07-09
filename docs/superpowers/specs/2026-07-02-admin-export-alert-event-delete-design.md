# 后台异步导出告警事件删除设计

日期：2026-07-02

## 问题

后台异步导出告警事件已经支持查询、汇总、确认、关闭、重开和筛选，但关闭后的历史事件仍只能保留在列表中。管理员需要一个受控删除入口清理已关闭事件；同时不能允许直接删除未关闭告警，否则活跃故障会被抹掉。

## 范围

- 新增 `DELETE /api/admin/export-job-alert-events/{event_id}`。
- 只允许管理员 session 调用，并要求 session-bound CSRF header。
- 只删除 `closed_at IS NOT NULL` 的告警事件。
- 未关闭事件返回 `409 ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED`。
- 不存在事件返回 `404 ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND`。

## 非目标

- 不做批量删除。
- 不删除导出任务或导出文件。
- 不新增真实 email、Slack、Webhook 告警。
- 不做前端页面；前端对话可后续接入该 API。

## 数据与安全边界

删除接口返回 `AdminExportJobAlertEventDeleteDTO`，只包含 `eventId` 和 `deleted`。响应不得包含 `filters`、`storage_key`、本机路径、SQL、堆栈、原始异常、session、CSRF token 或内部管理员 id。

Postgres repository 使用参数化 `DELETE`，并通过 `closed_at IS NOT NULL` 在 SQL 层限制只能删除已关闭事件。服务层把 repository 结果映射成成功、404 或 409。

## 验收

- `backend/tests/test_admin_export_jobs_api.py` 覆盖已关闭事件删除、未关闭事件拒绝、事件不存在、管理员权限、CSRF 和 SQL 参数绑定。
- `backend/tests/test_openapi_contract.py` 覆盖 DELETE 响应 DTO 和 CSRF header。
- `backend/tests/test_security_basics.py` 覆盖本地前端 CORS 预检允许 DELETE。
- `scripts/verify-backend.sh` 作为后端完整门禁。
