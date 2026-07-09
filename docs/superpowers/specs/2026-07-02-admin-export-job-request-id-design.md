# 后台异步导出任务 requestId 关联

## 问题

异步导出跨创建请求、轮询、worker stdout 和下载请求。只有统一响应 request_id，任务本身缺少创建请求关联字段，排障时难以把前端操作和后端任务串起来。

## 范围

- 创建导出任务时保存当前请求 id 到 `admin_export_job.request_id`。
- `AdminExportJobDTO` 公开返回 `requestId`。
- 历史任务可为 null；保存值最多 64 字符，匹配数据库字段。
- requestId 仅用于排障关联。

## 边界

- requestId 不参与权限、CSRF、幂等、任务领取、文件生成、下载鉴权或重试条件。
- 不回填历史数据。
- 不接入外部 tracing/APM。

## 验收

- API 测试覆盖创建响应和仓储记录 requestId。
- Postgres 测试覆盖 request_id 参数绑定。
- schema 测试覆盖基线和旧库迁移。
