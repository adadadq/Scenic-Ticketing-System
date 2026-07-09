# 后台异步导出告警事件类型和格式筛选设计

## 背景

后台异步导出告警事件已经支持列表、汇总、确认、关闭、重开和未关闭去重。前端管理台接下来需要按导出类型和文件格式查看告警，例如只看 `ORDER_DETAIL` 或只看 `XLSX` 失败，否则列表和汇总只能按错误码、确认状态、关闭状态和时间范围收窄。

## 设计

- `GET /api/admin/export-job-alert-events` 新增 `exportType` 和 `fileFormat` 查询参数。
- `GET /api/admin/export-job-alert-events/summary` 同步新增 `exportType` 和 `fileFormat` 查询参数。
- `exportType` 去空白并转大写后必须属于现有异步导出类型白名单。
- `fileFormat` 去空白并转大写后必须是 `CSV` 或 `XLSX`。
- 非法类型或格式统一返回 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`，保持告警筛选错误语义，不复用导出任务列表的错误码。
- 仓储层只在已有 `admin_export_job_alert_event.export_type` 和 `file_format` 列上追加参数化 `WHERE` 条件。

## 安全边界

- 接口仍只接受管理员 session。
- 两个接口都是只读 GET，不要求 CSRF header。
- 响应 DTO 不新增字段，仍不返回 `filters`、`storage_key`、本机路径、SQL、原始异常、session、CSRF token 或内部管理员 id。
- 本切片不新增表结构、不引入真实 email/Slack/Webhook 通知、不做删除、不做跨任务聚合，也不实现前端页面。

## 测试

- API 测试覆盖列表和汇总的 `exportType/fileFormat` 归一化。
- API 测试覆盖非法导出类型和非法文件格式返回 `ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。
- Postgres 仓储测试覆盖 SQL 参数绑定，不把导出类型或格式拼进 SQL 字符串。
- 文档事实源测试覆盖里程碑、API 契约、安全审计和验收报告。
