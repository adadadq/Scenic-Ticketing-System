# 后台异步导出 worker 进程守护模板

## 问题

`scripts/run-admin-export-worker.py` 已经能循环消费 `PENDING` 导出任务，但如果部署环境直接在终端里运行，进程崩溃或机器重启后不会自动恢复。后台导出链路需要一个最小的常驻进程守护模板，方便本地服务器或 Linux 部署环境把 worker 纳入系统服务。

## 范围

- 新增 `deploy/systemd/scenic-ticket-admin-export-worker.service` 作为 systemd 服务模板。
- 服务启动现有循环 worker，不新增外部队列、不改变 API、不改变任务状态机。
- 服务使用固定非 root 用户、环境文件、受控导出目录、自动重启和基础 systemd 加固项。

## 边界

- 不接 S3/OSS/COS 等生产对象存储。
- 不实现 Redis/Celery/RQ/消息队列。
- 不实现多 worker 并发规模配置；当前仍依赖数据库行锁避免重复领取。
- 不替代正式的部署文档、CI/CD 或机器初始化脚本。

## 运行约定

- 项目部署到 `/opt/scenic-ticket/current`。
- 虚拟环境位于 `/opt/scenic-ticket/current/.venv`。
- 后端环境变量文件位于 `/etc/scenic-ticket/backend.env`。
- 导出文件目录为 `/var/lib/scenic-ticket/admin-exports`，由部署流程预创建并授权给 `scenic-ticket` 用户，并通过 `ADMIN_EXPORT_STORAGE_DIR` 传给后端。
- 项目目录 `/opt/scenic-ticket/current` 应由部署流程保持只读发布形态，不作为 worker 写目录。

## 安全要点

- 使用 `User=scenic-ticket` 和 `Group=scenic-ticket`，避免 root 运行 worker。
- 使用 `NoNewPrivileges=true`、`PrivateTmp=true`、`ProtectSystem=strict` 和 `ProtectHome=true` 降低进程权限。
- 只通过 `ReadWritePaths=/var/lib/scenic-ticket/admin-exports` 暴露导出写目录。
- 退出信号使用 `SIGINT`，让脚本按既有中断路径输出固定 JSON，并避免异常细节进入 stderr。

## 验收

- 自动化测试必须检查 service 模板包含 worker 命令、环境文件、受控导出目录、自动重启、停止信号、非 root 用户和基础加固项。
- `scripts/verify-backend.sh` 仍然通过。
