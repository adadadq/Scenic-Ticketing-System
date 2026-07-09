# 后台异步导出告警事件筛选增强设计

## 问题

告警事件已经支持管理员查询和确认，但列表只能按 `jobId` 与 `errorCode` 过滤。前端管理台后续需要直接查看未处理告警，也需要按时间范围缩小排查范围；如果只能全量拉取再在前端过滤，会增加联调成本，也容易把分页语义做错。

## 范围

- 为 `GET /api/admin/export-job-alert-events` 增加 `acknowledged`、`dateFrom`、`dateTo` 查询参数。
- `acknowledged=true` 只返回已确认事件，`acknowledged=false` 只返回未确认事件。
- `dateFrom/dateTo` 按事件 `created_at` 过滤，日期格式固定为 `YYYY-MM-DD`，`dateTo` 为包含当天。
- 保持只读 GET，不要求 CSRF。

## 非目标

- 不新增告警关闭、重开、删除、静默、去重或升级策略。
- 不发送 email、Slack、Webhook 或短信告警。
- 不新增前端页面。
- 不返回 `filters`、`storage_key`、本机路径、SQL、异常栈、session、CSRF token 或内部管理员 id。

## API 与错误

- `acknowledged` 只接受 `true` 或 `false`，忽略空值。
- `dateFrom/dateTo` 只接受 `YYYY-MM-DD`；当两者同时存在且 `dateFrom > dateTo` 时拒绝。
- 非法筛选返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。

## 数据与安全

- Repository 只拼接固定 WHERE 片段：`job_id`、`error_code`、`acknowledged_at`、`created_at`。
- 所有动态筛选值都走 SQL 参数绑定。
- 列表查询仍只选择告警事实字段和确认展示字段，不选择任务 `filters` 或内部 `storage_key`。

## 测试

- API 测试覆盖组合筛选、非法日期、日期倒挂和非法 `acknowledged`。
- Repository 测试覆盖新增 WHERE 条件、日期上界包含整天和参数绑定。
- OpenAPI、接口契约、安全清单、里程碑和验收报告同步更新。
