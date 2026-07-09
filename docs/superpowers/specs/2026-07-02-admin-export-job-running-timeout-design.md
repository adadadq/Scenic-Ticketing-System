# 后台异步导出 RUNNING 超时回收设计

## 背景

后台异步导出 worker 已经支持任务领取、文件生成、自动重试和延迟重试。但如果 worker 进程在任务处于 `RUNNING` 时崩溃，任务不会进入异常处理分支，也就无法自动标记失败或重试，前端任务中心会长期看到运行中状态。

## 范围

- worker 每轮领取 pending 任务前，先回收启动超过 30 分钟的 `RUNNING` 任务。
- 超时任务仍有自动重试额度时，回到 `PENDING`，清空运行时间、文件元数据、错误信息和 `next_attempt_at`，并递增 `retry_count`。
- 超时任务已耗尽重试额度时，落为 `FAILED`，错误码为 `ADMIN_EXPORT_JOB_WORKER_TIMEOUT`。
- 为 `admin_export_job(status, started_at)` 增加索引，支撑按状态和开始时间扫描超时任务。
- 该能力只改变内部 worker 调度，不新增公开 API 字段。

## 非目标

- 不实现 worker 心跳、分布式租约或外部队列可见性超时。
- 不实现真实失败告警。
- 不清理没有落库元数据的孤儿文件。
- 不改变管理员任务列表、详情或下载接口 DTO。

## 安全边界

- 回收 SQL 只处理 `status = 'RUNNING'` 且 `started_at` 已超过固定超时阈值的任务。
- 状态更新继续使用 SQL 参数绑定，错误码、错误信息和超时秒数都不拼接进 SQL。
- `storage_key`、`retry_count`、`max_retries` 和超时策略仍不进入公开 DTO。

## 验收

- worker 会在领取 pending 任务前调用超时回收。
- 未耗尽重试额度的超时任务会回到 `PENDING` 并优先被重新领取。
- 耗尽重试额度的超时任务会落为 `FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT`。
- PostgreSQL 仓储测试覆盖超时回收 SQL 的状态条件、时间条件、重试分支和参数绑定。
- schema 基线、初始建表迁移和旧库迁移都包含 `idx_admin_export_job_status_started_at`。
