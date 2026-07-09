# 实施计划

日期：2026-06-28

本文档把已批准的重构设计拆成可执行任务。每个任务都必须遵守：

```text
定义 -> 契约 -> 威胁建模 -> 测试先行 -> 小步实现 -> 验收 -> 沉淀
```

## 0. 执行原则

- 每次只实现一个可验证切片。
- 不把旧 Node 代码逐行翻译成 Python。
- 不在没有测试或验收命令的情况下声称完成。
- 不把数据库行原样返回给前端。
- 状态变更接口默认需要 CSRF。
- 游客侧默认从会话读取 `visitor_id`，不信任前端提交归属字段。
- 每个阶段结束后更新 `docs/decision-log.md`。

## 1. 工具和运行约定

后端：

- Python 3。
- `requirements.txt` 管理依赖。
- FastAPI + Uvicorn。
- `psycopg` 连接 openGauss / PostgreSQL。
- pytest + httpx 做接口测试。

前端：

- npm。
- React + Vite + TypeScript。
- Ant Design。
- TanStack Query。

数据库：

- SQL 文件放在 `database/`。
- 先用显式 SQL 管理结构变化，不在第一阶段引入大型 ORM。

建议命令：

```bash
cd 服务器项目源码分类包/00_可直接运行的主工程_当前服务器正在运行

# 后端
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
pytest backend/tests
uvicorn app.main:app --app-dir backend --reload

# 前端
cd frontend
npm install
npm run dev
npm run build
```

## 2. 阶段 0：冻结旧基线

目标：保留可运行参照物，避免原地重构把现状弄丢。

任务：

1. 记录当前 Node 入口、接口和启动方式。
2. 新建 `legacy-node/`，移动旧 `src/`、`public/`、`tests/`、`package.json`、`package-lock.json`。
3. 在根 README 说明旧版位置和新版目标。
4. 保留旧 SQL 作为数据库参考源。

验收：

```bash
find legacy-node -maxdepth 2 -type f | head
test -f legacy-node/package.json
test -f docs/architecture.md
```

安全检查：

- 不移动真实 `.env`。
- 不提交数据库密码或线上密钥。

## 3. 阶段 1：工程骨架

目标：搭出空的 FastAPI 后端、React 前端和数据库目录，不实现业务。

任务：

1. 创建 `backend/`：
   - `app/main.py`
   - `app/core/config.py`
   - `app/core/errors.py`
   - `app/api/health.py`
   - `tests/test_health.py`
   - `requirements.txt`
2. 创建 `frontend/`：
   - Vite React TypeScript。
   - Ant Design provider。
   - 基础 App Shell。
3. 创建 `database/`：
   - `schema.sql`
   - `seed.sql`
   - `README.md`
4. 更新 README，说明新版启动命令。

验收：

```bash
pytest backend/tests
cd frontend && npm run build
```

安全检查：

- `.env.example` 只放示例值。
- 后端错误响应不返回堆栈。

## 4. 阶段 2：数据库和会话基础

目标：实现数据库连接、会话表和 CSRF 基础设施。

任务：

1. 从旧 SQL 提取 MVP 表：
   - `visitor`
   - `ticket_type`
   - `route_product`
   - `time_slot_quota`
   - `ticket_order`
   - `ticket_order_item`
   - `payment_record`
2. 增加调整：
   - `ticket_order.visitor_id`
   - `ticket_order_item` 支持 `PENDING_PAYMENT`
   - `payment_record.idempotency_key`
   - `user_session`
3. 实现数据库连接和事务 helper。
4. 实现统一响应和错误码。
5. 实现 CSRF token 生成、读取和校验。

验收：

```bash
pytest backend/tests/test_health.py
pytest backend/tests/test_security_basics.py
```

安全检查：

- Cookie 设置 HttpOnly、SameSite、过期时间。
- CSRF token 不写入日志。
- session token 只存哈希或不可逆摘要，避免数据库泄露后直接复用。

## 5. 阶段 3：游客认证和实名注册

目标：完成游客登录、实名注册、当前会话查询。

API：

```text
GET  /api/auth/csrf
POST /api/auth/visitor/login
POST /api/auth/visitor/register
GET  /api/auth/me
POST /api/auth/logout
```

任务：

1. 定义认证 DTO。
2. 实现游客手机号登录。
3. 实现实名注册。
4. 实现 `GET /api/auth/me`。
5. 前端实现登录/实名注册入口和账号状态区。

测试：

- 未登录访问 `me` 返回 401。
- 登录成功设置 HTTP-only Cookie。
- 缺 CSRF 的注册请求返回 403。
- 临时游客不能下单。
- 注册后 scope 变为实名游客。

验收：

```bash
pytest backend/tests/test_auth_api.py
cd frontend && npm run build
```

安全检查：

- 登录错误信息不泄露账号是否存在。
- 手机号和证件号校验在 DTO 层完成。
- 响应中不返回 session token。

## 6. 阶段 4：票种和时段目录

目标：实现游客可浏览票种和时段。

API：

```text
GET /api/catalog/products
GET /api/catalog/time-slots
```

任务：

1. 定义 `ProductPublicDTO`、`TimeSlotPublicDTO`。
2. 实现票种、线路产品、码头相关查询。
3. 实现日期和票种过滤。
4. 前端实现票种列表和时段选择。
5. 实现 loading、empty、error 状态。

测试：

- 公共接口不需要登录。
- 禁用产品不返回。
- 公共 DTO 不包含内部字段。
- 时段剩余量计算正确。

验收：

```bash
pytest backend/tests/test_catalog_api.py
cd frontend && npm run build
```

安全检查：

- 不返回内部备注、审计字段、管理字段。
- 不暴露不必要的库存策略字段。

## 7. 阶段 5：创建待支付订单

目标：实名游客可以创建待支付订单，但不扣库存。

API：

```text
POST /api/orders
GET  /api/me/orders
GET  /api/me/orders/{order_no}
```

任务：

1. 定义订单创建 DTO。
2. 实现订单金额计算。
3. 创建订单主表和订单明细。
4. 订单状态为 `CREATED`，明细状态为 `PENDING_PAYMENT`。
5. 前端实现订单确认和订单摘要。
6. 前端实现我的订单列表和订单详情入口。

测试：

- 未登录不能创建订单。
- 临时游客不能创建订单。
- 实名游客能创建待支付订单。
- 创建订单不扣库存。
- 游客不能查看别人的订单。

验收：

```bash
pytest backend/tests/test_order_create_api.py
cd frontend && npm run build
```

安全检查：

- 请求体中不能通过传 `visitor_id` 指定订单归属。
- 订单详情必须按当前会话过滤。

## 8. 阶段 6：模拟支付和库存事务

目标：支付成功后扣库存、写支付记录、生成票码。

API：

```text
POST /api/orders/{order_no}/pay
```

任务：

1. 支付接口要求 `Idempotency-Key`。
2. 事务内锁定订单。
3. 校验订单属于当前游客。
4. 校验订单状态为 `CREATED`。
5. 锁定时段库存。
6. 库存足够则扣库存。
7. 写 `payment_record`。
8. 生成票码。
9. 更新订单为 `PAID`，明细为 `UNUSED`。
10. 前端实现“模拟支付”和支付结果反馈。

测试：

- 缺 `Idempotency-Key` 返回 400。
- 重复相同幂等键不重复扣库存。
- 重复点击支付不重复出票。
- 库存不足返回 409。
- 支付别人订单返回 404 或 403。
- 事务失败回滚库存和订单状态。

验收：

```bash
pytest backend/tests/test_payment_api.py
cd frontend && npm run build
```

安全检查：

- 幂等键与订单、游客绑定。
- 并发支付不能造成超卖。
- 票码不使用可预测的简单递增值。

## 9. 阶段 7：取消订单和我的订单体验

目标：完成待支付订单取消和游客订单中心。

API：

```text
POST /api/orders/{order_no}/cancel
GET  /api/me/orders
GET  /api/me/orders/{order_no}
```

任务：

1. 只允许取消 `CREATED` 订单。
2. 已支付订单不能在 MVP 取消。
3. 前端订单列表支持状态筛选。
4. 订单详情展示票码、时段、金额、状态。
5. 小屏布局验证。

测试：

- 未支付订单可取消。
- 已支付订单取消返回业务错误。
- 取消别人的订单失败。
- 我的订单只返回当前游客订单。

验收：

```bash
pytest backend/tests/test_my_orders_api.py
cd frontend && npm run build
```

安全检查：

- 订单列表不返回其他游客订单。
- 证件号、手机号按场景脱敏。

## 10. 阶段 8：端到端验收和清理

目标：完成第一阶段闭环，清理迁移临时状态。

任务：

1. 写端到端验收脚本或 Playwright 检查：
   - 游客登录。
   - 实名注册。
   - 浏览票种。
   - 创建订单。
   - 模拟支付。
   - 查看我的订单。
2. 运行后端完整测试。
3. 运行前端 build。
4. 做 UI 响应式检查。
5. 做安全清单逐项审查。
6. 更新 `docs/decision-log.md` 和 README。

验收：

```bash
pytest backend/tests
cd frontend && npm run build
```

如果启用 Playwright：

```bash
cd frontend && npm run test:e2e
```

安全检查：

- 按 `docs/security-checklist.md` 全量勾一遍。
- 抽样检查真实 API 响应字段。
- 确认日志没有敏感字段。

## 11. 第一批推荐开工顺序

按这个顺序开工最稳：

1. `P0-1` 冻结旧基线和目录迁移。
2. `P1-1` FastAPI 最小骨架和健康检查。
3. `P1-2` React + Vite + Ant Design 最小骨架。
4. `P2-1` 数据库 MVP schema 和 session 表。
5. `P3-1` CSRF + Cookie session。
6. `P3-2` 游客登录、实名注册、`/auth/me`。
7. `P4-1` catalog public DTO 和接口。
8. `P5-1` 创建待支付订单。
9. `P6-1` 模拟支付事务和幂等。
10. `P7-1` 我的订单页面和取消订单。

## 12. 单任务上下文模板

以后每次让 AI 做一个切片时，使用这个模板：

```text
任务：
只实现 <一个明确切片>。

必须读取：
- docs/project-brief.md
- docs/architecture.md
- docs/api-contract.md
- docs/security-checklist.md
- <本切片相关源码路径>

范围：
- 做：
- 不做：

契约：
- API：
- DTO：
- 状态：
- 错误码：

安全：
- 权限：
- CSRF：
- DTO 字段：
- 日志脱敏：

验收：
- 命令：
- 期望：
- 需要截图/响应样例：
```

