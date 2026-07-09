# 景区票务系统 Python + React 重构设计

日期：2026-06-28

## 1. 目标

把当前 Node.js + 原生前端项目原地重构为一个更清晰、可扩展、可学习的项目：

- 后端改为 FastAPI。
- 前端改为 React + Vite + Ant Design。
- 第一阶段只实现游客购票 MVP。
- 通过设计文档、测试、安全清单和决策日志沉淀完整开发工作流。
- 用小切片、可验证任务减少 AI 协作时的 token 浪费。

## 2. 已确认决策

- 迁移方式：原地替换，但分阶段接管。
- 迁移策略：重设计迁移，不逐行翻译旧 Node 代码。
- MVP：游客购票闭环。
- 支付：模拟支付。
- 技术栈：FastAPI + React + Vite + Ant Design。
- 认证：HTTP-only Cookie 会话 + CSRF。
- 前端视觉：浅色运营工作台，参考已生成的游客购票工作台草图。

## 3. MVP 范围

第一阶段只做游客购票闭环：

- 游客手机号进入系统。
- 游客实名注册后才能下单。
- 浏览票种、日期、时段和剩余名额。
- 创建待支付订单。
- 模拟支付成功后扣库存并生成票码。
- 查看我的订单。
- 游客只能查看、支付、取消自己的订单。

第一阶段不做：

- 管理员后台。
- 核销。
- 退款。
- 报表。
- 真实第三方支付。

这些能力作为第二阶段扩展。

## 4. 目录结构

目标主工程目录：

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

职责边界：

- `backend/`：FastAPI、Pydantic DTO、业务服务、数据库访问、pytest。
- `frontend/`：React 页面、表单、API client、主题与组件。
- `database/`：建表 SQL、迁移、种子数据、ERD。
- `docs/`：项目事实源、架构、接口、安全清单、决策日志。
- `legacy-node/`：迁移期临时保留旧 Node 基线，最后归档或删除。

## 5. 后端设计

后端使用 FastAPI。

模块边界：

- `api`：路由、依赖注入、HTTP 状态码、请求/响应 DTO。
- `schemas`：Pydantic 模型，区分请求、公共响应、内部模型、管理员响应。
- `services`：业务规则、订单状态机、事务编排。
- `repositories`：SQL 和数据库行映射。
- `core`：配置、数据库连接、会话、CSRF、错误处理、日志。

后端不直接把数据库行返回给前端。所有公共接口都必须经过专门 DTO。

## 6. 数据模型与状态机

MVP 保留旧 SQL 的主体表：

- `visitor`
- `ticket_type`
- `route_product`
- `time_slot_quota`
- `ticket_order`
- `ticket_order_item`
- `payment_record`

需要调整：

- `ticket_order` 增加 `visitor_id`，明确订单归属。
- `ticket_order_item` 增加 `PENDING_PAYMENT` 状态，支付成功后变 `UNUSED`。
- `payment_record` 增加 `idempotency_key`，防重复支付。
- 新增 `user_session` 表，替代旧版内存 Map 会话。

订单状态：

```text
CREATED -> PAID
CREATED -> CANCELLED
PAID -> COMPLETED  # 第二阶段核销后使用
PAID -> REFUNDING  # 第二阶段退款后使用
```

MVP 规则：

- 创建订单时不扣库存。
- 模拟支付成功时扣库存并生成票码。
- 支付接口必须幂等。
- 支付事务中锁订单、锁时段库存、检查状态、扣库存、写支付记录、生成票码。

## 7. API 契约

公共接口：

```text
GET  /api/health
GET  /api/catalog/products
GET  /api/catalog/time-slots
POST /api/auth/visitor/login
POST /api/auth/visitor/register
GET  /api/auth/csrf
```

游客接口：

```text
GET  /api/auth/me
POST /api/orders
POST /api/orders/{order_no}/pay
POST /api/orders/{order_no}/cancel
GET  /api/me/orders
GET  /api/me/orders/{order_no}
```

安全规则：

- 游客侧默认使用 `/me` 风格，从会话中获取 `visitor_id`。
- 前端不能通过提交 `visitor_id` 决定订单归属。
- 状态变更接口校验 CSRF。
- 支付接口需要 `Idempotency-Key`。
- 登录失败使用统一错误信息，避免账号枚举。
- 错误响应不暴露 SQL、堆栈、表名或内部字段。

响应契约：

```json
{
  "success": true,
  "data": {},
  "request_id": "..."
}
```

```json
{
  "success": false,
  "code": "ORDER_NOT_FOUND",
  "message": "订单不存在或无权限访问",
  "request_id": "..."
}
```

## 8. 前端蓝图

设计读法：

> 景区票务与码头运营系统，面向游客和运营人员，以清晰可信、工作流驱动的视觉语言呈现，倾向 Ant Design 的运营工作台风格，加入少量遇龙河/码头业务识别，不做营销首页或大片装饰背景。

设计旋钮：

- `DESIGN_VARIANCE 4/10`
- `MOTION_INTENSITY 2/10`
- `VISUAL_DENSITY 7/10`

MVP 页面：

- 游客购票工作台。
- 我的订单。
- 管理员工作台预留，不在第一阶段实现。

前端模块：

- `features/auth`
- `features/visitor-booking`
- `features/orders`
- `shared/api`
- `shared/theme`
- `shared/components`

状态策略：

- Server state 使用 TanStack Query。
- 表单状态使用 Ant Design Form。
- 少用全局状态。

已生成草图：

- `docs/frontend/mockups/visitor-booking-workbench-v1.png`

草图采用：

- 左侧业务导航。
- 顶部状态栏。
- 步骤条。
- 票种表格。
- 日期与时段选择。
- 右侧订单摘要。
- 主按钮“模拟支付”。

草图不采用：

- 错误生成的“清江画廊”品牌文字。
- 不可读小字。
- 具体随机文案和图标。

## 9. 测试策略

后端测试：

- `pytest`
- `httpx`
- 接口测试覆盖认证、票种、下单、支付、我的订单。

业务测试：

- 库存不足。
- 重复支付。
- 幂等键复用。
- 越权查看订单。
- 越权支付订单。
- 事务回滚。

前端验证：

- 购票流程。
- 我的订单。
- loading、empty、error、success、disabled 状态。
- 桌面、平板、手机宽度。
- 无水平溢出。
- 长产品名和脱敏证件号不破坏布局。

## 10. 安全清单

必须检查：

- 游客只能访问自己的订单。
- 公共接口不返回内部模型。
- Cookie 设置 HttpOnly、SameSite、过期时间。
- 状态变更接口校验 CSRF。
- 支付接口幂等。
- 并发支付不会重复扣库存。
- 错误响应不暴露 SQL 或堆栈。
- 日志脱敏手机号、证件号、Cookie、CSRF token。
- 登录接口有限速和统一错误信息。

## 11. 低 Token 工作流

每次开发只做一个功能切片。给 AI 的上下文包固定为四块：

```text
Task Brief：本次做什么、不做什么、成功标准
Relevant Files：只给相关文件和路径，不全量喂项目
Contracts：API、DTO、状态、安全约束
Verification：必跑命令、期望输出、截图或响应样例
```

每个功能切片固定流程：

```text
定义 -> 契约 -> 威胁建模 -> 测试先行 -> 小步实现 -> 验收 -> 沉淀
```

## 12. 实施阶段

阶段 0：盘点冻结

- 记录旧项目接口、数据库、启动命令。
- 把旧 Node 运行链路迁入 `legacy-node/` 或等价归档位置。

阶段 1：工程骨架

- 创建 `backend/` FastAPI 骨架。
- 创建 `frontend/` React + Vite + Ant Design 骨架。
- 建立 `database/` 和 `docs/`。

阶段 2：游客认证与会话

- 实现 Cookie session。
- 实现 CSRF。
- 实现游客登录和实名注册。

阶段 3：票种与时段

- 实现公共 catalog 接口。
- 实现公开 DTO。
- 前端展示票种和时段。

阶段 4：订单与模拟支付

- 创建待支付订单。
- 模拟支付。
- 扣库存。
- 生成票码。
- 我的订单。

阶段 5：验收与清理

- 完成测试。
- 做安全审查。
- 清理旧 Node 链路。
- 更新决策日志和复盘。

## 13. 非目标

- 不接真实支付。
- 不做复杂营销页。
- 不一次性重做后台、核销、退款和报表。
- 不引入大型 ORM 抽象，除非后续明确需要。
- 不把 imagegen 草图当作固定像素稿照抄。

