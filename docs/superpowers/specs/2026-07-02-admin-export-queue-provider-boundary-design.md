# 后台异步导出队列 provider 边界

## 问题

后台异步导出当前把 `admin_export_job` 数据库表作为任务队列，并依赖行锁领取 `PENDING` 任务。后续如果接 Redis、Celery、RQ 或消息队列，不能让部署人员只改环境变量就误以为外部队列已经可用。

## 范围

- 新增 `ADMIN_EXPORT_QUEUE_PROVIDER` 配置，默认值为 `database`。
- 配置值会 trim 并转小写。
- 当前只支持 `database`，任何未知 provider 都在配置校验阶段拒绝启动。
- 不改变现有任务创建、领取、重试、清理或下载接口。

## 边界

- 不接入 Redis、Celery、RQ、RabbitMQ、Kafka 或云消息队列。
- 不新增后台进程池、并发容量配置或队列监控。
- 不改变数据库行锁队列语义。

## 安全要点

- 未实现的队列 provider 不能静默回退到数据库队列。
- 当前数据库队列继续依赖 `FOR UPDATE SKIP LOCKED` 避免重复领取。
- 任务状态更新继续限制在 `RUNNING` 状态上。

## 验收

- 配置测试覆盖默认 `database`、大小写归一化和未知 provider 拒绝。
- 后端里程碑和安全清单明确当前外部队列未接入。
- 后端完整验证脚本通过。
