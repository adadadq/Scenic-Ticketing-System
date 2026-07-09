# 决策日志

## 2026-06-28

### 原地替换，但分阶段接管

原因：用户希望最终项目目录干净，但直接删除旧代码风险高。先保留旧 Node 基线，逐步让 Python 后端和 React 前端接管。

### 选择重设计迁移

原因：目标不只是换语言，还要理解完整开发工作流、学习安全和做出更高质量项目。

### 第一阶段只做游客购票 MVP

原因：游客购票闭环能覆盖 API 契约、数据库事务、订单状态机、权限控制、DTO 防泄露和测试闭环。

### 使用模拟支付

原因：不接真实第三方支付，但保留订单状态机、幂等、防重复提交、退款前置条件等真实业务学习点。

### 使用 FastAPI + React + Vite + Ant Design

原因：FastAPI 适合 API 契约和 Pydantic DTO；React + Ant Design 适合票务、订单、库存、报表类运营系统。

### 使用 HTTP-only Cookie 会话 + CSRF

原因：比前端保存 Bearer token 更适合学习 Web 安全；能自然引入 XSS token 保护、CSRF、防会话固定和退出失效。

### 使用 imagegen 生成前端草图

原因：先明确视觉方向，再转成 token、组件和布局规则。草图只作为方向参考，不作为像素级实现稿。

### 先补齐 MVP 页面设计稿集

原因：只有全栈实施计划还不够，前端需要先明确页面级设计，避免直接写 React 时凭感觉堆组件。已补齐登录 / 实名注册、游客购票工作台、我的订单 / 订单详情、移动端购票流程四类设计稿，并沉淀到 `docs/frontend/page-design.md`。

### 未支付订单取消不回补库存

原因：MVP 采用支付成功时才扣库存的事务模型，`CREATED` 订单只是待支付意向，不预占库存。因此取消订单只更新订单和明细状态，不更新 `time_slot_quota`，避免引入“未扣先补”的库存错误。

### 后端端到端验收先用接口级测试

原因：前端页面由另一个对话并行重构，当前后端线程先用 FastAPI TestClient 串通 CSRF、登录、实名、catalog、下单、支付、订单中心和取消边界。这样既能证明 API 契约闭环，也不阻塞前端视觉和交互实现。

### 用 DTO 契约测试保护前后端互通

原因：前端已开始按 `frontend/src/shared/api/types.ts` 调真实 API，后端字段名、敏感字段过滤和请求体 `extra=forbid` 都会直接影响联调。新增 DTO 契约测试，把 camelCase 字段、订单票码省略规则、禁止前端指定 `visitorId` 等规则固定下来。

### 用错误响应契约测试保护前端 ApiError

原因：前端统一客户端依赖失败响应中的 `success`、`code`、`message`、`request_id` 字段。如果后端框架层请求体验证、CSRF 或 404 回退到默认结构，联调时错误提示和 request id 追踪都会失效。新增错误契约测试，要求失败响应体和 `x-request-id` 响应头保持一致，并禁止把校验细节、原始输入或堆栈返回给前端。

### 将 CSRF token 绑定到当前 session

原因：普通 double-submit 只能证明 header 和 cookie 相等，不能证明这个 token 就是登录时写入当前 session 的 token。后端已经在 `user_session.csrf_token_hash` 保存哈希，因此状态变更请求在通过 header/cookie 校验后，还要验证 header token 与当前 session 哈希匹配。这样能防止登录后 CSRF cookie 被替换成另一个匹配 header/cookie 的值后仍然通过订单、支付、取消或退出操作。为保证页面刷新后的前端联调体验，`GET /api/auth/csrf` 在请求携带有效 session 时会把新 token hash 重新绑定到当前 session。

### 用成功响应契约测试保护前端 ApiSuccess

原因：前端 `apiRequest<T>` 依赖成功响应中的 `success`、`data`、`request_id` 字段，并用 `x-request-id` 辅助排查问题。新增成功契约测试，要求代表性成功接口保持统一响应壳子，并覆盖前端不传 `x-request-id` 时服务端生成非空 request id 的路径。

### 生产环境拒绝开发安全配置

原因：文档提醒“部署时收紧 CORS、开启 Secure Cookie”容易被遗漏。后端在 `APP_ENV=production` 时主动校验 `COOKIE_SECURE`、`DB_PASSWORD`、`CORS_ALLOWED_ORIGINS` 和 `CORS_ALLOWED_ORIGIN_REGEX`，把高风险部署错误提前变成启动失败，而不是上线后暴露 Cookie 或开放错误来源。生产 CORS origin 必须是明确 HTTPS origin，不接受通配符、本机开发源、路径或查询参数。

### 退出登录同时清理 CSRF Cookie

原因：session-bound CSRF 已经让旧 CSRF token 无法单独越权，但退出登录应清理浏览器侧认证相关状态，避免前端保留过期 token 造成误导或后续流程歧义。`POST /api/auth/logout` 撤销服务端 session 后，同时过期 session Cookie 和 CSRF Cookie。

### 接口闭环验收抽样检查敏感字段

原因：后端和前端并行开发时，接口“能跑通”不等于“适合给页面直接消费”。在游客购票闭环测试中抽样检查 catalog 与订单响应，确保订单归属字段、证件信息、session/CSRF 相关字段和原始手机号不会混入页面 DTO，避免联调后才发现字段泄露或前端误依赖内部字段。

### 拆分 API 与数据库健康检查

原因：前端联调和部署排障需要区分“FastAPI 进程活着”和“数据库可用”。保留 `GET /api/health` 作为轻量进程健康检查，新增 `GET /api/health/db` 执行数据库 ping；数据库不可用时统一返回 `503 DATABASE_UNAVAILABLE`，不暴露 DSN、密码、host 或底层异常。

### Auth 请求 DTO 拒绝额外字段

原因：登录和实名注册只需要前端提交明确的身份输入。额外的 `visitorId`、`sessionToken`、`csrfToken` 等客户端控制字段即使当前不会被使用，也不应被默默忽略，否则容易让前端误依赖无效字段，或让安全边界显得含糊。Auth 请求 DTO 改为 `extra=forbid`，验证失败仍走统一 `422 VALIDATION_ERROR` 且不回显字段和值。

### 我的订单列表返回明细摘要字段

原因：前端订单列表的 view model 会从 `OrderMeDTO.items` 读取票种、游玩日期、时段、票数和票码摘要。接口契约已经把 `GET /api/me/orders` 定义为返回 `OrderMeDTO`，因此真实 Postgres repository 不能只返回订单主表空 `items`。列表查询现在会加载订单明细，保证 fake 测试、真实数据库实现和前端类型一致。

### 固化后端阶段验收脚本

原因：阶段 8 要求端到端验收和后端完整测试，且当前对话只负责后端。新增 `scripts/verify-backend.sh` 作为后端固定验收入口，先跑游客登录、实名、catalog、下单、支付、订单中心和敏感字段抽样的闭环测试，再跑 `backend/tests` 全量测试，减少每个后端切片收尾时遗漏验收命令的风险。

### 给后端路由补 OpenAPI 成功响应模型

原因：实际接口已经统一返回 `ApiSuccess<T>`，但路由只标注 `dict` 会让 OpenAPI 文档丢失 `data` 的具体 DTO 类型，前端联调时只能靠手写文档和测试猜契约。为已实现的 health、auth、catalog、orders 接口补 `response_model=ApiSuccessDTO[...]`，让运行时响应、文档契约和前端 TypeScript 类型保持同一方向。

### OpenAPI 错误响应改为前端 ApiError 契约

原因：运行时错误处理已经把校验失败、业务错误、404 和 500 统一成 `success/code/message/request_id`，但 OpenAPI 仍会为请求体验证自动生成 FastAPI 默认 `HTTPValidationError.detail`。这会误导前端按 `detail/loc` 写错误解析，也和“验证错误不回显字段和值”的安全要求冲突。后端现在在 OpenAPI 中统一使用 `ApiFailureDTO` 描述失败响应。

### 阶段 8 后端安全审查沉淀为证据表

原因：安全清单只列原则和测试文件还不够，后续联调或答辩时需要能快速说明“每一条安全要求由什么代码或测试证明”。新增 `docs/backend-security-audit.md`，把会话、CSRF、CORS、权限、DTO、防泄露、支付幂等、库存事务、错误响应和日志边界逐项映射到测试证据，并明确后续新增日志、管理员接口或真实支付时必须重新审查。

### 提供后端 OpenAPI 离线导出入口

原因：前端线程需要稳定参考后端接口契约，但不一定总能依赖正在运行的后端服务。新增 `scripts/export-openapi.py`，可直接从 FastAPI app 导出 OpenAPI JSON，包含统一成功/失败响应模型，方便前端联调、类型检查或人工核对。

### 游客登录先采用 MVP 内存限速

原因：总设计安全清单要求登录接口有限速，但当前第一阶段没有 Redis、网关或多实例部署设施。先在 FastAPI app 实例内按客户端地址和手机号哈希做 60 秒 5 次的滑动窗口限速，超限统一返回 `429 RATE_LIMITED`，满足本地联调和 MVP 自动化滥用防护；生产多进程或多实例部署时再迁移到 Redis、网关或负载均衡层全局限速。

### 后端测试读取前端共享 API 类型

原因：前后端并行开发时，接口 DTO 容易出现“后端测试绿、前端类型已变”的错位。新增跨端契约测试，直接读取 `frontend/src/shared/api/types.ts`，把 `VisitorMe`、catalog、订单 DTO 字段和 `OrderStatusFilter` 与后端 DTO/状态集合对齐。这样前端类型变化会在后端验收中显式暴露，减少联调阶段的隐性字段漂移。

### 后端测试读取前端共享 API 请求入口

原因：只校验 DTO 还不够，前端可能新增、改名或误写请求路径和查询参数，导致类型仍然匹配但运行时 404 或 422。新增后端侧 endpoint 契约测试，读取 `frontend/src/shared/api/client.ts` 与 `frontend/src/shared/api/endpoints.ts` 中的 `apiRequest(...)` 调用，把 method/path/query key 归一化后与 FastAPI OpenAPI 对齐。这个测试不执行前端、不引入 Node，也不修改前端文件，只把“前端共享 API 层正在调用后端不存在的接口或参数”提前暴露在后端验收里。

### 后端测试覆盖前端共享 API client 的安全请求行为

原因：前后端真正联通不只取决于 URL 和 DTO，还取决于浏览器是否携带 HTTP-only session Cookie、状态变更是否注入后端返回的 CSRF header、支付是否带 `Idempotency-Key`。这些约定如果只写在文档里，前端共享 client 一次重构就可能悄悄破坏。后端契约测试现在会读取 `frontend/src/shared/api/client.ts` 和 `endpoints.ts`，校验 `credentials: 'include'`、CSRF bootstrap、非 GET 注入 CSRF、POST 不跳过 CSRF，以及支付调用传入幂等键；仍然不执行或修改前端代码。

### 后端测试校验前端返回类型和 OpenAPI data schema

原因：只确认前端请求路径存在还不够，`apiRequest<T>()` 的泛型如果和后端 OpenAPI 200 响应壳子里的 `data` schema 不一致，前端仍会在运行时拿错字段。后端契约测试现在会读取前端共享 API 调用的返回类型，并映射到后端 OpenAPI 的 DTO schema，覆盖 health、auth、catalog、orders、支付和取消等共享入口。

### 用测试保护 API 契约文档 endpoint 清单

原因：`docs/api-contract.md` 是前后端协作时最容易被人直接阅读的接口清单，但真实路由以 FastAPI OpenAPI 为准。新增 OpenAPI 契约测试，双向比对文档中的 `GET/POST /api/...` 清单和后端 OpenAPI，避免新增接口漏写文档或文档保留已经不存在的接口。

### 在 OpenAPI 中声明状态变更 CSRF header

原因：运行时已经要求登录、实名注册、退出、下单、支付和取消接口带 CSRF header，但这些接口通过 `Request` 手动校验，FastAPI 默认不会把 `x-csrf-token` 写进 OpenAPI。后端现在在 OpenAPI 后处理阶段为状态变更接口补必需的 CSRF header，并用契约测试固定，避免前端联调或离线契约工具漏掉安全请求头。

### 固定配置化 CSRF header 的前端可见契约

原因：前端不会硬编码 CSRF header 名，而是从 `GET /api/auth/csrf` 的 `data.headerName` 读取。后端测试现在覆盖自定义 `CSRF_HEADER_NAME` 会同步出现在 CSRF bootstrap 响应、CORS 预检允许头和 OpenAPI 状态变更接口 header 参数中，避免配置化后出现“接口告诉前端一个名字，浏览器预检或 OpenAPI 却是另一个名字”的联调错误。

### 固定默认 CSRF Cookie 名的前后端一致性

原因：CSRF token 本体通过可读 Cookie 传给前端，前端共享 API client 默认从 `scenic_csrf` 读取。后端测试现在读取前端 `VITE_CSRF_COOKIE_NAME` fallback，并与后端默认 `CSRF_COOKIE_NAME` 对齐；如果后端改默认 Cookie 名或前端改默认读取名，后端契约测试会提前失败。若部署时自定义 `CSRF_COOKIE_NAME`，前端也必须同步设置 `VITE_CSRF_COOKIE_NAME`。

### 增加联调前完整验收脚本

原因：阶段 8 的闭环验收不能只停留在“后端测试绿”或“前端 build 另找时间跑”。新增 `scripts/verify-integration.sh`，依次运行后端闭环与全量测试、导出后端 OpenAPI、执行前端 `npm run lint` 和 `npm run build`。这个脚本默认不启动真实浏览器、不修改前端源码，用作前后端合并前的最小互通门禁；浏览器 e2e smoke 需通过 `VERIFY_INTEGRATION_E2E=1` 显式开启，避免把前端线程的视觉/浏览器稳定性问题变成后端每个切片的默认阻塞。

### 未处理异常也走统一失败契约

原因：阶段 8 的安全清单要求错误响应不暴露 SQL、堆栈、表名和敏感字段。验证错误、CSRF、404 和数据库健康检查已有脱敏覆盖后，仍需要把普通未处理异常的 500 响应也锁进前端 `ApiError` 契约。后端测试现在用 `raise_server_exceptions=False` 观察真实客户端响应，确认异常消息里的表名、证件字段、Cookie/CSRF 词不会出现在响应体中。

### 集成验收检查 OpenAPI JSON 结构

原因：联调前验收脚本导出 OpenAPI 后只检查文件非空，不能证明前端拿到的是可解析、包含接口路径和 DTO schema 的契约。`scripts/verify-integration.sh` 现在会解析导出的 JSON，并确认存在 `paths` 与 `components.schemas`，让“离线契约可用”成为集成门禁的一部分。

### 校验可配置 Cookie 和 CSRF header 名

原因：`SESSION_COOKIE_NAME`、`CSRF_COOKIE_NAME` 和 `CSRF_HEADER_NAME` 会进入 Set-Cookie、请求头读取、CORS 预检和 OpenAPI 契约。允许空值、空格、分号或 CRLF 一类非法字符会让前后端联调行为不稳定，甚至埋下响应头/请求头注入风险。后端配置加载现在会要求这些名称都是非空 HTTP token，不合规则在启动前失败。

### 后端测试保护前端错误码分支

原因：前端会用 `ApiError.code` 做登录态和订单状态判断，例如把 `AUTH_REQUIRED` 当成“未登录但不是系统故障”。如果前端新增或改错硬编码错误码，普通 DTO 和路径契约测试不会发现。后端契约测试现在读取前端源码中的错误码比较，并与后端 `AppError` 和统一错误处理器产出的错误码对齐；`INVALID_RESPONSE`、`CSRF_TOKEN_MISSING` 这类前端本地错误码单独列白名单。

### CORS 暴露 request id 响应头

原因：响应体已经携带 `request_id`，但前端的异常兜底也会尝试读取 `X-Request-Id` 响应头。浏览器跨域请求默认不允许 JS 读取自定义响应头，因此后端 CORS 现在显式 `expose_headers=["x-request-id"]`，并用测试固定本地前端源能看到该响应头，方便联调排障。

### 固定数据库健康检查前端返回类型

原因：前端共享 API 新增 `healthApi.database()`，并把 `/api/health/db` 的返回值标成 `DatabaseHealthPayload`。后端接口已经通过 OpenAPI 暴露 `DatabaseHealthDTO`，因此跨端契约测试需要把这个前端类型映射到对应后端 schema，避免前端能编译但后端互通门禁无法确认 `data` 结构。

### 订单明细持久化线路产品 ID

原因：前端订单 DTO 和下单请求都以 `productId` 表达具体线路产品，订单明细也应保存购买当时的 `product_id`。如果只通过 `ticket_type_id` 反查 `route_product`，后续解除 MVP 的“一票种一线路产品”限制时，历史订单明细可能展示错产品。`ticket_order_item` 现在持久化 `product_id`，并用 `(product_id, ticket_type_id)` 复合外键保证产品和票种一致；真实数据库 repository 创建订单时写入该字段，读取订单明细和支付出票时按 `toi.product_id` 关联产品。

### 固定非待支付订单的支付错误码

原因：前端支付失败分支会根据后端错误码展示可重试或不可继续的业务状态。后端现在用测试明确只有 `CREATED + UNPAID` 订单可进入扣库存、写支付记录和出票流程；取消订单或 `CREATED` 但支付状态已失败的订单再次支付都会返回 `409 ORDER_NOT_PAYABLE`，避免非待支付订单产生库存或票码副作用。

### 固定库存不足支付副作用边界

原因：前端会把 `TIME_SLOT_QUOTA_NOT_ENOUGH` 作为阻断继续支付的业务错误。后端现在用测试明确 Postgres repository 的库存条件更新返回空结果后会返回库存不足错误，并且不会写 `payment_record`、不会生成票码、不会把订单更新为已支付，避免库存不足路径产生半支付状态。

### 固定取消订单状态机边界

原因：API 契约要求只有 `CREATED + UNPAID` 订单可取消，前端也按这两个字段决定是否展示取消动作。后端现在用测试覆盖 `PAID` 订单和 `CREATED` 但支付状态已失败的订单都会返回 `ORDER_NOT_CANCELABLE`，并且 SQL repository 层会在更新明细、更新订单或触碰库存前停止，避免取消流程把非待支付订单改成取消态。

### 固定库存不足后的订单恢复路径

原因：前端在收到 `TIME_SLOT_QUOTA_NOT_ENOUGH` 后会阻断继续支付，并允许用户刷新或取消这个订单。后端现在用接口闭环测试明确库存不足支付失败不会把订单改成失败或已支付，也不会生成票码；订单仍保持 `CREATED + UNPAID`，后续取消会变成 `CANCELLED`，库存计数不被额外改动。

### 固定时段查询的产品过滤契约

原因：后端 `GET /api/catalog/time-slots` 已支持按 `productId` 过滤时段，适合前端在同一票种存在多线路产品时进一步收窄结果。现在把 `productId` 从“后续可加”改为正式可选查询参数，并用 OpenAPI 测试锁定 `visitDate`、`ticketTypeId` 和 `productId` 三个查询参数。

### 固定 Catalog 读取失败错误码

原因：前端购票页会在票品或时段接口失败时展示演示数据兜底，后端需要给这两类失败提供稳定且可区分的错误码。现在票品读取失败返回 `503 CATALOG_UNAVAILABLE`，时段读取失败返回 `503 TIME_SLOTS_UNAVAILABLE`，并用测试确认响应仍走统一失败壳子且不暴露底层异常、证件字段或 CSRF 信息。

### 固定登录限流不产生会话

原因：前端登录页会把 `RATE_LIMITED` 展示为失败提示，并保持未登录状态。后端现在用测试明确未登录用户被限流时只返回 `429 RATE_LIMITED`，不会创建临时游客、不会写入 session，也不会设置 HTTP-only 登录 Cookie，避免限流失败路径意外变成半登录状态。

### 固定登录限流后的 CSRF 重试路径

原因：前端登录页在第一次提交遇到 `RATE_LIMITED` 后，会继续保留当前页面和 CSRF Cookie，用户稍后重试时不应该被迫重新 bootstrap CSRF。后端现在用测试明确限流失败不会消费或轮换 CSRF，限流窗口过期后，同一个 CSRF token 可以完成游客登录，并被哈希绑定到新 session。

### 增加最小安全请求日志

原因：阶段 8 安全清理要求确认日志不记录证件号、Cookie 或 CSRF。后端现在只记录请求摘要：method、path、status、安全化 request id 和耗时，不记录 query、请求体、Cookie、CSRF header 或 CSRF Cookie；未处理 500 也会写同样的摘要日志。响应里的 `x-request-id` 仍按接口契约原样回传给前端，日志里的 request id 会先校验字符和长度，纯数字等容易承载手机号/证件号的值会降级为 `[invalid]`。

### 固定集成验收脚本的 Python 入口

原因：`scripts/export-openapi.py` 已经会优先切到项目 `.venv`，但 `scripts/verify-integration.sh` 后续解析导出的 OpenAPI JSON 时仍直接调用系统 `python3`。这会让本机和 CI 在 Python 路径上出现细微漂移。集成脚本现在统一使用可覆盖的 `PYTHON_BIN`，默认优先 `.venv/bin/python`，没有虚拟环境时再回退到 `python3`。

### 在 OpenAPI 中声明 request id 响应头

原因：前端统一 API client 会从响应体 `request_id` 和响应头 `x-request-id` 里做错误追踪，但此前 OpenAPI 只描述了响应体字段，没有描述响应头。后端现在为所有已实现接口的成功、验证失败和默认错误响应声明 `x-request-id` header，并用契约测试固定，避免离线契约工具或前端联调人员漏掉排障响应头。

### 固定我的订单状态筛选枚举

原因：前端订单页的筛选控件只允许 `CREATED`、`PAID`、`CANCELLED` 三种状态，后端 OpenAPI 也需要暴露同一个枚举，避免联调或接口生成工具把 `status` 当成任意字符串。后端仍保留服务层归一化和业务校验，非法状态统一返回 `422 ORDER_STATUS_INVALID`，响应体带 request id 且不回显非法输入。

### 同步导出先加行数上限再做异步任务

原因：后台订单、审计和报表 CSV/XLSX 已经能同步下载，但直接让查询返回任意行数会把数据库、内存和请求线程风险留到联调后期。先用统一 `SYNC_EXPORT_ROW_LIMIT` 给多行同步导出加 5000 行上限，查询层用参数化 `LIMIT` 做 `limit + 1` 探测，超过上限返回 `413 ADMIN_EXPORT_TOO_LARGE`；真正的异步导出任务、文件存储和下载链接再作为后续切片设计。

### 异步导出先落任务元数据

原因：完整异步导出包含队列、worker、文件生成、存储、下载链接和清理策略，单切片直接做完容易把边界搅乱。先落 `admin_export_job` 表和创建/列表/详情 API，让前端能接任务状态流，也让后续 worker 有稳定任务契约；当前只创建 `PENDING` 任务，不生成文件、不暴露存储路径。

### 异步导出先收紧 filters 白名单

原因：导出任务表已经能保存 `filters`，但后续 worker 会把这些值作为生成 CSV/XLSX 的输入。先按 `exportType` 固定允许字段、日期格式、枚举值和布尔归一化，能阻止客户端把未知字段、内部控制字段或无效筛选写进任务元数据；文件生成、下载链接、对象存储和公开 filters 脱敏继续作为后续切片。

### 异步导出公开 filters 脱敏

原因：异步导出 worker 需要完整 `filters` 生成文件，但创建、列表、详情和重试接口是给管理台轮询展示用的公开响应，不应原样回显票码、订单号或操作人用户名这类运营查询条件。现在 API 响应只保留筛选字段结构，`ticketCode`、`orderNo`、`operatorUsername` 返回 `***`；内部 worker 仍从数据库读取完整 `filters`，避免脱敏值影响文件生成。

### 异步导出 worker 脚本输出也复用公开 filters 脱敏

原因：单次 worker 和循环 worker 脚本的 stdout 常会进入终端、CI 或 systemd journal，即使它们不是前端 API，也属于公开运维输出面。现在脚本输出的 `job` 和 `lastJob` 复用公开 filters 脱敏规则，避免把票码、订单号或操作人用户名写入日志；内部 worker 处理任务时仍使用完整 `filters`。

### 异步导出任务保存创建 requestId

原因：导出任务从创建、轮询、worker 处理到文件下载会跨多个请求和进程，前端或运维排障时需要一个轻量关联点。现在创建任务时保存统一响应中的 request id，并在 `AdminExportJobDTO.requestId` 返回；它只用于排障关联，不参与权限、幂等、任务领取或文件生成，避免把可控请求头误用成安全边界。

### 异步导出先铺 worker 状态机

原因：文件生成前必须先保证任务不会被多个 worker 重复领取，也不能让非运行中任务被误标记成功或失败。先实现内部 `PENDING -> RUNNING -> SUCCEEDED/FAILED` 状态机，用行锁领取最早待处理任务，并把成功/失败更新限制在 `RUNNING` 任务上；真实 CSV/XLSX 生成、对象存储、下载链接、重试和清理继续拆成后续切片。

### 异步导出失败字段长度契约对齐

原因：worker 失败入口的服务层限制已经是错误码 80、错误信息 500，但旧表列宽仍是 64/200，可能出现校验通过后 Postgres 写入失败。先用新增迁移扩 `admin_export_job` 失败字段，并把内部告警事件的错误码列宽同步到 80；不改变公开 DTO、错误码语义或真实告警。

### 异步导出先补受控下载端点

原因：异步导出任务已经能登记筛选条件和 worker 状态，但前端还缺少下载已生成文件的稳定契约。先补 `GET /api/admin/export-jobs/{job_id}/download`，只允许管理员读取 `SUCCEEDED` 且有文件元数据的任务，并把内部 `storage_key` 限制在 `ADMIN_EXPORT_STORAGE_DIR` 内；文件生成、生产对象存储、重试和清理继续作为后续切片，避免把下载权限边界和生成逻辑混在一起。

### 异步导出先跑通订单 CSV 生成

原因：创建、轮询和下载接口都有了，但如果没有任何 worker 生成文件，前端只能联调“空任务流”。先让单次 worker 支持 `ORDER_DETAIL + CSV`，复用已验证的订单同步 CSV 口径生成文件并写入受控本地目录；其他类型和格式先失败落库，避免卡在 `RUNNING`。常驻队列、XLSX、其他导出类型、生产对象存储、重试和清理继续拆成后续切片。

### 异步订单明细 worker 补齐 XLSX

原因：创建、轮询、下载和订单 CSV 生成已经能支撑异步任务主链路，但前端会在同一任务入口选择 `ORDER_DETAIL + XLSX`。后端现在让单次 worker 复用同步订单 XLSX 口径生成文件，继续由服务端派生 `storage_key`，并沿用 inline string、无公式节点和 XML 控制字符清洗；其他导出类型、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步导出补核销审计 CSV

原因：订单明细 CSV/XLSX 已经跑通异步任务主链路，下一类前端常见导出是核销审计日志。后端现在让单次 worker 支持 `CHECK_IN_AUDIT + CSV`，复用同步核销审计 CSV 的筛选、字段和公式注入防护，继续由服务端派生 `storage_key`；`CHECK_IN_AUDIT + XLSX`、其他审计类型、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步核销审计 worker 补齐 XLSX

原因：核销审计 CSV 已经跑通异步任务链路，前端同一个导出入口也需要 Excel 友好的 XLSX 文件。后端现在让单次 worker 支持 `CHECK_IN_AUDIT + XLSX`，复用同步核销审计 XLSX 的筛选、字段、inline string、无公式节点和 XML 控制字符清洗，继续由服务端派生 `storage_key`；其他审计类型、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步导出补核销失败审计 CSV

原因：核销失败审计已经有同步 CSV/XLSX 导出和异步任务 filters 白名单，下一步需要让大范围失败审计留档先走异步任务。后端现在让单次 worker 支持 `CHECK_IN_FAILURE_AUDIT + CSV`，复用同步核销失败审计 CSV 的筛选、失败码枚举校验、字段和公式注入防护，继续由服务端派生 `storage_key`；`CHECK_IN_FAILURE_AUDIT + XLSX`、退款审计、报表类异步生成、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步核销失败审计 worker 补齐 XLSX

原因：核销失败审计 CSV 已经接入异步任务，前端同一个失败审计导出入口也需要 Excel 友好的 XLSX 文件。后端现在让单次 worker 支持 `CHECK_IN_FAILURE_AUDIT + XLSX`，复用同步核销失败审计 XLSX 的筛选、失败码枚举校验、字段、inline string、无公式节点和 XML 控制字符清洗，继续由服务端派生 `storage_key`；退款审计、报表类异步生成、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步退款审计 worker 补齐 CSV

原因：核销相关审计已经跑通异步任务链路，退款审计是后台运营留档的下一类高频表格。后端现在让单次 worker 支持 `REFUND_AUDIT + CSV`，复用同步退款审计 CSV 的筛选、退款类型枚举校验、字段和公式注入防护，继续由服务端派生 `storage_key`；`REFUND_AUDIT + XLSX`、报表类异步生成、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步退款审计 worker 补齐 XLSX

原因：退款审计 CSV 已经接入异步任务，后台运营也需要直接下载 Excel 友好的退款审计文件。后端现在让单次 worker 支持 `REFUND_AUDIT + XLSX`，复用同步退款审计 XLSX 的筛选、退款类型枚举校验、字段、inline string、无公式节点和 XML 控制字符清洗，继续由服务端派生 `storage_key`；报表类异步生成、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 统一订单不存在和无权限错误

原因：前端订单详情错误块会展示业务错误文案、错误码和请求编号；后端不能让错误文案暴露订单是否真实存在或属于其他游客。订单详情、支付、取消遇到不存在或非当前游客订单时统一返回 `404 ORDER_NOT_FOUND`，消息固定为“订单不存在或无权限访问”，响应体不回显订单号，减少订单枚举风险。

### 固定支付非业务异常的脱敏边界

原因：模拟支付流程会写库存、支付记录、票码和订单状态，任何非业务异常都必须交给事务上下文回滚，并且不能把 SQL、订单号或幂等键暴露给前端。后端现在用测试固定：支付仓储层写支付记录失败会向外抛出，不继续出票或更新订单；HTTP 层统一返回 `500 INTERNAL_SERVER_ERROR` 和“服务暂时不可用”，响应仍带 request id。

### 沉淀阶段 8 后端验收报告

原因：第一阶段游客购票 MVP 的后端、API 契约、安全边界和前端共享 API 互通门禁已经形成稳定验收证据，不能只留在聊天记录或一次性命令输出里。新增 `docs/backend-acceptance-report.md` 记录 `scripts/verify-integration.sh` 的游客闭环、后端全量、OpenAPI 导出、前端 lint/build 和已知边界；README 也提供该报告与 `docs/backend-security-audit.md` 的入口，方便后续联调、复盘和答辩时快速找到事实源。

### 归档旧 Node 基线

原因：阶段 0 要求冻结旧基线，避免重构过程中把原有 Express 后端、静态页面和旧 Node 测试散落在当前主线根目录。现在把旧版 `package.json`、`package-lock.json`、`src/`、`public/` 和 `tests/` 移到 `legacy-node/`，并补说明文件和结构测试。后续需要参考旧业务规则时从该目录读取，但新功能仍进入 FastAPI、React 和 SQL 主线。

### 固定 seed 数据脱敏边界

原因：`database/seed.sql` 是数据库事实源的一部分，演示数据如果使用真实形态姓名、手机号或证件号，后续复制、截图或答辩时容易把样例误当真实数据传播。现在把游客 seed 改成明显演示值，并用测试禁止旧的真实形态样例回流；SQL 文件也不应定义角色、用户、密码或环境级状态，避免把部署配置混进数据库基线。

### 沉淀后端里程碑状态矩阵

原因：第一阶段后端已经形成实现、测试、安全审查和联调门禁，但继续推进时仍需要一个比聊天记录更稳定的阶段导航。新增 `docs/backend-milestone-status.md`，把阶段 0 到阶段 8 的后端状态、证据文件和下一步边界集中起来，并用测试确保所有计划阶段都有状态记录。后续涉及管理员、退款、核销、真实支付、报表或生产部署时，必须先补问题、契约、威胁模型和验收命令，再进入代码实现。

### 确定第二阶段先做管理员权限基座

原因：核销、退款、报表和后台维护都依赖稳定的管理员身份与权限边界。旧 Node 基线已有后台登录和管理路由，但它使用 Bearer token 与本地存储思路，不能直接迁移到当前 FastAPI 主线。第二阶段先设计 `admin_user`、管理员登录、管理员 session、`require_admin_session` 和 CSRF/OpenAPI/DTO 防泄露测试，仍沿用 HTTP-only Cookie、session-bound CSRF 和统一响应壳；后台业务 CRUD、核销、退款和报表在权限基座完成后再单独建模。

### 登录限流 provider 边界

原因：游客和管理员登录限流当前仍是进程内内存实现，适合 MVP 和单实例联调。如果允许 `LOGIN_RATE_LIMIT_PROVIDER=redis` 或 `gateway` 静默通过，部署环境容易误以为全局限流已经生效。先新增 `LOGIN_RATE_LIMIT_PROVIDER=memory` 配置边界，未知 provider 在配置校验阶段拒绝启动；真实 Redis、网关、负载均衡层或风控服务继续拆成后续切片。

### 短信 provider 边界

原因：当前游客登录是课程 MVP 的手机号直登演示流，没有短信验证码生命周期、发送频率、供应商签名、回调或账单对账。如果允许 `SMS_PROVIDER=aliyun`、`tencent` 或 `twilio` 静默通过，部署环境容易误以为真实短信已经接入。先新增 `SMS_PROVIDER=disabled` 配置边界，未知 provider 在配置校验阶段拒绝启动；真实短信验证码和账号风控继续拆成后续切片。

### 第二阶段先铺后台订单只读数据面

原因：前端管理台最先需要跨订单检索，但核销和退款会改变订单状态，必须更谨慎地设计状态机和审计边界。因此权限基座后先实现 `GET /api/admin/orders` 与 `GET /api/admin/orders/{order_no}`，只读返回专门的 Admin DTO、筛选分页和脱敏手机号，不复用游客 `OrderMeDTO` 或数据库行。后续核销、退款和报表在这个只读数据面上继续分片。

### 单张票码核销先于退款和报表

原因：已支付订单生成票码后，现场运营最核心的下一步是核销。核销会把明细从 `UNUSED` 改为 `USED`，并增加时段 `quota_checked_in`，属于必须校验管理员 session 和 session-bound CSRF 的状态变更。先实现单张票码核销，可以把 `PAID -> COMPLETED` 状态机、重复核销防护和库存核销量边界固定下来；批量核销、撤销核销、审计日志、退款和报表继续作为后续独立切片。

### 退款先做全单模拟退款

原因：退款同时影响订单、明细、支付记录和库存售出量，如果一开始就做部分退款和真实支付回调，状态机复杂度会过高。第二阶段先实现管理员全单模拟退款，只允许 `PAID + PAID` 且所有明细 `UNUSED` 的订单退款，成功后回补 `quota_sold`、明细变 `REFUNDED`、订单和支付状态变 `REFUNDED`。部分退款、真实支付回调和退款审计日志继续单独建模。

### 报表先做后台运营汇总

原因：前端管理台需要先有稳定的首页运营概览，但报表导出、分组图表和真实财务对账都会引入更多口径争议。本阶段先做 `GET /api/admin/reports/summary`，只按订单创建日期过滤，返回订单数、票数流转和当前净收款。SQL 将订单金额聚合与明细票数聚合分开，避免 join 后放大金额；后续再单独建模导出、产品维度和真实支付对账。

### 支付回调先做模拟验签边界

原因：游客主动模拟支付已经覆盖 CSRF、游客 session 和 `Idempotency-Key`，但真实支付平台回调不是浏览器请求，不能依赖 Cookie 或 CSRF。第二阶段先做 `POST /api/payments/mock/callback`，用 HMAC-SHA256、时间戳窗口和 `eventId` 幂等固定回调安全模型，同时复用已有库存条件更新、支付记录、出票和订单状态机。真实支付渠道 SDK、退款通知、IP 白名单和对账文件继续单独建模。

### 管理员认证沿用 Cookie 会话并增加独立限速

原因：管理员密码登录比游客手机号入口更敏感，不能复用旧 Node 的 Bearer token/localStorage，也不能和游客限速 key 混在一起。管理员登录现在使用 `admin_user`、PBKDF2 带盐口令 hash、HTTP-only session Cookie、session-bound CSRF 和独立的 `client_host + hash(username)` 失败限速；账号不存在、密码错误和账号禁用统一返回 `ADMIN_LOGIN_FAILED`。游客 session 访问管理员接口返回 `ADMIN_FORBIDDEN`，管理员退出不会误清理游客会话。

### 禁用管理员既有 session 立即失效

原因：管理员登录时校验 `status = ENABLED` 只能挡住新的登录，不能覆盖账号登录后被禁用的情况。现在后台 session 校验会读取管理员当前状态；如果已不是 `ENABLED`，后端撤销当前服务端 session，并返回统一 `ADMIN_AUTH_REQUIRED`，避免禁用账号继续访问后台，也避免通过响应区分账号状态。

### 报表导出先做订单级 CSV

原因：运营管理台在有汇总卡片后，下一步最常见需求是下载订单明细做筛选和留档。先做 `GET /api/admin/reports/orders.csv`，复用报表日期过滤和管理员只读权限，成功响应直接返回 CSV 文件，错误仍走统一失败壳。CSV 只导出订单级安全字段，并对公式开头的单元格做注入防护；XLSX、异步大文件导出、产品分组图表和真实财务对账继续单独建模。

### 订单 XLSX 导出复用 CSV 字段边界

原因：运营人员常用 Excel 打开导出文件，CSV 已有字段、权限、脱敏和公式注入边界，可以直接复用到同步 XLSX 下载。先做 `GET /api/admin/reports/orders.xlsx`，仍按订单创建日期过滤，只返回订单级安全字段，并用标准库生成最小 XLSX 包；单元格写成字符串，不生成公式节点，避免为了一个导出端点增加运行时依赖。异步大文件导出、审计 XLSX 和真实财务对账继续单独建模。

### 分组图表先做产品维度报表

原因：管理台图表最先需要回答“哪些票品卖得好、核销多、退款多”，相比时间序列和真实财务对账，产品维度聚合更贴近已有订单明细数据，风险也更可控。先做 `GET /api/admin/reports/product-breakdown`，按订单创建日期过滤，返回产品/票种分组的订单数、票数、核销量、退款量和当前净收款；订单数使用去重订单，金额按有效明细 `final_price` 聚合，避免 join 后放大订单金额。时间序列趋势、真实支付渠道对账和财务结算口径继续单独建模。

### 时间序列先做日报趋势

原因：产品维度报表回答“卖什么”，日报趋势回答“什么时候变化”，两者组合能支撑管理台第一版图表。先做 `GET /api/admin/reports/daily-trend`，按订单创建日期聚合订单数、票数、核销量、退款量和当前净收款；SQL 将订单金额聚合与明细票数聚合分开，避免 join 后放大金额。本切片不补零，月度趋势后续单独建模，小时粒度和真实财务对账不在本切片。

### 长周期趋势补月度聚合

原因：日报趋势适合短周期看波动，但管理台做月度复盘或跨季度查看时需要更粗的时间粒度。新增 `GET /api/admin/reports/monthly-trend`，继续按订单创建日期过滤，返回 `YYYY-MM` 月份、订单数、票数、核销量、退款量和当前净收款；SQL 仍将订单金额聚合与明细票数聚合分开，避免 join 后放大金额。本切片不补零、不做小时粒度，也不进入真实财务对账。

### 小时趋势复用日报趋势口径

原因：日报和月报已经能看大周期，但运营排查当天入园、支付、退款波峰时需要小时粒度。新增 `GET /api/admin/reports/hourly-trend`，继续按订单创建日期过滤，返回 `YYYY-MM-DDTHH:00:00` 小时、订单数、票数、核销量、退款量和当前净收款；SQL 仍将订单金额聚合与明细票数聚合分开，避免 join 后放大金额。本切片只返回有订单活动的小时，不补零、不做小时趋势导出，也不进入真实财务对账或前端页面实现。

### 趋势补零使用显式 includeEmpty

原因：管理台图表需要连续时间轴，但直接改变日报、小时和月报默认响应会影响已接入页面和测试。新增可选 `includeEmpty=true`，只在前端明确要求时由 service 层按 `dateFrom/dateTo` 补全连续日期、小时或月份，repository 仍只查真实聚合结果。补零请求必须提供日期边界，并限制日报 366 天、小时 31 天、月度 60 个月，避免无边界大响应；趋势导出和真实财务对账继续单独建模。

### 部分退款先按未使用票项做模拟退款

原因：后台已经有整单模拟退款，但运营常见场景是同一订单只退部分票项。当前数据库中 `ticket_order.payment_status` 支持 `PARTIAL_REFUND`，但 `payment_record.payment_status` 不支持该状态，因此本切片只在订单层记录部分退款状态，支付流水继续保持 `SUCCESS`；当所有票项都退款完成时，再把支付流水标记为 `REFUNDED`。这样既避免违反数据库约束，也把后续接真实支付渠道、退款通知和退款审计日志的边界留清楚。

### 退款审计日志写入退款事务

原因：退款会同时改变订单金额、票项状态、库存售出量和支付状态，后续运营复盘不能只依赖请求日志或前端展示。第二阶段先新增 `refund_audit_log`，由整单退款和部分退款的后端事务写入操作人、原因、退款金额、票项号和 request id；查询接口只按订单维度提供管理员只读 GET，不要求 CSRF，但必须有管理员 session。真实渠道退款流水号、退款通知和独立审计检索页继续单独建模。

### 退款审计先补全局检索

原因：订单详情维度的退款日志适合查看单笔订单，但运营复盘和异常退款排查需要跨订单检索。第二阶段先做 `GET /api/admin/refund-logs`，按退款类型、订单号、操作人和审计日期筛选，返回分页 DTO；它仍然是管理员只读 GET，不要求 CSRF，但必须校验管理员 session。审计导出、真实渠道退款流水号、退款通知和真实财务对账继续单独建模。

### 退款审计导出先做 CSV

原因：全局退款审计检索已经能支撑后台页面查询，但运营留档和异常退款排查还需要把同一批审计记录下载到表格工具中复核。先做 `GET /api/admin/refund-logs.csv`，复用退款类型、订单号、操作人和日期筛选，仍是管理员只读 GET 且不要求 CSRF；成功响应为 CSV 文件，并对所有单元格做公式注入防护。XLSX、异步导出、真实渠道退款流水号、退款通知和真实财务对账继续单独建模。

### 核销先补操作审计日志

原因：单张票码核销已经会改变票项状态、订单完成状态和时段核销量，现场运营排查时需要知道“谁在什么时候核销了哪张票”。第二阶段先新增 `check_in_audit_log`，由核销成功事务写入订单号、票项号、票码、动作、操作人展示字段和 request id，并提供 `GET /api/admin/check-ins/{ticket_code}/logs` 管理员只读查询。批量核销、全局核销日志检索和导出继续单独建模。

### 核销审计先补全局检索

原因：单票码核销日志适合订单详情里的局部追踪，但后台审计页还需要跨订单查“某天谁核销了哪些票”“某个管理员做了哪些核销”。第二阶段先做 `GET /api/admin/check-in-logs`，按票码、订单号、操作人和审计日期筛选，返回分页 DTO；它仍然是管理员只读 GET，不要求 CSRF，但必须校验管理员 session。核销日志导出和批量核销已单独建模，批量撤销已由后续切片单独建模。

### 核销审计导出先做 CSV

原因：全局核销审计检索已经能支撑后台页面查询，但运营留档和异常核销复盘还需要把同一批审计记录下载到表格工具中核对。先做 `GET /api/admin/check-in-logs.csv`，复用票码、订单号、操作人和日期筛选，仍是管理员只读 GET 且不要求 CSRF；成功响应为 CSV 文件，并对所有单元格做公式注入防护。批量核销已单独建模，批量撤销已由后续切片单独建模；XLSX 和异步导出继续单独建模。

### 批量核销复用单张核销状态机

原因：现场运营连续扫码时需要一次看到多张票的处理结果，但批量入口不能绕过单张核销已经固定的权限、CSRF、库存核销量和审计边界。先做 `POST /api/admin/check-ins/batch`，请求体只接受去重后的 `ticketCodes`，每张票独立复用现有单张核销事务；已核销、状态不可核销或不存在的票码作为逐票业务失败返回，不影响同批其他票码成功。未知系统异常仍走统一失败壳，不伪装成业务失败。批量撤销和核销失败尝试审计已由后续切片单独建模，扫码设备接入和异步导入继续单独建模。

### 核销失败尝试单独建表

原因：成功核销和撤销核销已经进入 `check_in_audit_log`，但业务失败尝试也有安全价值，例如排查误扫、重复扫码和异常票码尝试。第二阶段先新增 `check_in_failure_audit_log`，只记录通过管理员 session 与 CSRF 后的核销业务失败码：`TICKET_NOT_FOUND`、`TICKET_ALREADY_USED`、`TICKET_NOT_CHECKABLE`；匿名、游客、CSRF 失败和系统异常不写入该表。管理员通过 `GET /api/admin/check-in-failure-logs` 做只读检索，DTO 不暴露内部 id 或认证材料；已有运行库需先跑 `database/migrations/2026-07-01-add-check-in-failure-audit-log.sql` 幂等补表，避免旧 schema 部署后失败核销变成 500；撤销失败尝试已由后续切片单独建模，自动风控、告警和导出继续单独设计。

### 撤销失败尝试复用失败审计表

原因：撤销核销失败和核销失败同属“管理员通过权限与 CSRF 后的业务失败尝试”，查询页面也需要放在同一类安全审计里。第二阶段不另建撤销失败表，而是把 `check_in_failure_audit_log.action` 扩展为 `CHECK_IN` / `UNDO_CHECK_IN`，失败码扩展到 `TICKET_NOT_CHECKED_IN` 和 `TICKET_UNDO_NOT_ALLOWED`；单张和批量撤销的逐票业务失败写入该表，系统异常仍不写。已有运行库需跑 `database/migrations/2026-07-01-extend-check-in-failure-audit-log-for-undo.sql` 扩展约束，避免后端能写 `UNDO_CHECK_IN` 但数据库拒绝。

### 失败尝试审计导出先做 CSV

原因：失败尝试审计已经覆盖核销和撤销核销的业务失败检索，运营排查和安全复盘下一步最需要的是把同一批记录下载留档。先做 `GET /api/admin/check-in-failure-logs.csv`，复用 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom` 和 `dateTo` 筛选；文件仍是管理员只读 GET，不要求 CSRF，但必须校验管理员 session。CSV 只导出票码、动作、失败码、失败信息、操作人展示字段、request id 和创建时间，并对所有单元格做公式注入防护。XLSX、异步大文件导出、自动风控和告警继续单独建模。

### 失败尝试审计 XLSX 复用 CSV 字段边界

原因：CSV 已经固定了失败审计导出的安全字段和筛选语义，XLSX 的价值是让运营和安全复盘可以直接在 Excel 中留档、筛选和排序，而不是扩大审计数据面。`GET /api/admin/check-in-failure-logs.xlsx` 复用 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom` 和 `dateTo` 筛选，文件仍是管理员只读 GET，不要求 CSRF，但必须校验管理员 session。XLSX 只导出票码、动作、失败码、失败信息、操作人展示字段、request id 和创建时间；所有单元格写成 inline string，不生成公式节点，并清理 XML 1.0 非法控制字符。异步大文件导出、自动风控和告警继续单独建模。

### 撤销核销只恢复已核销票码并写审计

原因：撤销核销会把现场操作从 `USED` 回退到 `UNUSED`，同时减少时段 `quota_checked_in`，还可能把已完成订单恢复为 `PAID`，风险边界不同于普通核销和批量核销。先做 `POST /api/admin/check-ins/{ticket_code}/undo`，只允许管理员带 session-bound CSRF 撤销 `PAID/COMPLETED + PAID/PARTIAL_REFUND + USED` 的票码；SQL 层锁定票明细和订单，使用条件更新保证 `quota_checked_in` 不会减成负数，并在同一事务写入 `UNDO_CHECK_IN` 审计日志。批量撤销、撤销失败尝试审计和撤销原因审计已由后续切片单独建模，审批流继续单独设计。

### 批量撤销复用单张撤销状态机

原因：现场运营误扫通常会一次发现多张票，但批量入口不能绕过单张撤销已经固定的权限、CSRF、库存核销量回退和 `UNDO_CHECK_IN` 审计边界。先做 `POST /api/admin/check-ins/batch/undo`，请求体只接受去重后的 `ticketCodes`，每张票独立复用现有单张撤销事务；未核销、不允许撤销或不存在的票码作为逐票业务失败返回，不影响同批其他票码成功。未知系统异常仍走统一失败壳，不伪装成业务失败。撤销失败尝试审计和撤销原因审计已由后续切片单独建模，审批流、扫码设备接入和异步导入继续单独设计。

### 撤销核销原因只进入成功撤销审计

原因：运营复盘需要知道“为什么撤销”，但这一片不应该扩大成审批流或风控系统。单张撤销 `POST /api/admin/check-ins/{ticket_code}/undo` 可接受空请求体，或可选 `{ "reason": "..." }`；批量撤销 `POST /api/admin/check-ins/batch/undo` 可接受同批共享的可选 `reason`。原因会 trim，限制为 1-100 字，空白、超长和额外字段返回 `422`，并且不会产生撤销副作用。成功撤销时原因写入 `check_in_audit_log.reason`，普通核销保持 `NULL`，业务失败尝试仍只进入 `check_in_failure_audit_log`，不记录原因。核销审计日志详情、检索、CSV 和 XLSX 导出都返回该字段，并继续做公式注入防护和 XML 控制字符清洗。强制填写原因、按原因筛选、审批流和失败尝试原因留痕继续单独设计。

### 核销审计 XLSX 复用 CSV 字段边界

原因：全局核销审计 CSV 已能留档，但后台人员更常用 Excel 继续筛选和排查异常核销。先做 `GET /api/admin/check-in-logs.xlsx`，复用票码、订单号、操作人和日期筛选，字段与 CSV 完全一致；文件仍是管理员只读 GET，不要求 CSRF。XLSX 用标准库生成最小 OOXML 包，单元格写成字符串、不生成公式节点，并清理 XML 1.0 非法控制字符。审计异步导出和对象存储继续单独建模。

### 退款审计 XLSX 复用 CSV 字段边界

原因：全局退款审计 CSV 已能留档，但异常退款排查经常需要在 Excel 中筛选退款类型、退款票项和操作人。先做 `GET /api/admin/refund-logs.xlsx`，复用退款类型、订单号、操作人和日期筛选，字段与 CSV 完全一致；文件仍是管理员只读 GET，不要求 CSRF。XLSX 用标准库生成最小 OOXML 包，单元格写成字符串、不生成公式节点，并清理 XML 1.0 非法控制字符。审计异步导出、真实渠道退款流水号、退款通知和真实财务对账继续单独建模。

### 趋势报表导出先做 CSV

原因：日报、小时和月度趋势已经有 JSON 查询与 `includeEmpty` 补零，后台页面下一步最需要的是把同一口径的数据下载留档。先做 `GET /api/admin/reports/daily-trend.csv`、`hourly-trend.csv` 和 `monthly-trend.csv`，复用对应趋势查询、日期范围和补零限制；文件仍是管理员只读 GET，不要求 CSRF，并对所有 CSV 单元格做公式注入防护。趋势 XLSX、异步大文件导出和真实财务对账继续单独建模。

### 趋势 XLSX 复用 CSV 字段边界

原因：趋势 CSV 已经固定了日报、小时和月度导出的字段、权限和补零语义，XLSX 的价值是让运营人员直接用 Excel 留档和筛选，而不是扩大报表数据面。新增 `GET /api/admin/reports/daily-trend.xlsx`、`hourly-trend.xlsx` 和 `monthly-trend.xlsx`，字段与 CSV 完全一致；文件仍是管理员只读 GET，不要求 CSRF。XLSX 用标准库生成最小 OOXML 包，单元格写成字符串、不生成公式节点，并复用 XML 1.0 非法控制字符清洗。异步大文件导出和真实财务对账继续单独建模。

### 支付对账先做内部汇总

原因：当前系统已有订单净收款、模拟支付流水和退款审计三套事实源，但还没有一个后台接口回答“订单账和支付/退款账是否一致”。先做 `GET /api/admin/reports/payment-reconciliation`，按订单创建日期比较订单净收款、已捕获支付金额和退款审计金额，返回差异与是否对平；接口仍是管理员只读 GET，不要求 CSRF，且不暴露支付流水号、渠道交易号或内部 id。真实支付渠道结算文件、手续费、退款通知和渠道流水号继续单独建模。

### 支付对账汇总导出先做 CSV

原因：支付对账汇总 JSON 已经能给管理台展示一行内部对账结果，但运营复盘通常还需要下载文件留档。先做 `GET /api/admin/reports/payment-reconciliation.csv`，复用同一日期过滤、订单净收款、已捕获支付和退款审计金额口径；文件仍是管理员只读 GET，不要求 CSRF，并对所有 CSV 单元格做公式注入防护，不暴露支付流水号、渠道交易号或审计明细。XLSX、异步大文件导出、真实支付渠道结算文件、手续费和退款通知继续单独建模。

### 支付对账汇总 XLSX 复用 CSV 字段边界

原因：支付对账汇总 CSV 已经固定了字段、权限、日期过滤和敏感字段边界，XLSX 的价值是让运营人员直接用 Excel 留档和汇报，而不是扩大财务数据面。新增 `GET /api/admin/reports/payment-reconciliation.xlsx`，字段与 CSV 完全一致；文件仍是管理员只读 GET，不要求 CSRF。XLSX 用标准库生成最小 OOXML 包，单元格写成 inline string、不生成公式节点，并复用 XML 1.0 非法控制字符清洗。异步大文件导出、真实支付渠道结算文件、手续费和退款通知继续单独建模。

### 产品维度报表先补 CSV 留档

原因：产品维度 JSON 已经固定了按产品和票种分组的订单数、票数、核销量、退款量和净收款口径，运营复盘时也需要下载同一口径做留档和二次筛选。先做 `GET /api/admin/reports/product-breakdown.csv`，复用同一日期过滤和聚合查询；文件仍是管理员只读 GET，不要求 CSRF，并对所有 CSV 单元格做公式注入防护。XLSX、异步大文件导出和真实财务对账继续单独建模。

### 产品维度报表补齐 XLSX 下载

原因：前端管理台已经有产品维度 JSON/CSV 口径，运营人员更常用 XLSX 做筛选、留档和转交。先做 `GET /api/admin/reports/product-breakdown.xlsx`，复用产品维度同一日期过滤、管理员权限和产品/票种聚合 DTO，不新增统计口径；XLSX 单元格统一写成 inline string，不生成公式节点，并清理 XML 1.0 非法控制字符。异步大文件导出和真实财务对账继续单独设计。

### 异步产品维度报表 worker 补齐 CSV

原因：同步产品维度 CSV 已经固定产品/票种聚合字段和表格安全边界，异步导出任务也已经允许 `PRODUCT_BREAKDOWN` 的日期 filters。先让内部 worker 支持 `PRODUCT_BREAKDOWN + CSV`，复用同步产品维度 CSV 口径，不重新设计统计字段；文件名和 `storage_key` 继续由后端派生，成功后标记 `SUCCEEDED`。产品维度 XLSX worker 已由后续切片补齐，常驻队列、剩余报表异步导出和生产对象存储继续单独建模。

### 异步产品维度报表 worker 补齐 XLSX

原因：产品维度异步 CSV 已经证明任务流、受控存储和日期 filters 传递路径可复用，XLSX 的价值是让运营人员在大文件任务流里拿到与同步 XLSX 相同的 Excel 友好文件。先让内部 worker 支持 `PRODUCT_BREAKDOWN + XLSX`，复用同步产品维度 XLSX 的聚合字段、inline string、无公式节点和 XML 1.0 非法控制字符清洗；文件名和 `storage_key` 仍由后端派生，暂未支持的趋势任务继续失败落库。常驻队列、趋势报表异步导出、生产对象存储、重试和清理继续单独建模。

### 异步日报趋势 worker 补齐 CSV

原因：产品维度报表 CSV/XLSX 已经接入异步任务，趋势图下一步最常被下载留档的是日报 CSV。先让内部 worker 支持 `DAILY_TREND + CSV`，复用同步日报趋势 CSV 的聚合字段、`includeEmpty` 补零范围校验、日期校验和公式注入防护；文件名和 `storage_key` 仍由后端派生。日报趋势 XLSX、小时/月度趋势异步导出、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步日报趋势 worker 补齐 XLSX

原因：日报趋势 CSV 已经跑通异步任务链路，前端同一导出入口也需要 Excel 友好的日报趋势 XLSX。先让内部 worker 支持 `DAILY_TREND + XLSX`，复用同步日报趋势 XLSX 的聚合字段、`includeEmpty` 补零范围校验、inline string、无公式节点和 XML 控制字符清洗；文件名和 `storage_key` 仍由后端派生。小时/月度趋势异步导出、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步小时趋势 worker 补齐 CSV

原因：日报趋势 CSV/XLSX 已经接入异步任务，小时趋势用于排查当天入园、支付、退款波峰，CSV 留档价值高且复用同步导出口径成本低。先让内部 worker 支持 `HOURLY_TREND + CSV`，复用同步小时趋势 CSV 的聚合字段、`includeEmpty` 31 天补零范围校验、日期校验和公式注入防护；文件名和 `storage_key` 仍由后端派生。小时趋势 XLSX、月度趋势异步导出、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步小时趋势 worker 补齐 XLSX

原因：小时趋势 CSV 已经跑通异步任务链路，运营人员在小时粒度复盘时也需要 Excel 友好的 XLSX 文件。先让内部 worker 支持 `HOURLY_TREND + XLSX`，复用同步小时趋势 XLSX 的聚合字段、`includeEmpty` 31 天补零范围校验、inline string、无公式节点和 XML 控制字符清洗；文件名和 `storage_key` 仍由后端派生。月度趋势异步导出、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步月度趋势 worker 补齐 CSV

原因：日报和小时趋势 CSV/XLSX 已经接入异步任务，月度趋势用于长周期运营复盘，CSV 是最小且最容易联通前端任务流的格式。先让内部 worker 支持 `MONTHLY_TREND + CSV`，复用同步月度趋势 CSV 的聚合字段、`includeEmpty` 60 个月补零范围校验、日期校验和公式注入防护；文件名和 `storage_key` 仍由后端派生。月度趋势 XLSX、常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步月度趋势 worker 补齐 XLSX

原因：月度趋势 CSV 已经接入异步任务，后台运营长周期复盘也需要 Excel 友好的 XLSX 文件。先让内部 worker 支持 `MONTHLY_TREND + XLSX`，复用同步月度趋势 XLSX 的聚合字段、`includeEmpty` 60 个月补零范围校验、inline string、无公式节点和 XML 控制字符清洗；文件名和 `storage_key` 仍由后端派生。常驻队列、生产对象存储、重试和清理继续拆成后续切片。

### 异步导出失败任务手动重试

原因：所有当前异步导出类型的 CSV/XLSX worker 已经补齐，前端任务列表需要一个低成本恢复失败任务的操作。先实现管理员 `POST /api/admin/export-jobs/{job_id}/retry`，只允许 `FAILED -> PENDING`，清空运行时间、文件名、错误信息和内部 `storage_key` 后交给现有 worker 再处理；非失败状态返回冲突错误。自动重试已由后续切片补齐，常驻队列、生产对象存储和清理继续拆成后续切片。

### 异步导出失败任务自动重试

原因：worker 已经覆盖所有当前异步导出类型，但偶发文件写入或运行时异常如果直接落为失败，会让管理员重复做手动恢复。先给 `admin_export_job` 增加内部 `retry_count/max_retries`，只对未预期异常导致的 `ADMIN_EXPORT_JOB_WORKER_FAILED` 自动重试一次；业务/校验失败、unsupported 任务和手动中断不自动重试，避免永久失败任务无限循环。固定延迟领取已由后续切片补齐，指数退避、告警、生产对象存储和外部队列继续单独设计。

### 异步导出自动重试延迟领取

原因：自动重试第一次失败会把任务回到 `PENDING`，循环 worker 可能立刻再次领取同一条临时故障任务，形成紧密重试循环。先给任务表补内部 `next_attempt_at`，可重试失败只在 60 秒后再次允许领取；worker 领取 SQL 只选择未设置延迟或延迟已到期的 `PENDING` 任务，成功、最终失败和管理员手动 retry 都清空延迟。完整指数退避、可配置延迟、告警和外部队列继续单独设计。

### 异步导出 RUNNING 超时回收

原因：worker 进程如果在任务处于 `RUNNING` 时崩溃，不会走异常处理，也不会触发自动重试，任务会长期挂在运行中。先给数据库队列补固定 30 分钟超时回收：worker 每轮领取前扫描超时 `RUNNING`，未耗尽自动重试额度则回到 `PENDING`，耗尽则落为 `FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT`；回收 SQL 通过 `status + started_at` 索引和参数绑定执行。真实 worker 心跳、分布式租约、告警和外部队列可见性超时继续单独设计。

### 异步导出本地孤儿文件补偿清理

原因：worker 写文件和标记任务成功不是同一个强事务。文件已经写出但成功落库返回 `None` 或抛异常时，如果不补偿删除，导出目录会留下未被任务元数据引用、清理脚本也无法发现的孤儿文件。现在只对刚由后端派生并写出的 `storage_key` 做尽力删除，删除失败不掩盖原始落库失败；历史孤儿文件扫描和对象存储生命周期另行设计。

### 异步导出本地文件清理

原因：当前异步导出已经能持续生成本地文件，如果不清理会在联调和部署环境积累磁盘占用。先实现 `scripts/cleanup-admin-export-files.py`，按过期时间和批量上限处理 `SUCCEEDED` 任务，删除受控存储目录内的文件并清空文件元数据；缺失文件也清理元数据，异常路径只跳过不越权删除。生产对象存储生命周期、自动调度和常驻队列继续拆成后续切片。

### 异步导出 worker 循环入口

原因：单次 worker 已经能处理一条 pending 任务，但本地联调和部署环境需要一个能持续消费任务的后端入口。先实现 `scripts/run-admin-export-worker.py`，复用现有 worker service 循环处理任务，并提供最大处理数、空闲退出和空闲 sleep 参数，输出固定 JSON 汇总且错误脱敏。进程守护、自动重启和外部队列服务继续拆成后续切片。

### 异步导出 worker 进程守护模板

原因：循环 worker 已经能持续消费任务，但部署时仍需要交给系统进程管理器托管，避免终端退出、进程崩溃或机器重启后导出任务无人消费。先提供 `deploy/systemd/scenic-ticket-admin-export-worker.service` 作为 Linux systemd 参考模板，固定非 root 用户、环境文件、导出写目录、自动重启、SIGINT 停止信号和基础加固项；生产对象存储、外部队列服务和多 worker 容量规划继续拆成后续切片。

### 异步导出清理定时器模板

原因：清理脚本已经能按保留天数删除过期成功导出文件并清空元数据，但部署环境如果完全依赖人工执行，仍会积累本地导出文件。先提供 `deploy/systemd/scenic-ticket-admin-export-cleanup.service` 和 `.timer`，每日以 oneshot 方式运行清理脚本，并固定非 root 用户、环境文件、受控导出目录、随机延迟、错过补跑和基础加固项；生产对象存储生命周期、跨节点清理锁和平台级调度继续拆成后续切片。

### 异步导出存储 provider 边界

原因：当前导出文件仍保存在本地受控目录，但后续会接生产对象存储。如果现在允许 `ADMIN_EXPORT_STORAGE_PROVIDER=s3` 这类值静默通过，会让部署环境误以为云存储已经可用。先新增 `ADMIN_EXPORT_STORAGE_PROVIDER=local` 配置边界，所有脚本和 API 统一走 storage factory，未知 provider 在配置校验阶段拒绝启动；真实 S3/OSS/COS provider、凭证和生命周期继续拆成后续切片。

### 异步导出队列 provider 边界

原因：当前异步导出用数据库表和行锁承担任务队列职责，已经能支撑单机和小规模部署。如果现在允许 `ADMIN_EXPORT_QUEUE_PROVIDER=redis` 或 `celery` 静默通过，会让部署环境误以为外部队列已经可用。先新增 `ADMIN_EXPORT_QUEUE_PROVIDER=database` 配置边界，未知 provider 在配置校验阶段拒绝启动；真实 Redis/Celery/RQ/消息队列、容量规划和监控继续拆成后续切片。

### 异步导出失败告警 provider 边界

原因：异步导出已经有自动重试和最终失败状态，但还没有真实邮件、Slack 或 Webhook 告警。如果允许 `ADMIN_EXPORT_ALERT_PROVIDER=webhook` 这类值静默通过，部署环境会误以为失败任务已能主动通知。先新增 `ADMIN_EXPORT_ALERT_PROVIDER=disabled` 配置边界，未知 provider 在配置校验阶段拒绝启动；真实告警发送、去重、脱敏和告警审计继续拆成后续切片。

### 异步导出最终失败告警事件记录

原因：失败告警 provider 已经显式关闭真实通知，但 worker 最终失败后仍需要一个内部可追溯事实，为后续告警查询、真实通知或运维复盘留接口。先新增 `admin_export_job_alert_event` 表，并在 `mark_export_job_failed` 返回最终 `FAILED` 时尽力写入 `WORKER_FINAL_FAILURE` 事件；retryable 第一次失败回到 `PENDING` 不记录，事件不包含 `filters`、`storage_key`、本机路径、SQL 或原始异常。真实 email/Slack/Webhook、去重/静默窗口继续拆成后续切片。

### 异步导出任务文件格式筛选

原因：异步导出任务列表已经能按导出类型和状态收窄，但前端任务中心还需要直接区分 CSV 与 XLSX 任务，且告警事件已经具备同名 `fileFormat` 筛选。继续增强管理员 `GET /api/admin/export-jobs`，新增 `fileFormat=CSV/XLSX` 查询参数，非法格式返回 `ADMIN_EXPORT_JOB_FILE_FORMAT_INVALID`，仓储只追加参数化 `file_format = %s` 条件。任务创建、worker、下载端点和前端页面继续保持不变。

### 异步导出 RUNNING 超时最终失败告警事件记录

原因：RUNNING 超时回收会绕过 `mark_export_job_failed`，直接由批量 SQL 把耗尽重试额度的任务落为 `FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT`。为了让所有 worker 最终失败都有同样的内部事实，仓储回收接口改为返回回收数量和最终失败任务记录，服务层继续对外返回数量，并只为最终 `FAILED` 的超时任务写入 `WORKER_FINAL_FAILURE` 事件；可重试回 `PENDING` 的超时任务不记录。真实通知、去重/静默窗口、worker 心跳和分布式租约继续单独设计。

### 异步导出告警事件只读查询 API

原因：内部告警事件已经能记录 worker 最终失败和 RUNNING 超时最终失败，但没有后台只读入口时，前端后续页面和运维复盘都只能直接查库。先新增管理员 `GET /api/admin/export-job-alert-events`，支持 `jobId/errorCode/page/pageSize`，只返回告警事实字段，不回连任务 `filters`、`storage_key`、路径、SQL 或异常。真实 email/Slack/Webhook、告警确认/关闭、去重/静默窗口和前端页面继续单独设计。

### 异步导出告警事件筛选增强

原因：告警事件已经支持查询和确认，前端管理台下一步需要直接拉取未处理告警并按时间范围排查。继续增强 `GET /api/admin/export-job-alert-events`，新增 `acknowledged/dateFrom/dateTo` 筛选；接口仍是管理员只读 GET，不要求 CSRF，日期按 `created_at` 包含 `dateTo` 当天，非法确认状态、非法日期和日期倒挂统一返回 `ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。真实外部通知、关闭筛选/汇总、去重/静默窗口和前端页面继续单独设计。

### 异步导出告警事件汇总 API

原因：告警事件列表适合排查单条失败，但前端管理台还需要低成本展示当前未处理规模和主要失败类型。先新增管理员 `GET /api/admin/export-job-alert-events/summary`，只支持 `dateFrom/dateTo` 时间范围，返回总数、已确认、未确认和 `byErrorCode` 聚合；接口仍是只读 GET，不要求 CSRF，DTO 不返回 `filters`、`storage_key`、路径、SQL、异常、session 或内部管理员 id。真实外部通知、关闭筛选/汇总、去重/静默窗口、趋势图和前端页面继续单独设计。

### 异步导出告警事件确认 API

原因：告警事件已经能被管理员查询，但没有处理标记时，运营人员无法区分哪些最终失败已经人工排查。先给 `admin_export_job_alert_event` 增加 nullable 确认字段，并新增管理员 `POST /api/admin/export-job-alert-events/{event_id}/acknowledge`；接口必须携带 CSRF，备注限制 200 字符，确认采用第一次确认获胜，重复确认不覆盖原处理人或备注。真实 email/Slack/Webhook、关闭筛选/汇总、去重/静默窗口和前端页面继续单独设计。

### 异步导出告警事件批量确认 API

原因：单条确认已经能表达“有人处理过”，但前端管理台多选处理告警时逐条请求会增加交互复杂度。先新增管理员 `POST /api/admin/export-job-alert-events/batch-acknowledge`，要求 CSRF，请求体只接受 1-100 个不重复正整数 `eventIds` 和可选 200 字符备注；服务层逐项复用单条确认逻辑，已确认事件返回成功但不覆盖第一次确认记录，不存在事件作为逐项失败返回。真实 email/Slack/Webhook、跨任务聚合、可配置静默窗口和前端页面继续单独设计。

### 异步导出告警事件关闭和重开 API

原因：确认字段表示“有人处理过”，但前端管理台还需要把不再活跃展示的内部告警关闭，并允许误关闭后重开。先给 `admin_export_job_alert_event` 增加 nullable 关闭字段，新增管理员 `POST /api/admin/export-job-alert-events/{event_id}/close` 和 `/reopen`；两个接口都必须携带 CSRF，关闭备注限制 200 字符，关闭采用第一次关闭获胜，重开只清空关闭字段且不改变确认记录。真实 email/Slack/Webhook、关闭筛选/汇总、去重/静默窗口和前端页面继续单独设计。

### 异步导出告警事件批量关闭 API

原因：单条关闭已经能把不再活跃展示的告警移出开放队列，但前端管理台多选关闭时逐条请求会增加交互复杂度。先新增管理员 `POST /api/admin/export-job-alert-events/batch-close`，要求 CSRF，请求体只接受 1-100 个不重复正整数 `eventIds` 和可选 200 字符备注；服务层逐项复用单条关闭逻辑，已关闭事件返回成功但不覆盖第一次关闭记录，不存在事件作为逐项失败返回。真实 email/Slack/Webhook、跨任务聚合、可配置静默窗口和前端页面继续单独设计。

### 异步导出告警事件关闭筛选和汇总增强

原因：关闭/重开已经提供告警生命周期动作，但前端管理台还需要直接拉取未关闭告警队列，并在汇总卡片里区分关闭和未关闭规模。继续增强 `GET /api/admin/export-job-alert-events` 和 `/summary`，新增 `closed=true/false` 查询参数，汇总响应新增 `closed/open` 顶层计数和按错误码分组计数；非法关闭状态继续返回 `ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`。真实 email/Slack/Webhook、去重/静默窗口和前端页面继续单独设计。

### 异步导出告警事件去重静默

原因：关闭筛选可以让前端拉取活跃告警，但同一任务同一错误在未关闭期间重复进入最终失败链路时，不应刷出多条等价告警。先在本地事件表做最小折叠：同一个 `job_id + error_code + alert_source` 且 `closed_at IS NULL` 时更新原事件的 `occurrence_count`、`last_seen_at` 和最新错误信息，不新增事件行；关闭后的再次失败允许创建新事件。真实 email/Slack/Webhook、跨任务合并、可配置静默窗口和前端页面继续单独设计。

### 异步导出告警事件类型和格式筛选

原因：告警事件已经支持生命周期管理和未关闭去重，前端管理台还需要按导出类型和文件格式收窄列表与汇总。继续增强 `GET /api/admin/export-job-alert-events` 和 `/summary`，新增 `exportType/fileFormat` 查询参数，复用现有导出类型和 `CSV/XLSX` 白名单，非法值统一返回 `ADMIN_EXPORT_JOB_ALERT_EVENT_FILTER_INVALID`；SQL 只追加参数化条件。真实 email/Slack/Webhook、跨任务合并、可配置静默窗口和前端页面继续单独设计。

### 异步导出告警事件删除 API

原因：告警事件已经支持关闭/重开和类型/格式筛选，但关闭后的历史事件缺少受控清理入口。先新增管理员 `DELETE /api/admin/export-job-alert-events/{event_id}`，要求 CSRF，只允许删除 `closed_at IS NOT NULL` 的已关闭事件；未关闭事件返回 `ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED`，不存在事件返回 `ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND`。批量删除、真实外部通知、跨任务聚合、可配置静默窗口和前端页面继续单独设计。

### 异步导出告警事件批量删除 API

原因：单条删除已关闭告警事件已经能清理历史记录，但前端管理台多选清理时逐条请求会增加交互复杂度。先新增管理员 `POST /api/admin/export-job-alert-events/batch-delete`，要求 CSRF，请求体只接受 1-100 个不重复正整数 `eventIds`；服务层逐项复用单条删除逻辑，只删除已关闭事件，未关闭和不存在事件作为逐项失败返回，不影响同批其他事件。真实外部通知、跨任务聚合、可配置静默窗口和前端页面继续单独设计。

### 支付 provider 边界

原因：当前游客支付和回调仍是模拟支付，虽然已经有幂等、库存事务和 HMAC 回调边界，但不能让部署环境通过 `PAYMENT_PROVIDER=wechat` 或 `alipay` 误以为真实渠道已经接通。先新增 `PAYMENT_PROVIDER=mock` 配置边界，未知 provider 在配置校验阶段拒绝启动；真实支付 SDK、渠道回调、退款通知和结算文件继续拆成后续切片。

### 退款写操作先收紧到 SUPER_ADMIN

原因：管理员模型已经有 `SUPER_ADMIN` 和 `OPERATOR`，但退款会改变订单、支付、库存和审计，是后台高风险资金状态变更。先把整单退款和部分退款限制为 `SUPER_ADMIN`，`OPERATOR` 返回统一 `ADMIN_FORBIDDEN`，并在调用退款 repository 前拒绝，避免产生订单、库存、支付或退款审计副作用。完整权限矩阵、审批流、退款通知和真实渠道退款继续单独设计。

### 核销审计补撤销原因筛选

原因：撤销核销已经把 `reason` 写进成功审计日志，但后台检索和导出只能按票码、订单号、操作人和日期过滤，排查“误核销”这类原因时还要下载后手工筛。先给 `GET /api/admin/check-in-logs`、CSV/XLSX 同步导出和 `CHECK_IN_AUDIT` 异步导出 filters 增加 `reason` 模糊筛选；SQL 继续参数绑定，异步导出公开 DTO 中 `reason` 脱敏，worker 内部使用完整 filters。强制填写原因、按原因聚合、告警和审批流继续单独设计。

### 异步支付对账 worker 先补 CSV

原因：同步支付对账 CSV/XLSX 已经固定单行汇总字段，异步任务流也已经覆盖审计、产品和趋势导出，支付对账是任务中心剩余的报表缺口。先让导出任务支持 `PAYMENT_RECONCILIATION` 类型，并让 worker 处理 `PAYMENT_RECONCILIATION + CSV`，复用同步支付对账 CSV 的日期口径、公式注入防护和文件名规则；`PAYMENT_RECONCILIATION + XLSX` 暂按 unsupported 失败落库，下一步单独补齐。真实渠道结算文件、手续费和退款通知继续单独设计。

### 异步支付对账 worker 补齐 XLSX

原因：同步支付对账 XLSX 已有安全导出口径，异步支付对账 CSV 也已接入任务中心。继续补齐 `PAYMENT_RECONCILIATION + XLSX`，复用同步 XLSX 的单行汇总字段、inline string、无公式节点和 XML 1.0 非法控制字符清洗；worker 只读取 `dateFrom/dateTo` filters，文件名和 `storage_key` 仍由后端派生。真实渠道结算文件、手续费、多 sheet 财务对账和生产对象存储继续单独设计。
