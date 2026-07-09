# 后台产品维度报表设计

日期：2026-06-30

## 问题定义

后台已经有运营汇总和订单 CSV 导出，但管理台图表还需要一个按产品/票种分组的明细口径，用来展示哪些票品贡献了订单、售票、核销和退款。这个切片先做产品维度分组报表，不进入真实财务对账或复杂 BI。

## 边界

本切片实现：

- `GET /api/admin/reports/product-breakdown`
- 可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤。
- 只允许管理员 session 访问；这是只读 GET，不要求 CSRF header。
- 返回统一 `ApiSuccessDTO[list[AdminProductBreakdownDTO]]`。
- 每一行按 `productId + ticketTypeId + productName + ticketName` 分组。
- 返回订单数、总票数、已售票数、已核销票数、已退款票数和当前净收款。

本切片不实现：

- 按小时/天/月的时间序列趋势。
- 多维度任意分组、排序参数或分页。
- 真实财务对账、支付渠道手续费或退款通知。
- 前端图表样式和交互。

## API 契约

```text
GET /api/admin/reports/product-breakdown?dateFrom=2026-07-01&dateTo=2026-07-31
```

成功响应：

```json
{
  "success": true,
  "data": [
    {
      "productId": 1,
      "ticketTypeId": 10,
      "productName": "金龙桥至旧县成人票",
      "ticketName": "遇龙河成人票",
      "orderCount": 3,
      "ticketCount": 6,
      "soldTicketCount": 4,
      "checkedInTicketCount": 2,
      "refundedTicketCount": 1,
      "netPaidAmount": "512.00"
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

- `orderCount`：包含该产品明细的去重订单数。
- `ticketCount`：该产品下所有订单明细数。
- `soldTicketCount`：明细状态为 `UNUSED` 或 `USED` 的票数。
- `checkedInTicketCount`：明细状态为 `USED` 的票数。
- `refundedTicketCount`：明细状态为 `REFUNDED` 的票数。
- `netPaidAmount`：只统计当前仍有效的已售票明细金额，即 `UNUSED` 和 `USED` 明细的 `final_price` 合计。

## 安全边界

- 权限：必须先校验管理员 session；匿名和游客 session 不能触达 repository。
- DTO：不复用数据库行，不返回完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。
- SQL：日期筛选只通过参数绑定进入 SQL，不拼接原始查询字符串。
- 聚合：金额从明细维度聚合，避免订单金额在 join 后被重复放大。
- 日志：不新增业务日志，避免把查询参数或聚合结果写入日志。

## 数据流

1. Router 接收可选日期参数。
2. `AdminReportService` 校验管理员 session 和日期范围。
3. Repository 使用参数化 SQL 聚合产品维度报表。
4. Service 转换为 `AdminProductBreakdownDTO` 列表。
5. Router 返回统一成功壳。

## 验收

- 管理员可在无 CSRF header 的情况下读取产品维度报表。
- 匿名和游客 session 被拒绝，且不会调用 repository。
- 日期范围非法返回 `ADMIN_REPORT_DATE_RANGE_INVALID`。
- 响应不包含完整手机号、证件号、session、CSRF、密码 hash、数据库内部 id。
- Postgres 查询使用参数绑定，SQL 字符串不包含具体日期值。
- SQL 使用 `COUNT(DISTINCT o.id)` 统计订单数，金额按明细 `final_price` 条件聚合，不把订单金额因 join 放大。
- OpenAPI 记录该端点返回 `ApiSuccessDTO[list[AdminProductBreakdownDTO]]`，并且 endpoint 清单与后端实际路由一致。
