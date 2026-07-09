# 架构说明

## 目标技术栈

- 后端：FastAPI
- 前端：React + Vite + Ant Design
- 数据库：openGauss / PostgreSQL 风格 SQL
- 测试：pytest、httpx、前端关键流程验证

## 目标目录

```text
backend/
  app/
    api/
    core/
    schemas/
    services/
    repositories/
  tests/
frontend/
  src/
    features/
    shared/
database/
docs/
legacy-node/
```

## 后端边界

- `api`：HTTP 路由、依赖注入、请求/响应 DTO。
- `schemas`：Pydantic DTO。
- `services`：业务规则、状态机、事务编排。
- `repositories`：SQL 和数据库行映射。
- `core`：配置、数据库、会话、CSRF、日志、错误处理。

## 前端边界

- `features/auth`：游客登录、实名注册、当前会话。
- `features/visitor-booking`：购票工作台。
- `features/orders`：我的订单、支付、取消。
- `shared/api`：请求封装、CSRF、幂等键、错误处理。
- `shared/theme`：Ant Design token 与视觉规则。

## 数据流

```text
React UI -> shared/api -> FastAPI api -> service -> repository -> database
```

公共响应必须经过 DTO，不直接返回数据库行。

