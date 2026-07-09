# 后台异步导出自动重试延迟领取设计

## 背景

后台异步导出已经支持 worker 未预期异常自动重试一次。上一版实现会把可重试任务立即从 `RUNNING` 改回 `PENDING`，循环 worker 可能马上再次领取同一条任务；如果故障是短暂文件系统、临时依赖或运行时抖动，这会形成紧密重试循环，也让日志和资源消耗变得难以观察。

## 范围

- 为 `admin_export_job` 增加内部 `next_attempt_at` 字段。
- 只有可自动重试的未预期异常会设置 `next_attempt_at = now + 60s` 并回到 `PENDING`。
- worker 领取任务时只选择 `next_attempt_at IS NULL` 或已经到期的 `PENDING` 任务。
- 成功、最终失败和管理员手动 retry 都会清空 `next_attempt_at`。
- `next_attempt_at` 不进入公开 DTO，前端仍只依赖既有任务状态和错误字段。

## 非目标

- 不实现指数退避。
- 不把延迟秒数做成运行时配置。
- 不接入外部队列、Celery/RQ/Redis 或消息队列。
- 不接入真实邮件、Slack、Webhook 告警。

## 安全边界

- 延迟领取只改变内部任务调度，不扩大管理员 API 入参或公开响应字段。
- 领取 SQL 继续使用行锁、状态条件和参数绑定，避免并发 worker 重复领取。
- 自动重试仍只用于 worker 未预期异常；业务/校验失败、unsupported 任务和手动中断不自动重试。
- 固定 60 秒延迟用于避免 tight loop，完整指数退避、可配置策略和告警审计后续再拆。

## 验收

- worker 未预期异常第一次失败后回到 `PENDING`，设置内部 `next_attempt_at`，立即再次处理应拿不到任务。
- 模拟延迟到期后，同一任务可以再次被领取；耗尽一次自动重试后落为 `FAILED`。
- 管理员手动 retry、成功和最终失败都会清空内部 `next_attempt_at`。
- schema 基线、初始建表迁移和旧库补列迁移都包含 `next_attempt_at` 和领取索引。
- API 契约、安全审计、里程碑状态和验收报告同步记录该内部调度边界。
