# 后台异步导出 RUNNING 超时最终失败告警事件记录设计

日期：2026-07-02

## 背景

异步导出已经有 `admin_export_job_alert_event` 记录 worker 最终失败事实，也已经有 `recover_stale_running_jobs` 在下一轮 worker 领取前回收超过 30 分钟的 `RUNNING` 任务。上一切片只覆盖 `mark_export_job_failed` 入口，RUNNING 超时批量回收若直接把耗尽重试额度的任务落为 `FAILED`，仍缺少同样的内部告警事实。

本切片把 RUNNING 超时回收入口接入同一条内部告警事件链路，不发送真实通知，也不新增前端页面。

## 范围

- `recover_stale_running_jobs` 仓储返回回收数量和本次最终 `FAILED` 的任务记录。
- 服务层仍对外返回回收数量，保持 worker 调用方契约不变。
- 只有 RUNNING 超时且已耗尽重试额度、最终落为 `FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT` 的任务写入 `WORKER_FINAL_FAILURE` 事件。
- 未耗尽重试额度、回到 `PENDING` 等待后续处理的 RUNNING 超时任务不写入事件。
- 事件写入继续复用既有尽力策略；写入失败不能改变任务回收结果。

## 非目标

- 不发送 email、Slack、Webhook、短信或其他真实告警。
- 不新增后台告警列表、详情、统计或前端页面。
- 不实现告警去重、静默窗口、升级策略或通知模板。
- 不改变 30 分钟超时阈值、自动重试次数、worker 心跳、分布式租约或外部队列可见性超时。

## 安全边界

- 告警事件只复制任务记录中的错误码和错误信息，以及任务编号、导出类型、文件格式和事件来源。
- 事件不保存 `filters`、`storage_key`、本机路径、SQL、堆栈、Cookie、session、CSRF token 或原始异常。
- RUNNING 超时回收 SQL 继续使用状态条件、超时条件和参数绑定，不拼接错误码、错误信息或超时秒数。
- 可重试回 `PENDING` 的任务不写事件，避免把临时故障误标为最终失败告警。

## 验收

- RUNNING 超时未耗尽重试额度时回到 `PENDING`，不产生告警事件。
- RUNNING 超时耗尽重试额度时落为 `FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT`，产生一条 `WORKER_FINAL_FAILURE` 事件。
- 事件 repr 中不包含 `filters` 或 `storage_key`。
- Postgres 回收 SQL 返回最终失败任务所需字段，并由测试覆盖参数绑定。
