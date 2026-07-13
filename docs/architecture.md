# 架构说明

## 技术栈

- 前端：React、TypeScript、Vite、Ant Design、TanStack Query
- 后端：FastAPI、Pydantic、psycopg
- 数据库：openGauss 6.0
- 部署：Nginx、systemd、openGauss 容器
- 测试：pytest、httpx、oxlint、Chrome CDP E2E

## 运行拓扑

```text
Browser
  -> Nginx
     -> frontend/dist 静态资源
     -> /api/* -> FastAPI (127.0.0.1:8000)
                    -> service
                    -> repository
                    -> openGauss
```

## 后端边界

- `api`：路由、依赖注入和 HTTP 边界。
- `schemas`：Pydantic 请求/响应 DTO。
- `services`：权限、状态机、业务规则与事务编排。
- `repositories`：参数化 SQL 和数据库行映射。
- `core`：配置、数据库、Cookie/CSRF、请求日志和统一错误。

游客、管理员使用不同的服务端 session Cookie。状态变更请求校验双提交 CSRF；订单归属和管理权限只从后端 session 获取。

## 前端边界

- `app`：游客端与管理端应用壳、响应式导航。
- `features/auth`：游客账号注册、登录和退出。
- `features/booking`：票种、时段、出行人、订单确认和支付。
- `features/orders`：订单列表、票码、取消和游客退款。
- `features/visitor-service`：景区服务信息。
- `features/admin` 与 `features/admin-*`：运营工作台、票种、设置、订单、核销、审计、报表和导出。
- `shared/api`：统一请求、CSRF、DTO 和 endpoint wrapper。

## 数据库事实源

- 新库：`database/schema.sql`
- 开发种子：`database/seed.sql`
- 线上升级：`database/migrations/*.sql`

数据库迁移必须和对应后端版本一起发布。退款审计同时支持管理员与游客操作人，并通过约束保证操作人类型和外键一致。

## 响应契约

所有 API 使用统一成功/失败包络并返回 `requestId`。公共接口必须经过 DTO，不直接暴露数据库行、密码 hash、session、CSRF token 或内部归属字段。
