# 遇龙河景区票务系统

面向游客购票与景区运营管理的一体化系统，主线技术栈为 FastAPI、React、Vite、Ant Design 和 openGauss。线上演示地址：<http://scenic.ddx123.xyz/>。

旧版 Node / Express / 静态页面基线已归档到 `legacy-node/`，只作为参考源，不作为当前主线继续开发。

## 当前系统能力

- 游客 CSRF 初始化、账号密码注册/登录、当前会话查询和退出登录。
- 公共票种和时段目录查询。
- 游客常用出行人增删改查、订单出行人分配和重复时段校验。
- 登录游客创建待支付订单。
- 模拟支付，支持 `Idempotency-Key`，支付成功后扣库存、生成票码；当前支付 provider 固定为 `PAYMENT_PROVIDER=mock`。
- 我的订单列表、详情、状态筛选、电子票码和移动端订单卡片。
- 待支付订单取消；符合期限且未核销的已支付订单支持游客自助退款。
- 游客购票、我的订单和游客服务页面已按 iPhone 15 Pro（393 × 852）完成移动端验收。
- 第二阶段管理员能力：管理员登录、当前管理员、管理员退出、游客/管理员 session 隔离、后台订单只读列表/详情 API、单张票码核销 API、批量核销 API、撤销核销 API、批量撤销核销 API、撤销核销原因审计、核销审计日志、核销/撤销失败尝试审计及 CSV/XLSX 导出、全局检索、原因筛选和 CSV/XLSX 导出 API、全单模拟退款 API、部分模拟退款 API、退款审计日志、全局检索和 CSV/XLSX 导出 API、后台运营汇总报表 API、后台支付对账汇总 API、后台支付对账汇总 CSV/XLSX 导出、后台产品维度报表 API、后台产品维度报表 CSV/XLSX 导出、后台日报趋势报表 API、后台小时趋势报表 API、后台月度趋势报表 API、后台趋势报表补零、后台趋势报表 CSV/XLSX 导出、后台同步导出行数上限、后台异步导出任务基础、后台异步导出任务文件格式筛选、后台异步导出 filters 白名单、后台异步导出 worker 状态机基础、后台异步导出失败字段长度契约对齐、后台异步导出文件下载端点、后台异步导出失败任务手动/自动重试、后台异步导出自动重试延迟领取、后台异步导出 RUNNING 超时回收、后台异步导出 RUNNING 超时最终失败告警事件记录、后台异步导出本地孤儿文件补偿清理、后台异步导出告警 provider 边界、后台异步导出最终失败告警事件记录、后台异步导出告警事件只读查询 API、后台异步导出告警事件汇总 API、后台异步导出告警事件确认 API、后台异步导出告警事件批量确认 API、后台异步导出告警事件关闭和重开 API、后台异步导出告警事件批量关闭 API、后台异步导出告警事件关闭筛选和汇总增强、后台异步导出告警事件去重静默、后台异步导出告警事件类型和格式筛选、后台异步导出告警事件删除 API、后台异步导出告警事件批量删除 API、后台异步订单明细 CSV/XLSX 生成 worker、后台异步核销审计 CSV/XLSX 生成 worker、后台异步核销失败审计 CSV/XLSX 生成 worker、后台异步退款审计 CSV/XLSX 生成 worker、后台异步支付对账 CSV/XLSX 生成 worker、后台异步产品维度报表 CSV/XLSX 生成 worker、后台异步日报趋势 CSV/XLSX 生成 worker、后台异步小时趋势 CSV/XLSX 生成 worker、后台异步月度趋势 CSV/XLSX 生成 worker、模拟支付回调安全边界，以及后台订单 CSV/XLSX 导出。

## 后端启动

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

环境变量参考 `.env.example`。不要提交真实 `.env`、数据库密码、Cookie、CSRF token 或线上密钥。

本地开发默认允许 `localhost` / `127.0.0.1` 前端源跨端口携带 Cookie 访问后端。部署到非本机环境时，使用 `CORS_ALLOWED_ORIGINS` 配置明确域名，并收紧或清空 `CORS_ALLOWED_ORIGIN_REGEX`。

`APP_ENV=production` 时后端会拒绝不安全配置：必须设置 `COOKIE_SECURE=true`、非空 `DB_PASSWORD`、明确的 HTTPS `CORS_ALLOWED_ORIGINS`，并清空 `CORS_ALLOWED_ORIGIN_REGEX`。生产 CORS 不允许 `*`、`localhost`、`127.0.0.1` 或带路径/查询参数的 origin。支付当前只支持 `PAYMENT_PROVIDER=mock`；未实现的 `wechat`、`alipay`、`stripe`、`unionpay` 或其他真实支付 provider 会在启动配置校验阶段被拒绝。短信当前只支持 `SMS_PROVIDER=disabled`；未实现的 `aliyun`、`tencent`、`twilio` 或其他短信 provider 会在启动配置校验阶段被拒绝。登录限流当前只支持 `LOGIN_RATE_LIMIT_PROVIDER=memory`；未实现的 `redis`、`memcached`、`gateway` 或其他全局限流 provider 会在启动配置校验阶段被拒绝。异步导出文件存储当前只支持 `ADMIN_EXPORT_STORAGE_PROVIDER=local`，任务队列当前只支持 `ADMIN_EXPORT_QUEUE_PROVIDER=database`，失败告警当前只支持 `ADMIN_EXPORT_ALERT_PROVIDER=disabled`；未实现的 `s3`、`oss`、`redis`、`celery`、`webhook` 或其他 provider 会在启动配置校验阶段被拒绝。

前端读取 CSRF Cookie 时依赖浏览器同 hostname Cookie 规则。联调时页面和 API 可以不同端口，但 hostname 要一致：前端打开 `http://localhost:5173` 时，`VITE_API_BASE_URL` 应使用 `http://localhost:<后端端口>`；前端打开 `http://127.0.0.1:5173` 时，API 也使用 `127.0.0.1`。

前端共享 API client 默认读取 `scenic_csrf` Cookie；如果后端通过 `CSRF_COOKIE_NAME` 改名，前端环境也要同步设置 `VITE_CSRF_COOKIE_NAME`，否则状态变更请求无法注入 CSRF token。

游客登录接口默认按客户端地址和账号限制为 60 秒内 5 次，可通过 `LOGIN_RATE_LIMIT_MAX_ATTEMPTS` 和 `LOGIN_RATE_LIMIT_WINDOW_SECONDS` 调整。当前使用 `SMS_PROVIDER=disabled` 和 `LOGIN_RATE_LIMIT_PROVIDER=memory` 进程内内存限速；真实短信验证码、账号风控、多进程或多实例全局限速都需要后续单独接入，未实现 provider 会被拒绝启动。

## 后端测试

```bash
.venv/bin/pytest backend/tests
```

联调排障：

- `GET /api/health` 只确认 API 进程可用。
- `GET /api/health/db` 同时确认数据库连接可用；失败时返回 `503 DATABASE_UNAVAILABLE`，不会暴露连接串或底层异常。

接口级游客购票闭环验收：

```bash
.venv/bin/pytest backend/tests/test_visitor_flow_api.py
```

后端阶段验收脚本：

```bash
scripts/verify-backend.sh
```

该脚本先跑游客购票闭环测试，再跑后端全量测试。当前对话提交后端切片前默认使用它或等价命令作为验收入口。

联调前完整验收脚本：

```bash
scripts/verify-integration.sh
```

该脚本会依次运行后端闭环与全量测试、导出 OpenAPI 契约、执行前端 `npm run lint` 和 `npm run build`。默认不启动真实浏览器，也不修改前端源码，适合作为前后端合并前的最小互通门禁。需要浏览器 smoke 时显式运行：

```bash
VERIFY_INTEGRATION_E2E=1 scripts/verify-integration.sh
```

`VERIFY_INTEGRATION_E2E=1` 等价于 `mock`，会启动前端临时 mock API，不依赖真实后端浏览器环境，并会忽略外部 `E2E_API_BASE_URL`。后端已启动并需要真实 API smoke 时使用：

```bash
VERIFY_INTEGRATION_E2E=real scripts/verify-integration.sh
```

真实 API 地址默认是 `http://127.0.0.1:8000`，如需覆盖：

```bash
VERIFY_INTEGRATION_E2E=real E2E_API_BASE_URL=http://127.0.0.1:8001 scripts/verify-integration.sh
```

浏览器 smoke 当前聚焦游客端注册登录、常用出行人、下单、支付、退款和移动端布局；管理端接口、权限与写操作由后端 pytest 覆盖，生产发布时再执行真实管理员 smoke。

后端里程碑完成度和下一阶段边界见 `docs/backend-milestone-status.md`，其中已包含管理员认证、订单只读、单张/批量/撤销/批量撤销核销、撤销核销原因审计、核销/撤销失败尝试审计及 CSV/XLSX 导出、核销审计检索/导出、整单/部分退款、退款审计日志与检索/导出、报表和导出切片。阶段 8 后端验收证据见 `docs/backend-acceptance-report.md`。安全清单到代码和测试的逐项映射见 `docs/backend-security-audit.md`。

导出 OpenAPI 契约给前端联调用：

```bash
scripts/export-openapi.py /tmp/scenic-ticket-openapi.json
```

不传输出路径时会把 JSON 打印到 stdout。该契约包含统一成功响应 `ApiSuccessDTO<T>` 和失败响应 `ApiFailureDTO`。

单次处理一条后台异步导出任务：

```bash
scripts/process-admin-export-job.py
```

循环处理后台异步导出任务：

```bash
scripts/run-admin-export-worker.py --max-idle-loops 12 --idle-sleep-seconds 5
```

Linux 部署环境可参考 `deploy/systemd/scenic-ticket-admin-export-worker.service` 把循环 worker 交给 systemd 常驻运行和自动重启；也可参考 `deploy/systemd/scenic-ticket-admin-export-cleanup.service` 与 `deploy/systemd/scenic-ticket-admin-export-cleanup.timer` 每日清理过期成功导出文件。导出文件存储当前通过 `ADMIN_EXPORT_STORAGE_PROVIDER=local` 固定为本地受控目录，异步任务队列当前通过 `ADMIN_EXPORT_QUEUE_PROVIDER=database` 固定为数据库表和行锁，失败告警当前通过 `ADMIN_EXPORT_ALERT_PROVIDER=disabled` 显式关闭；worker 最终失败会写入本地告警事件，管理员可通过只读 API 查询和按导出类型、文件格式汇总筛选，但不发送外部通知；生产对象存储、外部队列和邮件/Webhook 告警 provider 尚未接入，配置为其他 provider 会被拒绝启动。

当前 worker 支持 `ORDER_DETAIL + CSV/XLSX`、`CHECK_IN_AUDIT + CSV/XLSX`、`CHECK_IN_FAILURE_AUDIT + CSV/XLSX`、`REFUND_AUDIT + CSV/XLSX`、`PAYMENT_RECONCILIATION + CSV/XLSX`、`PRODUCT_BREAKDOWN + CSV/XLSX`、`DAILY_TREND + CSV/XLSX`、`HOURLY_TREND + CSV/XLSX` 和 `MONTHLY_TREND + CSV/XLSX`，会生成文件并配合 `GET /api/admin/export-jobs/{job_id}/download` 下载；worker 未预期异常会自动重试一次，重试前延迟 60 秒，超过 30 分钟仍处于 `RUNNING` 的任务会在下一轮 worker 领取前按重试额度回收，耗尽后落为 `FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT` 并记录本地告警事件，worker 写出文件后若成功落库失败会尽力删除刚生成的本地文件，worker 标记最终失败或超时回收最终失败时会记录本地告警事件但不发送外部通知，业务/校验失败不自动重试，失败任务也可通过 `POST /api/admin/export-jobs/{job_id}/retry` 手动回到 `PENDING`；过期成功任务文件可通过 `scripts/cleanup-admin-export-files.py --older-than-days 7 --limit 100` 手动清理，或用 `systemctl enable --now scenic-ticket-admin-export-cleanup.timer` 启用每日清理；异常任务元数据中的未知导出类型或格式仍会标记为暂不支持，后续继续拆分生产对象存储和外部队列服务。

后端测试会读取前端共享 API 类型和请求入口，检查 `frontend/src/shared/api/types.ts` 的 DTO 字段、`frontend/src/shared/api/client.ts` / `endpoints.ts` 的 method/path/query key 是否能被当前后端 OpenAPI 支持，并校验 `apiRequest<T>()` 的前端返回类型与后端 OpenAPI `data` schema 对齐。它也会检查 Cookie、CSRF、默认 CSRF Cookie 名和 `Idempotency-Key` 这些后端运行时安全约定。前端线程调整共享 API 层后，应同步运行 `scripts/verify-backend.sh` 或至少运行：

```bash
.venv/bin/pytest backend/tests/test_api_dto_contract.py backend/tests/test_frontend_endpoint_contract.py
```

## API 工作流

1. `GET /api/auth/csrf` 获取 CSRF Cookie。
2. `POST /api/auth/visitor/register` 使用账号、密码和手机号注册；已有账号使用 `POST /api/auth/visitor/login` 登录。
3. `GET/POST/PATCH/DELETE /api/me/passenger-templates` 维护常用出行人。
4. `GET /api/catalog/products` 和 `GET /api/catalog/time-slots` 浏览票种与时段。
5. `POST /api/orders` 创建待支付订单。
6. `POST /api/orders/{order_no}/pay` 模拟支付，必须带 `Idempotency-Key`。
7. `GET /api/me/orders` / `GET /api/me/orders/{order_no}` 查看订单。
8. `POST /api/orders/{order_no}/cancel` 仅取消当前游客自己的待支付订单。
9. `POST /api/orders/{order_no}/refund` 在退票期限内申请游客自助退款。

## 使用与部署文档

- Windows 从 GitHub 拉取并启动：[docs/windows-setup.md](docs/windows-setup.md)
- 游客端和管理端操作：[docs/usage.md](docs/usage.md)
- 本地前端说明：[frontend/README.md](frontend/README.md)
- 数据库初始化与迁移：[database/README.md](database/README.md)
- 生产部署与回滚：[docs/deployment.md](docs/deployment.md)
- 系统架构：[docs/architecture.md](docs/architecture.md)
- API 契约：[docs/api-contract.md](docs/api-contract.md)
- 版本变更：[CHANGELOG.md](CHANGELOG.md)

## 安全边界

- 状态变更接口校验 CSRF。
- 游客登录接口有 MVP 内存限速，超限返回统一 `429 RATE_LIMITED`。
- 会话使用 HTTP-only Cookie。
- CORS 默认只放行本机开发源并允许 Cookie。
- 当前前端通过 `document.cookie` 读取 CSRF Cookie，因此页面和 API URL 要使用相同 hostname。
- 后端从会话读取 `visitor_id`，不信任前端提交订单归属字段。
- 游客订单 DTO 不返回 `visitorId`、证件号、session token、CSRF token。
- 订单手机号按场景脱敏。
- 支付在事务内锁定订单并用条件更新库存防超卖。
