# 数据库说明

本目录是当前 FastAPI 主线的数据库事实源，目标运行环境为 openGauss 6.0。

## 文件用途

- `schema.sql`：全新数据库的完整结构。
- `seed.sql`：仅用于本地演示的景区、票种、时段和演示账号数据。
- `migrations/`：已有数据库的增量迁移，按文件名日期和名称顺序执行。

当前结构覆盖游客账号、常用出行人、票种与线路、时段库存、订单、支付、票码、管理员、系统设置、公告、核销、退款、审计和异步导出任务。

## 新数据库初始化

```bash
gsql -h 127.0.0.1 -p 15432 -U scenic_app -d scenic_ticket -f database/schema.sql
gsql -h 127.0.0.1 -p 15432 -U scenic_app -d scenic_ticket -f database/seed.sql
```

`seed.sql` 不应执行到含真实业务数据的数据库。

## 已有数据库升级

1. 先停止写入或进入维护窗口。
2. 使用 `gs_dump` 完成数据库备份并校验备份文件。
3. 对照迁移记录，只执行尚未应用的 SQL。
4. 每个迁移成功后再继续下一个，不要跳过失败。
5. 完成后检查 `/api/health/db`，再验证登录、下单、支付、退款和后台写操作。

```bash
for migration in database/migrations/*.sql; do
  echo "review and apply: $migration"
done
```

上面的循环只用于列出顺序，生产环境应由运维逐个确认后执行。

## 近期关键迁移

- `2026-07-05-add-admin-system-settings.sql`：系统设置与设置审计。
- `2026-07-09-add-passenger-templates.sql`：常用出行人。
- `2026-07-09-add-raft-assignment-to-order-items.sql`：订单乘筏分配信息。
- `2026-07-10-active-passenger-slot-index.sql`：出行人时段冲突查询索引。
- `2026-07-10-add-admin-device-audit.sql`：管理员设备与会话审计字段。
- `2026-07-13-add-visitor-refund-audit-actor.sql`：游客自助退款操作人类型和游客关联。

最后一个迁移使用条件 `DO` 块添加字段，避免 openGauss 6.0 不支持 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 的兼容性问题。

## 约束

- `schema.sql` 只用于新库，不能代替增量迁移。
- 迁移、后端代码和 API DTO 必须在同一版本发布。
- 不在 SQL 文件中写入真实数据库口令。
- 退款审计的 `operator_type` 必须为 `ADMIN` 或 `VISITOR`，且对应操作人只能有一类非空。
