# 后台异步导出任务文件格式筛选设计

## 背景

后台异步导出任务列表已经支持按 `exportType` 和 `status` 查询，但前端任务中心还需要按文件格式筛选 CSV 或 XLSX 任务。告警事件列表和汇总已经支持 `fileFormat`，任务列表也应保持同一筛选口径。

## 设计

- `GET /api/admin/export-jobs` 新增 `fileFormat` 查询参数。
- `fileFormat` 去空白并转大写后只允许 `CSV` 或 `XLSX`。
- 非法文件格式返回 `422 ADMIN_EXPORT_JOB_FILE_FORMAT_INVALID`。
- 仓储层在已有 `admin_export_job.file_format` 列上追加参数化 `WHERE file_format = %s`。
- 返回 DTO 不变，继续复用现有任务列表响应。

## 安全边界

- 接口仍只接受管理员 session。
- 这是只读 GET，不要求 CSRF header。
- 响应继续不返回内部 `storage_key`、本机路径、SQL、session、CSRF token 或内部管理员 id。
- 本切片不改任务创建、worker 状态机、下载端点、文件生成、告警事件或前端页面。

## 测试

- API 测试覆盖 `fileFormat` 归一化和传入仓储 filter。
- API 测试覆盖非法文件格式返回 `ADMIN_EXPORT_JOB_FILE_FORMAT_INVALID`。
- OpenAPI 测试覆盖 `fileFormat` 查询参数。
- Postgres 仓储测试覆盖 `file_format = %s` 参数绑定。
- 文档事实源测试覆盖里程碑、API 契约、安全审计和验收报告。
