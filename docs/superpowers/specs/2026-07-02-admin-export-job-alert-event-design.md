# 后台异步导出最终失败告警事件记录设计

日期：2026-07-02

## 背景

异步导出已经有自动重试、RUNNING 超时回收和 `ADMIN_EXPORT_ALERT_PROVIDER=disabled` 配置边界。provider 边界能避免部署误以为 email、Slack 或 Webhook 已接入，但 worker 最终失败后仍缺少一个内部事实记录，不利于后续接入真实告警、后台检索或运维复盘。

本切片先补数据库内的本地告警事件记录，不发送外部通知，也不新增前端页面。

## 范围

- 新增 `admin_export_job_alert_event` 表，记录导出任务通过 worker 标记为最终失败时的内部告警事实。
- 事件字段只包含 `job_id`、`export_type`、`file_format`、`error_code`、`error_message`、`alert_source`、`created_at`。
- `AdminExportJobService.mark_export_job_failed` 只有在仓储返回的任务状态为最终 `FAILED` 时才写入事件。
- 未预期异常第一次自动重试回到 `PENDING` 时不写入事件。
- unsupported、业务/校验失败或自动重试耗尽后落为 `FAILED` 时写入 `WORKER_FINAL_FAILURE` 事件。
- 事件写入是尽力动作；写入失败不能掩盖原始任务失败状态。

## 非目标

- 不发送 email、Slack、Webhook、短信或其他真实告警。
- 不新增后台告警列表、详情、统计或前端页面。
- 不实现告警去重、静默窗口、升级策略或通知模板。
- 不接入外部队列、对象存储、监控平台或工单系统。

## 安全边界

- 告警事件不保存 `filters`、`storage_key`、文件本地路径、原始异常、堆栈、SQL、Cookie、session 或 CSRF token。
- 事件字段来自已归一化的任务失败记录，错误码和错误信息仍受既有长度限制。
- Postgres 插入必须使用 SQL 参数绑定，不拼接任务编号、导出类型、错误码或错误信息。
- 事件写入失败会被吞掉，避免“告警记录失败”反过来改变原始任务失败语义。

## 验收

- 自动重试第一次失败返回 `PENDING`，不产生告警事件。
- 自动重试耗尽后最终 `FAILED`，产生一条 `WORKER_FINAL_FAILURE` 事件。
- unsupported 任务最终 `FAILED`，产生一条 `WORKER_FINAL_FAILURE` 事件。
- 事件 repr 中不包含 `filters` 或 `storage_key`。
- schema 和迁移包含 `admin_export_job_alert_event` 表、外键、来源约束和查询索引。
- Postgres 告警事件插入由测试覆盖参数绑定。
