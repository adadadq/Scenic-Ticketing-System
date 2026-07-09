# 后台日报趋势报表设计

日期：2026-06-30

## 问题定义

后台已经有汇总报表、产品维度报表和订单 CSV 导出。管理台趋势图还需要按日期展示订单、票数、核销、退款和净收款走势。这个切片先提供日维度趋势数据，不进入真实财务对账或复杂 BI。

## 边界

本切片实现：

- `GET /api/admin/reports/daily-trend`
- 可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤。
- 只允许管理员 session 访问；这是只读 GET，不要求 CSRF header。
- 返回统一 `ApiSuccessDTO[list[AdminDailyTrendDTO]]`。
- 每一行按 `reportDate` 聚合。
- 返回订单数、已支付订单数、已完成订单数、已退款订单数、已取消订单数、总票数、已售票数、已核销票数、已退款票数和当前净收款。

本切片不实现：

- 小时、周、月粒度切换。
- 对没有订单活动的日期补零。
- 任意图表维度组合。
- 真实财务对账、支付渠道手续费、退款通知或结算口径。
- 前端图表样式和交互。

## API 契约

```text
GET /api/admin/reports/daily-trend?dateFrom=2026-07-01&dateTo=2026-07-31
```

成功响应：

```json
{
  "success": true,
  "data": [
    {
      "reportDate": "2026-07-01",
      "orderCount": 3,
      "paidOrderCount": 2,
      "completedOrderCount": 1,
      "refundedOrderCount": 0,
      "cancelledOrderCount": 1,
      "netPaidAmount": "384.00",
      "ticketCount": 5,
      "soldTicketCount": 3,
      "checkedInTicketCount": 1,
      "refundedTicketCount": 0
    }
  ],
  "request_id": "..."
}
```

错误响应仍使用统一失败壳：

- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`
- 游客 session：`403 ADMIN_FORBIDDEN`
- `dateFrom > dateTo`：`422 ADMIN_REPORT_DATE_RANGE_INVALID`

## 统计口径

- `reportDate`：订单创建日期。
- `orderCount`：当天创建的订单数。
- `paidOrderCount`：当天创建且当前支付状态为 `PAID` 的订单数。
- `completedOrderCount`：当天创建且当前订单状态为 `COMPLETED` 的订单数。
- `refundedOrderCount`：当天创建且当前订单状态为 `REFUNDED` 的订单数。
- `cancelledOrderCount`：当天创建且当前订单状态为 `CANCELLED` 的订单数。
- `netPaidAmount`：当天创建订单的当前 `paid_amount` 合计。
- `ticketCount`：当天创建订单的全部明细数。
- `soldTicketCount`：明细状态为 `UNUSED` 或 `USED` 的票数。
- `checkedInTicketCount`：明细状态为 `USED` 的票数。
- `refundedTicketCount`：明细状态为 `REFUNDED` 的票数。

## 安全边界

- 权限：必须先校验管理员 session；匿名和游客 session 不能触达 repository。
- DTO：不复用数据库行，不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。
- SQL：日期筛选只通过参数绑定进入 SQL，不拼接原始查询字符串。
- 聚合：订单金额聚合与明细票数聚合分开，避免订单金额因明细 join 被重复放大。
- 日志：不新增业务日志，避免把查询参数或聚合结果写入日志。

## 数据流

1. Router 接收可选日期参数。
2. `AdminReportService` 校验管理员 session 和日期范围。
3. Repository 使用参数化 SQL 聚合日维度报表。
4. Service 转换为 `AdminDailyTrendDTO` 列表。
5. Router 返回统一成功壳。

## 验收

- 管理员可在无 CSRF header 的情况下读取日报趋势。
- 匿名和游客 session 被拒绝，且不会调用 repository。
- 日期范围非法返回 `ADMIN_REPORT_DATE_RANGE_INVALID`。
- 响应不包含完整手机号、证件号、session、CSRF、密码 hash、数据库内部 id。
- Postgres 查询使用参数绑定，SQL 字符串不包含具体日期值。
- SQL 先按订单日期聚合金额，再按明细聚合票数，不能把订单金额因 join 放大。
- OpenAPI 记录该端点返回 `ApiSuccessDTO[list[AdminDailyTrendDTO]]`，并且 endpoint 清单与后端实际路由一致。
