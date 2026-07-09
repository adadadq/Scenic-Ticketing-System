# 后台异步导出失败告警 provider 边界设计

## 背景

后台异步导出已经支持任务创建、worker 处理、文件下载、失败手动重试、未预期异常自动重试和本地文件清理。当前仍没有真实失败告警能力，如果部署环境配置了邮件、Slack 或 Webhook 这类 provider 并被静默接受，会误以为导出任务最终失败时已经能主动通知。

## 范围

- 新增 `ADMIN_EXPORT_ALERT_PROVIDER` 配置项。
- 当前唯一支持值为 `disabled`，表示不发送失败告警。
- 配置值需要 trim、大小写归一化，空值回退到 `disabled`。
- 未实现的 `email`、`slack`、`webhook` 或其他 provider 必须在配置校验阶段拒绝启动。
- `.env.example`、README、API 契约、安全清单、安全审查、里程碑和决策日志同步说明边界。

## 非目标

- 不实现邮件、Slack、Webhook 或短信告警发送。
- 不改变 worker 失败状态机、自动重试次数或管理员 API 响应。
- 不在 DTO 暴露内部告警状态。
- 不新增告警去重、告警审计、告警静默窗口或通知模板。

## 安全边界

- 告警 provider 未接入前只能显式关闭，不能静默回退或假装成功。
- 真实告警接入前必须重新设计失败任务数据脱敏，避免把完整筛选条件、文件路径、SQL、异常文本或本机路径发到外部系统。
- 真实告警接入前需要定义去重和重试策略，避免同一失败任务在自动重试、手动重试或 worker 重启时重复轰炸。

## 验收

- `backend/tests/test_config_db.py` 覆盖 `.env.example` 默认值、环境变量读取、大小写归一化、未知 provider 拒绝和生产显式配置。
- `docs/backend-milestone-status.md` 记录本切片为已完成。
- `docs/backend-security-audit.md` 映射配置测试证据。
- `scripts/verify-backend.sh` 通过。
