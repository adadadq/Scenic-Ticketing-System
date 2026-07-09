# 后台异步导出告警事件只读查询设计

日期：2026-07-02

## 背景

异步导出最终失败已经会写入内部 `admin_export_job_alert_event`，但只能落库，管理员和后续前端页面还没有只读查询入口。真实 email、Slack 或 Webhook 告警接入前，先提供最小可观测 API，方便运维复盘和前端后续接任务异常页。

本切片只读取内部告警事实，不发送外部通知。

## 范围

- 新增 `GET /api/admin/export-job-alert-events`。
- 只接受管理员 session；只读 GET 不要求 CSRF header。
- 支持 `jobId`、`errorCode`、`page`、`pageSize` 查询参数。
- `errorCode` 查询值 trim 后转大写；空字符串视为未筛选；超长筛选返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。
- 响应使用统一成功壳，`data` 为分页列表。
- 事件 DTO 只包含 `jobId`、`exportType`、`fileFormat`、`errorCode`、`errorMessage`、`alertSource`、`createdAt`。

## 非目标

- 不新增前端页面、统计图表或导出功能。
- 不发送 email、Slack、Webhook、短信或其他真实告警。
- 不实现告警确认、关闭、分派、去重、静默窗口或升级策略。
- 不暴露任务 `filters`、`storage_key`、本机路径、SQL、堆栈或原始异常。

## 安全边界

- 查询 API 只返回已脱敏的内部告警事件字段，不回连导出任务完整 filters。
- 仓储 SQL 只拼接固定白名单 `WHERE` 片段，`jobId`、`errorCode`、`LIMIT` 和 `OFFSET` 均使用参数绑定。
- 列表按 `created_at DESC, id DESC` 排序，避免同一时间写入多条事件时顺序不稳定。
- 未登录返回后台管理员未登录错误，游客 session 返回管理员权限错误。

## 验收

- 管理员可无 CSRF 查询告警事件列表。
- 匿名和游客不能查询。
- `jobId` 与 `errorCode` 筛选能归一化并传入仓储。
- 响应不包含 `filters`、`storageKey` 或 `storage_key`。
- OpenAPI 公开 `AdminExportJobAlertEventListDTO`。
- Postgres 查询测试覆盖参数绑定、分页、排序和不选择敏感字段。
