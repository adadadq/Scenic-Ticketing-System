# 后台异步导出告警事件关闭筛选和汇总增强设计

## 背景

告警事件已经支持记录、列表、确认、关闭和重开。前端管理台接下来需要直接拉取“未关闭”告警作为待处理队列，也需要在汇总卡片里区分关闭和未关闭规模。

## 范围

- `GET /api/admin/export-job-alert-events` 新增 `closed=true/false` 查询参数。
- `GET /api/admin/export-job-alert-events/summary` 新增 `closed=true/false` 查询参数，并在响应中返回 `closed` 和 `open` 计数。
- `byErrorCode` 每个错误码分组也返回 `closed` 和 `open` 计数。
- `closed=false` 表示 `closed_at IS NULL`，`closed=true` 表示 `closed_at IS NOT NULL`。

## 非目标

- 不新增真实外部通知、静默窗口、去重、删除或批量关闭。
- 不改前端页面，由前端对话独立设计。
- 不改变关闭/重开写接口的幂等语义。

## 安全与数据边界

- 两个 GET 接口仍只接受管理员 session；只读 GET 不要求 CSRF。
- `closed` 只接受 `true/false`，非法值沿用 `422 ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。
- SQL 只拼接固定条件片段，所有动态值继续使用参数绑定。
- DTO 不返回内部管理员 id、`filters`、`storage_key`、本机路径、SQL 或异常栈。

## 测试

- API 测试覆盖列表 `closed=false`、汇总 `closed=false`、非法 `closed`。
- 仓储测试覆盖 `closed_at IS NULL/IS NOT NULL` 条件和参数化查询。
- 文档验收测试继续追踪里程碑、验收报告、安全审计和 API 契约。
