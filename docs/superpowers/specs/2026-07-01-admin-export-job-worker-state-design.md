# 后台异步导出 worker 状态机基础设计

## 问题

后台已经能创建 `PENDING` 导出任务，并且 `filters` 已按导出类型白名单校验。后续要生成 CSV/XLSX 文件，worker 需要一个稳定的任务状态机入口：原子领取任务、标记成功、标记失败，并保证不会两个 worker 同时处理同一任务。

## 范围

- 新增内部仓储和服务方法：
  - `claim_next_pending_job()`：领取最早的 `PENDING` 任务并标记为 `RUNNING`。
  - `mark_export_job_succeeded(job_id, file_name, storage_key)`：仅把 `RUNNING` 任务标记为 `SUCCEEDED`。
  - `mark_export_job_failed(job_id, error_code, error_message)`：仅把 `RUNNING` 任务标记为 `FAILED`。
- 成功状态可以写入文件名和内部存储 key，但现有管理员 DTO 仍不返回 `storage_key`。
- 失败状态写入错误码和错误信息，返回给管理员用于排障。
- 不实现真实 worker 循环、文件生成、对象存储、下载链接、重试、清理任务或前端页面。

## 状态机

```text
PENDING -> RUNNING -> SUCCEEDED
PENDING -> RUNNING -> FAILED
```

- `claim_next_pending_job()` 只能领取 `PENDING`，并按 `requested_at ASC, id ASC` 选择最早任务。
- SQL 使用 `FOR UPDATE SKIP LOCKED` 避免并发 worker 领取同一任务。
- 成功/失败更新只作用于 `RUNNING` 任务；不存在或状态不匹配时返回 `None`，由后续 worker 决定是否重试或记录内部日志。

## 安全边界

- 这些方法当前是内部 worker API，不新增管理员状态变更 HTTP 端点。
- 所有 SQL 参数必须使用参数绑定，不拼接 `job_id`、文件名、存储 key、错误码或错误信息。
- `file_name`、`storage_key`、`error_code`、`error_message` 必须限制长度，避免写入超出 schema 的值。
- `storage_key` 只进入数据库内部字段，不出现在 `AdminExportJobDTO`。

## 验收

- `backend/tests/test_admin_export_jobs_api.py` 覆盖领取最早任务、无任务返回 `None`、成功/失败更新只接受 `RUNNING`、长度校验和 SQL 参数绑定。
- `docs/backend-security-audit.md`、`docs/backend-milestone-status.md` 和 `docs/backend-acceptance-report.md` 更新本切片证据。
- `scripts/verify-backend.sh` 继续通过。
