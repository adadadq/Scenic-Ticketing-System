# 前端蓝图

日期：2026-06-30

本文档是前端后续重构的真相源。imagegen 图片只提供视觉方向，具体实现以 API 契约、组件边界、响应式规则和安全边界为准。

## 项目目标

把遇龙河景区票务系统前端重构成一个可学习、可演示、可联调的 React + Vite + Ant Design 工作台：

- 游客完成登录、实名、选票、选时段、下单、模拟支付和查票。
- 游客在“我的订单”里处理待支付、已支付、已取消和错误状态。
- 管理员在后台查看报表、订单 read-model、票码核验、退款审计检索和整单退款动作。
- 所有状态变更默认走 CSRF；所有敏感数据只展示 DTO 允许的脱敏字段。
- 每个前端切片都先对齐接口契约，再 mock 验证，最后等待真实后端联调。

## 设计读法

Reading this as: 景区票务与码头运营工作台 for 游客、运营人员和学习安全工作流的学生, with a 清晰可信、工作流驱动、公共服务 SaaS visual language, leaning toward Ant Design plus custom water-pier tokens.

## 设计旋钮

- `DESIGN_VARIANCE 4/10`：页面稳、对称、好扫读，局部用码头/水线做识别。
- `MOTION_INTENSITY 2/10`：以状态反馈为主，不做炫技动效。
- `VISUAL_DENSITY 7/10`：游客侧中高密度，后台高密度，但移动端必须舒展。

## 前端栈

- Framework: React + Vite + TypeScript。
- UI: Ant Design 6。
- Icons: `@ant-design/icons`，不混用图标体系。
- Server state: TanStack Query。
- Styling: CSS 文件 + Ant Design theme token。后续可抽 CSS variables，但不新增重型 CSS 框架。
- API boundary: `src/shared/api` 是 DTO 和 endpoint wrapper 的边界；页面不直接拼 fetch。

## 页面清单

- 游客购票工作台：票种、日期、时段、数量、实名门槛、订单摘要、创建待支付订单。
- 我的订单：状态筛选、订单搜索、订单列表、详情、支付、取消、票码和契约错误态。
- 后台运营工作台：管理员登录、管理员会话、运营报表、订单运营、票码核验、整单退款、订单内退款审计日志、全局退款审计检索、CSV 导出。

## 草图资产

当前参考稿：

```text
docs/frontend/mockups/visitor-shell-booking-v4.png
docs/frontend/mockups/visitor-auth-dialog-v1.png
docs/frontend/mockups/visitor-orders-mobile-v1.png
docs/frontend/mockups/visitor-booking-workbench-v3.png
docs/frontend/mockups/admin-workbench-desktop-v3.png
docs/frontend/mockups/admin-order-detail-mutation-drawer-v1.png
docs/frontend/mockups/admin-mobile-workbench-v1.png
docs/frontend/mockups/admin-operations-workbench-v2.png
docs/frontend/mockups/mobile-booking-order-flow-v2.png
```

历史参考稿：

```text
docs/frontend/mockups/auth-realname-entry-v1.png
docs/frontend/mockups/visitor-booking-workbench-v1.png
docs/frontend/mockups/visitor-booking-workbench-v2.png
docs/frontend/mockups/my-orders-detail-v1.png
docs/frontend/mockups/my-orders-contract-states-v2.png
docs/frontend/mockups/mobile-booking-flow-v1.png
docs/frontend/mockups/admin-login-shell-v1.png
```

采用新图里的这些规则：

- 游客桌面：左导航 + 顶部状态条 + 主流程区 + 右侧 sticky 摘要；未实名是工作流门槛，不是错误页。
- 游客壳：游客端保留“游客购票 / 我的订单 / 游客服务”三项导航；游客服务只展示开放时间、交通、游玩须知、退改规则、优惠提醒和 FAQ，不混入后台能力。
- 游客购票 v4：顶部状态使用轻量 pills，页面首屏可以有淡山水/码头背景识别；右侧摘要是结算面板，必须展示游客状态、数量、金额和实名/下单主动作。
- 游客认证 v1：登录/实名不再做独立落地页；桌面使用当前游客页上的 modal，手机使用底部抽屉式 modal，必须保留登录、实名、创建订单三步解释和 CSRF / 最小字段说明。
- 游客订单移动端 v1：我的订单手机页优先展示状态胶囊、订单号搜索、刷新、订单卡片和详情抽屉；卡片只使用订单 DTO 中的票名、日期、时段、数量、金额、状态和订单时间。
- 后台桌面：使用一个后台壳承载多个业务页，不把报表、订单、审计和导出全部塞进同一屏；安全状态放在小型状态区，不做大宣传块。
- 后台桌面 v4：`#/admin` 是运营概览和入口页，保留“看报表 -> 管票种 -> 查订单 -> 做变更 -> 留证据”流程；`#/admin/tickets` 承载票种新增、改价、上下架和删除 mock 管理；`#/admin/reports` 承载报表总览、支付对账、产品和趋势；`#/admin/orders` 承载订单列表、核验、退款和订单详情抽屉；`#/admin/audit` 承载导出任务、核验审计、失败审计和退款审计。
- 后台订单详情抽屉 v1：订单详情不是普通只读面板，而是状态变更工作台；顶部必须有状态摘要，票项核验、整单退款、部分退款和退款审计必须各自保留边界说明、确认动作、成功/错误结果和请求编号位置。
- 后台移动端 v1：手机后台使用底部页面导航切换工作台、票种、报表、订单、审计；订单页使用卡片列表，报表页双列压缩指标，审计页按任务分组，避免把桌面表格压进同一屏。
- 移动端：单列、票种卡片、横向日期条、时段按钮网格、底部 sticky 摘要；订单详情用抽屉或下方分段，不把表格塞进手机。

拒绝新图里的这些内容：

- 任何无法由真实 DTO 支撑的随机数字、随机字段和假文案。
- imagegen 偶尔生成的全手机号、证件号、IP、二维码、真实账号等敏感样式。
- 固定截图比例、不可读小字、装饰性水墨图占太多首屏、卡片套卡片。
- 把后台退款、核验按钮做成无状态边界的裸按钮。

## 设计系统规则

颜色：

- 主色：`#008b84` 水绿，用于选中态、主按钮、关键链接。
- 深主色：`#006c69`，用于侧栏和小标题。
- 背景：`#f5f8fa`，容器 `#ffffff`。
- 边框：`#dce3ea`。
- 价格 / 待处理：`#fa541c` 或 Ant Warning 系列。
- 错误：Ant Error 系列，避免大面积红色背景。

形状和层级：

- 卡片、按钮、输入框统一 8px 半径。
- 主要靠边框、分隔线和留白建立层级，轻阴影只用于浮层或重要容器。
- 禁止页面 section 再套大卡片再套小卡片；重复列表项可以用 8px 卡片。

排版：

- 中文业务系统优先清晰：保留当前 `"Avenir Next", "IBM Plex Sans", "PingFang SC"` 字体栈。
- 页面标题只用于页面级；面板标题保持 16-20px。
- 长订单号、票码、请求编号必须可换行或横向滚动，不能撑破布局。

动效：

- 仅保留 hover、focus、loading、drawer/popconfirm 过渡。
- 不做滚动视差、背景漂浮、渐变光斑。

## 组件边界

已经形成的模块边界继续保留：

```text
src/app/
  VisitorAppShell.tsx
  AdminAppShell.tsx
  StatusStrip.tsx

src/features/auth/
src/features/booking/
src/features/orders/
src/features/admin/
src/features/admin-auth/
src/features/admin-orders/
src/features/admin-reports/
src/features/admin-refund-logs/
src/shared/api/
src/shared/components/
src/shared/theme/
```

后续重构规则：

- `App.tsx` 只负责页面选择和顶层事件，不放业务布局。
- 页面级组件负责组合；复杂表格、详情、状态面板下沉到 `components/`。
- API 查询、mock、状态机放在对应 feature 的 `queries.ts` / `mockData.ts`，页面不直接改 mock 数组。
- 跨页面复用的错误展示进入 `src/shared/components`。
- 新增后台子面板时优先拆成独立组件，避免 `AdminOrdersPanel.tsx` 继续变大。

## 数据和安全边界

- 游客身份、管理员身份都从后端 session 读取，前端不提交归属字段。
- 状态变更 POST 默认需要 CSRF。支付接口保留 `Idempotency-Key`，核验和整单退款不额外加幂等键，除非后端契约明确要求。
- 整单退款前端只提交 `reason`；金额、票项、库存回补和状态由后端计算。
- 后台列表只展示脱敏手机号 `buyerPhoneMasked`，不展示证件号、完整手机号、`adminUserId`、数据库审计字段、SQL、session token 或密码。
- 错误态展示稳定业务文案、错误码和请求编号，不暴露堆栈。

## 响应式规则

- `>= 1200px`：桌面工作台，左导航 + 主内容 + 右摘要或详情。
- `900px - 1199px`：中等桌面，右侧摘要下沉或变窄，表格保留横向滚动容器。
- `640px - 899px`：平板，内容堆叠，详情使用 Drawer 或下方区域。
- `< 640px`：手机，单列布局；订单和后台表格切换为列表卡；底部 sticky 操作条不遮挡内容。

必须检查：

- 不出现页面级水平溢出。
- 按钮文字不换行；必要时换短标签。
- 长票名、长订单号、长请求编号不撑破容器。
- 表格只在表格内部横向滚动。

## 页面骨架计划

入口拆分：

- 游客端和管理员端分成两套 app shell。游客端默认入口承载购票和我的订单；管理员端使用独立后台入口，不出现在游客侧导航里。
- 当前不引入 `react-router`，先使用轻量 hash 入口：`/#/visitor/booking`、`/#/visitor/orders`、`/#/visitor/service`、`/#/admin`。后续需要真实部署路径时再迁移到路由库。
- `VisitorAppShell` 只展示游客导航、服务状态和游客会话；`AdminAppShell` 只展示后台导航、服务状态、后台边界和返回游客端入口。
- 业务组件继续复用当前 `BookingWorkbench`、`OrdersWorkbench`、`AdminWorkbench`，这次只拆角色入口和布局边界，不重写接口契约。

游客购票：

- 保留当前 `BookingHeader`、`BookingStepsCard`、`TicketSelector`、`DateSlotPicker`、`OrderSummaryPanel`。
- 下一轮优先统一面板 heading、状态条、摘要块密度，并对齐 `visitor-booking-workbench-v3.png`。

我的订单：

- 保留列表 + 桌面详情 + 移动 Drawer。
- 下一轮优先统一筛选区、错误态和票码区域，让它和购票页共享状态语言。

游客服务：

- 新增只读服务页，先使用前端 mock 展示开放时间、交通到达、游玩须知、退改规则、优惠提醒和常见问题。
- 后续接入后端时优先使用 `GET /api/visitor/service-info`，页面不展示库存策略、退款计算、管理员审计字段或内部配置。

后台运营：

- 报表、订单、退款审计检索必须从一个巨型后台页逐步拆成可维护子面板。
- 下一轮优先做后台布局骨架重构：报表摘要、订单运营、审计检索形成清晰 grid；动作仍保持当前契约和 mock。

## 实施阶段

1. 蓝图和草图更新：生成 v3/v2 草图，更新文档，审查并提交。
2. 游客侧视觉整理：不改契约，只整理布局、密度、响应式和状态文案。
3. 订单侧视觉整理：统一筛选、详情、错误态和移动 Drawer。
4. 后台布局重构：拆分后台面板，降低 `AdminOrdersPanel` 复杂度。
5. 后端联调收口：打开 API mode，跑 `npm run test:e2e:real` 和根目录联调门禁。

每个阶段都要小步提交、子代理审查、测试通过后进入下一步。

## 验证清单

- `npm run test:contract`
- `npm run lint`
- `npm run build`
- `npm run test:e2e`
- 需要真实后端时：`npm run test:e2e:real`
- 视觉切片必须用浏览器或截图检查桌面、390px 手机、768px 平板边界。

## 非目标

- 不接真实支付。
- 不在前端计算退款金额、库存回补或审计操作人。
- 不新增未在 API 契约中的后台功能。
- 不引入新的 UI 库或图标库。
- 不把 imagegen 草图当作像素级规范。
