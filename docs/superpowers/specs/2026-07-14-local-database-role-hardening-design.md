# 本地数据库角色与认证加固设计

日期：2026-07-14

## 1. 目标

加固当前项目下 `.data/postgres` 的本地 PostgreSQL 16 开发库，在不丢数据、不把密码提交到 Git、不让 FastAPI 使用超级用户的前提下，完成认证和权限分离。

## 2. 当前问题

- `pg_hba.conf` 对 Unix socket、`127.0.0.1` 和 `::1` 使用 `trust`，本机进程可在不提供密码时声称为任意数据库角色。
- `dingdexin` 是超级用户。
- `scenic_app` 不是超级用户，但拥有 `scenic_ticket` 数据库和 public schema 中的业务对象，权限高于运行应用所需。
- 没有独立的只读查询角色。

## 3. 角色模型

| 角色 | 能否登录 | 职责 |
|---|---:|---|
| `dingdexin` | 是，仅本地 Unix socket peer | 本地数据库维护和应急恢复 |
| `scenic_owner` | 否 | 持有数据库、schema、表和序列 |
| `scenic_app` | 是，SCRAM | FastAPI 业务连接；仅有业务表 DML 和序列使用权限 |
| `scenic_readonly` | 是，SCRAM | 本地查询和演示；仅有 `SELECT` |

`scenic_app` 不得创建角色、创建数据库、创建表、删除表或修改表结构。

## 4. 认证模型

`pg_hba.conf` 调整为：

```text
local   all          all                              peer
host    all          all          127.0.0.1/32        scram-sha-256
host    all          all          ::1/128             scram-sha-256
local   replication  all                              peer
host    replication  all          127.0.0.1/32        scram-sha-256
host    replication  all          ::1/128             scram-sha-256
```

数据库继续只监听 `127.0.0.1:15432`，不对局域网或公网开放。

## 5. 密码与本地配置

加固脚本用 Python `secrets` 为 `scenic_app` 和 `scenic_readonly` 生成独立的高强度随机密码，数据库使用 SCRAM-SHA-256 保存验证信息。

本地连接信息写入 Git 已忽略的 `.data/local-db.env`，权限为 `0600`。脚本和验收输出不打印密码。

FastAPI 启动前执行：

```bash
set -a
source .data/local-db.env
set +a
```

## 6. 执行流程

1. 确认 PostgreSQL 数据目录、服务状态和当前数据库。
2. 在 `.data/backups/` 生成加固前的 custom-format 数据库备份。
3. 备份原 `pg_hba.conf`。
4. 在单个数据库事务中创建/更新角色、转移所有权并设置最小权限。
5. 原子写入 `.data/local-db.env` 和新的 `pg_hba.conf`。
6. 重新加载 PostgreSQL 认证配置。
7. 执行正向连接和越权拒绝验证。

脚本应可重复执行：已有角色会被校正属性并轮换密码，不重复创建对象。

## 7. 失败与回退

- 任何权限调整失败时回滚数据库事务，不更换 `pg_hba.conf`。
- 如认证重载后连接验证失败，脚本立即恢复本次备份的 `pg_hba.conf` 并再次 reload。
- 数据对象权限需要完整回退时，使用加固前 `.dump` 备份恢复；恢复前先保留当前数据库的额外备份。

## 8. 验收标准

- TCP 不提供密码时无法登录 `scenic_app`。
- `scenic_app` 使用 `.data/local-db.env` 可连接并对业务表执行必要 DML，但 `CREATE TABLE` 被拒绝。
- `scenic_readonly` 可执行 `SELECT`，`UPDATE` 被拒绝。
- `scenic_owner` 不能登录。
- `dingdexin` 仍可通过本机 Unix socket peer 进行应急维护。
- FastAPI 使用加固后环境变量时，`ping_database()` 返回成功。
- 密码不出现在 Git 变更、日志或命令行参数中。

## 9. 不在本次范围

- 不修改线上 openGauss 实例。
- 不按每张表或每个 API 继续拆分更细的应用角色。
- 不修改 FastAPI 业务代码。
- 不将本地密码同步到线上或任何共享密钥系统。
