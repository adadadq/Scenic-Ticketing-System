# 后台异步导出告警事件去重静默设计

## 背景

异步导出已经能在 worker 最终失败时写入内部告警事件，并支持查询、汇总、确认、关闭和重开。下一步需要减少同一任务同一错误在未处理期间反复写入多条事件造成的噪音。

## 范围

- 对同一个 `job_id + error_code + alert_source` 的未关闭告警做折叠。
- 重复出现时不新增事件行，只更新 `occurrence_count`、`last_seen_at` 和最新 `error_message`。
- 使用 `WHERE closed_at IS NULL` 的 partial unique index 保证同类未关闭告警在数据库层只有一条。
- `AdminExportJobAlertEventDTO` 返回 `occurrenceCount` 和 `lastSeenAt`，便于前端显示重复次数。
- 已关闭事件不参与折叠；同一任务关闭后再次最终失败，可创建新的未关闭事件。

## 非目标

- 不做跨任务、跨错误码或跨来源的合并。
- 不新增真实 email、Slack、Webhook 通知。
- 不新增删除、批量关闭或静默规则配置。

## 安全与数据边界

- 折叠只改变内部告警事件表，不改变导出任务状态机。
- SQL 继续使用参数绑定，不把 `filters`、`storage_key`、本机路径、SQL 或异常栈写入告警事件。
- 写入使用 `INSERT ... ON CONFLICT ... DO UPDATE`，避免并发写入产生多条未关闭重复事件。
- 重复计数最小值为 1，旧数据迁移默认按一次出现处理。

## 测试

- 仓储测试覆盖重复未关闭事件更新计数而不是直接插入。
- API 测试覆盖列表 DTO 返回 `occurrenceCount` 和 `lastSeenAt`。
- schema 测试覆盖新增列、约束和旧库迁移。
