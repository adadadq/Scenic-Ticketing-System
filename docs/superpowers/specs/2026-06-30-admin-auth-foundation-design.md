# 管理员权限基座设计

日期：2026-06-30

## 问题

第一阶段游客购票 MVP 已经完成，后续核销、退款、报表和后台维护都需要管理员身份。当前 FastAPI 主线只有游客会话，`user_session` 已预留 `account_type = 'ADMIN'` 和 `admin_user_id`，但没有 `admin_user` 表、管理员登录接口或后台权限依赖。

旧 Node 基线有管理员登录和后台路由，但它使用 Bearer token 与浏览器本地存储思路。第二阶段不能照搬旧实现，应沿用当前后端的 HTTP-only Cookie、session-bound CSRF、统一响应壳和 DTO 防泄露边界。

## 范围

本切片只做管理员认证与权限基座：

- 新增 `admin_user` SQL 基线和演示 seed。
- 新增管理员登录、当前管理员、管理员退出接口。
- 新增管理员 DTO、repository、service 和 `require_admin_session` 依赖。
- 把管理员状态变更接口纳入 CSRF / OpenAPI header 契约。
- 补后端测试和安全审查证据。

本切片不做：

- 管理员页面、React 组件或视觉设计。
- 线路产品 CRUD、时段维护、核销、退款、报表。
- 真实短信、真实支付、支付回调或生产部署。
- 从旧 Node 代码逐行迁移。

## API

计划新增接口：

```text
POST /api/admin/auth/login
GET  /api/admin/auth/me
POST /api/admin/auth/logout
```

说明：

- `POST /api/admin/auth/login` 是状态变更接口，必须先通过 `GET /api/auth/csrf` 初始化 CSRF Cookie，并携带配置化 CSRF header。
- `GET /api/admin/auth/me` 只接受管理员 session；游客 session 不能通过。
- `POST /api/admin/auth/logout` 只退出管理员 session，并清理 session Cookie 与 CSRF Cookie。

## DTO

请求：

```json
{
  "username": "admin",
  "password": "demo password"
}
```

响应 `AdminMeDTO`：

```json
{
  "adminUserId": 1,
  "username": "admin",
  "displayName": "演示管理员",
  "role": "SUPER_ADMIN"
}
```

DTO 规则：

- 请求体拒绝额外字段。
- 响应不返回 `passwordHash`、session token、CSRF token、内部备注或审计字段。
- 字段使用 camelCase，便于前端共享 API 类型直接消费。

## 数据

新增 `admin_user`：

```text
id
username
display_name
password_hash
role
status
created_at
updated_at
```

约束：

- `username` 唯一。
- `role` MVP 只允许 `SUPER_ADMIN`、`OPERATOR`。
- `status` 只允许 `ENABLED`、`DISABLED`。
- `user_session.admin_user_id` 应引用 `admin_user(id)`。

演示 seed：

- 只放明显演示用途的管理员账号。
- 不放真实明文密码、真实手机号、真实姓名或线上密钥。
- 口令哈希采用 Python 标准库 `hashlib.pbkdf2_hmac` 的带盐格式，避免新增依赖；后续生产可迁移到 Argon2 或 bcrypt。
- MVP 哈希格式固定为 `pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`。
- `iterations` 固定为 `260000`；salt 使用 `secrets.token_bytes(16)` 生成 16 字节随机值；派生结果长度为 32 字节。
- 校验时必须解析格式、重新派生并使用 `hmac.compare_digest` 做 constant-time 比较；格式错误或算法不匹配统一视为密码错误。

## 权限

- 管理员 session 写入 `user_session.account_type = 'ADMIN'` 和 `admin_user_id`。
- 游客 session 继续写入 `account_type = 'VISITOR'` 和 `visitor_id`。
- 游客和管理员鉴权依赖分开：游客订单接口只接受游客 session，后台接口只接受管理员 session。
- 管理员必须 `status = 'ENABLED'` 才能登录；登录后被禁用的既有 session 已由 `docs/superpowers/specs/2026-07-02-disabled-admin-session-boundary-design.md` 单独补齐撤销边界。
- `role` 本切片只进入 DTO、session 语义和后续授权扩展点；不在本切片定义后台业务权限矩阵。后续线路维护、核销、退款和报表接口再分别定义 `SUPER_ADMIN` 与 `OPERATOR` 权限。

## 登录限速

- 管理员登录必须新增独立限速器，不复用游客手机号登录 key。
- 限速 key 使用 `client_host + hash(username)`，避免日志或内存调试信息暴露明文账号。
- MVP 默认窗口为 60 秒内 5 次失败尝试；成功登录后清理该 key 的失败计数。
- 达到限制返回 `429 RATE_LIMITED`，不会创建管理员 session，不会设置 session Cookie。
- 限速失败不消费或轮换 CSRF；窗口过期后，同一个 CSRF token 可以继续尝试登录。
- 后续多进程或多实例生产部署时，管理员登录限速必须迁移到 Redis、网关或负载均衡层。

## CSRF 与 Cookie

- 管理员登录和退出都必须通过 double-submit CSRF。
- 管理员已登录后的状态变更必须校验 header token 与当前 session 保存的 `csrf_token_hash` 绑定关系。
- session token 仍只放 HTTP-only Cookie，数据库只保存哈希。
- CSRF token 仍只通过可读 CSRF Cookie 传给前端，JSON 不返回 token。

## 错误码

- 未登录或无有效管理员 session：`401 ADMIN_AUTH_REQUIRED`。
- 游客 session 访问管理员接口：`403 ADMIN_FORBIDDEN`。
- 用户名不存在、密码错误、账号禁用：统一 `401 ADMIN_LOGIN_FAILED`，消息固定为“管理员账号或密码错误”。
- 缺 CSRF 或 CSRF 无效：沿用 `403 CSRF_INVALID`。
- 请求体验证失败：沿用 `422 VALIDATION_ERROR`，不回显字段路径或输入值。

## 安全测试

必须覆盖：

- 管理员登录成功设置 HTTP-only session Cookie。
- 登录成功响应不包含 `passwordHash`、session token、CSRF token。
- 错误账号、错误密码、禁用管理员返回同一个 `ADMIN_LOGIN_FAILED`。
- 连续错误管理员登录被限速，限速不创建 session、不设置 session Cookie、不破坏 CSRF 重试路径。
- 缺 CSRF 的登录和退出返回 `CSRF_INVALID`。
- `GET /api/admin/auth/me` 未登录返回 `ADMIN_AUTH_REQUIRED`。
- 游客 session 访问 `GET /api/admin/auth/me` 返回 `ADMIN_FORBIDDEN`。
- 游客 session 调用 `POST /api/admin/auth/logout` 返回 `ADMIN_FORBIDDEN`，不能误清理游客会话。
- 管理员退出后旧 session 失效，并清理 session Cookie 与 CSRF Cookie。
- PBKDF2 hash 生成和校验覆盖格式、迭代次数、salt 长度和 constant-time 比较。
- OpenAPI 为新增状态变更接口声明配置化 CSRF header 和 `x-request-id` 响应头。
- `database/schema.sql` 和 `database/seed.sql` 不包含明文演示密码或真实形态敏感数据。

## 验收命令

目标测试：

```bash
.venv/bin/pytest backend/tests/test_admin_auth_api.py backend/tests/test_openapi_contract.py backend/tests/test_schema_contract.py -q
```

后端切片验收：

```bash
scripts/verify-backend.sh
```

影响前端共享 API 后，再运行：

```bash
scripts/verify-integration.sh
```

## 前端协作

前端对话后续需要补共享 API 类型和调用入口：

- `AdminMe`
- `adminAuthApi.login()`
- `adminAuthApi.me()`
- `adminAuthApi.logout()`

在前端共享 API 更新前，后端可以先通过 OpenAPI 和后端接口测试完成权限基座；共享 API 对齐后再把相关调用纳入 `backend/tests/test_frontend_endpoint_contract.py`。
