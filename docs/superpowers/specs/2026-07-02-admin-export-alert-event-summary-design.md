# 后台异步导出告警事件汇总设计

## 问题

告警事件已经能分页查询、筛选和确认。前端管理台后续还需要展示未处理告警数量、总体处理进度和主要失败原因。如果前端通过分页列表自行聚合，容易受到分页大小影响，也会增加接口调用次数。

## 范围

- 新增 `GET /api/admin/export-job-alert-events/summary`。
- 支持 `dateFrom`、`dateTo` 查询参数，按事件 `created_at` 过滤，`dateTo` 包含当天。
- 返回总事件数、已确认数、未确认数，以及按 `errorCode` 聚合的数量。
- 保持只读 GET，不要求 CSRF。

## 非目标

- 不新增告警关闭、重开、删除、静默、去重、升级策略或通知模板。
- 不发送 email、Slack、Webhook 或短信告警。
- 不新增前端页面。
- 不返回 `filters`、`storage_key`、本机路径、SQL、异常栈、session、CSRF token 或内部管理员 id。

## API 与 DTO

- `dateFrom/dateTo` 必须是 `YYYY-MM-DD`，两者同时存在时 `dateFrom <= dateTo`。
- 非法筛选返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。
- 响应 DTO：
  - `total`
  - `acknowledged`
  - `unacknowledged`
  - `byErrorCode[]`：`errorCode`、`total`、`acknowledged`、`unacknowledged`

## 数据与安全

- Repository 聚合只读取 `error_code`、`created_at` 和 `acknowledged_at`。
- 日期条件使用固定 WHERE 片段和 SQL 参数绑定。
- 汇总结果不回连导出任务表，不读取任务 `filters` 或内部 `storage_key`。

## 测试

- API 测试覆盖管理员可查询汇总、日期筛选归一化、非法日期拒绝、匿名/游客拒绝。
- Repository 测试覆盖聚合 SQL 参数绑定、`dateTo` 包含整天和敏感列未选择。
- OpenAPI、接口契约、安全清单、里程碑和验收报告同步更新。
