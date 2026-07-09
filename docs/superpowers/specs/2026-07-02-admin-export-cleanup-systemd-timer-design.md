# 后台异步导出清理 systemd 定时器

## 问题

后台异步导出已经支持本地文件清理脚本，但部署环境仍需要一个可复用的定时调度模板，避免运维人员忘记定期执行清理导致本地导出目录持续增长。

## 范围

- 新增 `scenic-ticket-admin-export-cleanup.service`，以 oneshot 方式执行 `scripts/cleanup-admin-export-files.py --older-than-days 7 --limit 100`。
- 新增 `scenic-ticket-admin-export-cleanup.timer`，每天触发一次清理，并设置随机延迟与错过补跑。
- 复用现有部署约定：非 root 用户、`/etc/scenic-ticket/backend.env` 环境文件、`/var/lib/scenic-ticket/admin-exports` 受控写目录。
- 不改变清理脚本、数据库清理逻辑、导出下载 API 或 worker 状态机。

## 边界

- 不接入生产对象存储生命周期策略。
- 不实现跨节点分布式清理锁。
- 不新增后台 API 或前端开关。
- 不要求 macOS 或本地开发环境使用 systemd。

## 安全要点

- service 使用非 root 用户运行。
- service 只允许写入导出目录，系统路径只读。
- 日志进入 journal，脚本仍只输出固定 JSON，错误不泄露路径、SQL 或配置细节。
- timer 使用 `RandomizedDelaySec` 避免多实例同时触发。

## 验收

- 测试覆盖 service 的执行命令、环境文件、受控目录和 systemd 加固项。
- 测试覆盖 timer 的每日触发、随机延迟、错过补跑和绑定 service。
- README、API 契约、里程碑、安全审计和决策日志都记录该部署模板。
