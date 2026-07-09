# 前端验收证据

日期：2026-07-02

本文件用于收口前端线程的验收范围。后端线程可以继续推进真实服务，但前端完成度以这里的证据和 `frontend` 下的验证脚本为准。

## 一键验收

```bash
npm --prefix frontend run verify
```

该命令串联：

- `npm run lint`
- `npm run test:contract`
- `npm run test:e2e`
- `npm run build`

真实后端已经启动并需要联调时，再单独运行：

```bash
npm --prefix frontend run test:e2e:real
```

## 需求到证据

| 前端目标 | 主要证据 |
| --- | --- |
| 游客完成登录、实名、选票、选时段、下单、模拟支付和查票 | `test:e2e` 覆盖游客登录、实名、创建订单、支付重试幂等、已支付票码展示 |
| 我的订单处理待支付、已支付、已取消和错误状态 | `test:e2e` 覆盖状态筛选、详情抽屉、不可支付、不可取消、订单不存在错误态 |
| 后台查看报表、订单 read-model、票码核验、退款审计和退款动作 | `test:e2e` 覆盖后台登录、订单详情、单张/批量核验、撤销核验、整单退款、部分退款、审计检索、导出任务 |
| 前后端接口不矛盾 | `test:contract` 覆盖共享 DTO、API endpoint、查询参数、文件下载 content type、CSRF 和幂等键边界 |
| 状态变更走 CSRF，支付保留 Idempotency-Key | `test:contract` 静态约束 API client；`test:e2e` 记录 CSRF header 轮换和支付幂等键复用 |
| 敏感数据只展示 DTO 允许字段 | `test:contract` 与 `test:e2e` 覆盖完整手机号、证件号、session、CSRF、密码、hash、SQL、内部 id 不出现在页面和导出 mock |
| 响应式不出现页面级横向溢出 | `test:e2e` 覆盖 390px 手机、平板、中等桌面和 1280px 桌面关键页面 |

## 游客端逐步验收清单

| 阶段 | 要确认的界面结果 | 证据来源 |
| --- | --- | --- |
| 未登录浏览 | 游客可看到票种、日期、时段和摘要；主动作提示先登录；我的订单显示登录门槛而不是空订单 | `test:e2e` 的 `loggedOutOrdersState`、`desktopAuthActionState.loginLabel` |
| 手机号登录 | 非法手机号只触发表单校验；限流错误显示错误码和请求编号；成功后会话显示临时游客 | `loginBodies`、`RATE_LIMITED`、`临时游客会话` 断言 |
| 实名登记 | 提交前必须确认实名用途；非法身份证不提交；成功后步骤进入支付订单 | `registerBodies`、`bookingStepState.afterRegisterStep` |
| 创建订单 | 前端只提交 `buyerName`、`buyerPhone` 和 `items`，不提交 visitorId；创建成功进入我的订单 | `createOrderBody` 与订单页 heading 断言 |
| 待支付订单 | 卡片显示待支付动作；详情允许继续模拟支付和取消；支付失败类错误不会反复重试 | `pageState`、`notPayablePaymentState`、`quotaPaymentState` |
| 已支付订单 | 详情显示支付成功和票码；不显示取消和支付动作 | `paidPageState`、`desktopDetailState` |
| 已取消订单 | 卡片和详情只读；不生成票码；不显示状态变更动作 | `pageState.hasCancelledStateCard`、`hidesCancelledStateActions` |
| 错误态 | 订单详情失败显示业务文案、错误码、请求编号和重试，不暴露状态变更按钮 | `orderDetailErrorState` |
| 移动端 | 390px 下表格隐藏、订单卡片显示、详情抽屉和底部动作不产生水平溢出 | `pageState.mobileCardFits`、`mobileDetailActionState` |

游客端联调真实后端时，优先按上表逐项替换 mock 证据为真实接口证据；不要一次性改完全部模式。建议顺序是：健康检查 -> 登录/实名 -> 票种/时段 -> 创建订单 -> 我的订单 -> 支付/取消。

## 管理端逐步验收清单

| 阶段 | 要确认的界面结果 | 证据来源 |
| --- | --- | --- |
| 未登录后台 | 只显示管理员登录、安全边界和锁定的工作台骨架；不展示订单、报表金额、退款审计行或核验失败审计行 | `adminLoggedOutState` |
| 管理员会话 | 后台壳与游客壳分离；侧栏只有后台工作台；顶部可返回游客端；会话显示 Mock / API 模式 | `adminShellState`、`adminReturnToVisitorState` |
| 运营流程 | 已登录后显示“看报表 -> 查订单 -> 做变更 -> 留证据”流程条；边界条说明只读视图、状态变更和审计导出 | `adminShellState.hasOperationsWorkflowStrip`、`hasOperationsBoundaryCopy` |
| 报表只读 | 报表显示统计周期、四个摘要指标、支付对账、小时/日/月趋势和产品维度；导出按钮可用；不展示完整手机号、证件号或 SQL | `adminReportState`、`adminReportTrendExportState` |
| 订单 read-model | 订单列表只展示脱敏手机号；状态、支付状态、订单号和手机号后四位筛选可收窄数据 | `adminShellState`、`adminFilterState` |
| 核验状态变更 | 单张和批量核验只提交票码；撤销核验可提交原因；成功和业务失败都展示可追溯结果 | `adminDetailState`、`adminBatchCheckInState`、`adminBatchUndoCheckInState` |
| 退款状态变更 | 整单退款和部分退款贴近状态机；退款后刷新订单状态，重复退款动作被禁用；原因只用于提交和审计展示 | `adminFullRefundState`、`adminPartialRefundState` |
| 审计和导出 | 退款审计、核验失败审计和异步导出支持筛选、错误态、CSV/XLSX 下载证据，不暴露内部管理员 id、session、CSRF 或 SQL | `adminRefundLogSearchState`、`adminCheckInFailureLogSearchState`、`adminExportJobCreateState` |
| 响应式 | 834px、768px 和 390px 下没有页面级横向溢出；订单表格在小屏切换成卡片列表；后台流程和边界条不撑破页面 | `adminIntermediateState`、`adminTabletState`、`adminMobileState` |

管理端联调真实后端时，建议按阶段逐项打开 API mode：管理员会话 -> 报表只读 -> 订单 read-model -> 单张核验 -> 批量核验/撤销 -> 退款动作 -> 审计检索 -> 导出任务。任何阶段失败时，先对照 DTO、错误码和请求编号定位契约，不要把前端 mock 字段直接改成后端临时字段。

## 当前边界

- 默认 E2E 使用 mock API，便于前端不等待后端时独立收口。
- `test:e2e:real` 依赖本机 `http://127.0.0.1:8000` 真实后端和数据库健康。
- Vite build 目前会提示大 chunk 警告；这是性能优化提醒，不影响当前前端功能验收。
- 后台默认 mock mode，可通过各 `VITE_ADMIN_*_MODE=api` 环境变量逐项切到真实接口。
