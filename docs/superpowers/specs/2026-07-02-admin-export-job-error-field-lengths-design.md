# 后台异步导出失败字段长度契约对齐设计

日期：2026-07-02

## 背景

异步导出 worker 失败入口在服务层已经限制 `error_code` 最长 80、`error_message` 最长 500。旧版 `admin_export_job` 表仍是 `error_code VARCHAR(64)` 和 `error_message VARCHAR(200)`，会造成服务层校验通过但 Postgres 写入失败的风险。最终失败告警事件表也应与失败记录的错误码长度保持一致。

## 范围

- 将 `database/schema.sql` 中 `admin_export_job.error_code` 对齐为 `VARCHAR(80)`。
- 将 `database/schema.sql` 中 `admin_export_job.error_message` 对齐为 `VARCHAR(500)`。
- 将 `admin_export_job_alert_event.error_code` 对齐为 `VARCHAR(80)`。
- 新增旧库迁移 `2026-07-02-align-admin-export-job-error-field-lengths.sql`，只做 VARCHAR 扩容。
- 保持服务层校验、公开 DTO、错误码语义和 worker 状态机不变。

## 非目标

- 不放宽 `file_name`、`storage_key`、`filters` 或其他字段。
- 不改变现有失败错误码和错误信息文本。
- 不新增前端 API、告警查询 API 或真实外部通知。
- 不重写既有迁移；旧库通过新增迁移完成列宽升级。

## 安全边界

- 本切片只扩容受控错误码和错误信息字段，不引入原始异常、堆栈、本机路径或 SQL。
- `error_message` 仍由服务层归一化和长度限制，不能作为任意日志载体。
- 告警事件继续只复制归一化后的失败字段，不保存 `filters` 或 `storage_key`。

## 验收

- schema 契约测试证明 `admin_export_job` 和 `admin_export_job_alert_event` 最终列宽与服务层一致。
- 迁移契约测试证明旧库会执行 `ALTER COLUMN ... TYPE VARCHAR(...)`。
- 现有 worker 输入长度测试继续覆盖 81 字符错误码和 501 字符错误信息会被服务层拒绝。
