# 后台运营汇总报表 API 设计

## 1. 问题定义

管理员已经可以登录、查看订单、核销票码和执行全单模拟退款。后台首页还需要一个只读运营概览，让前端能展示订单数量、票数流转和当前净收款，而不是从订单列表分页里临时拼统计。

本切片先实现最小汇总报表，不做导出、分组图表或真实支付对账。

## 2. 范围

包含：

- 管理员获取运营汇总。
- 可选 `dateFrom` / `dateTo` 按订单创建日期过滤。
- 返回订单状态统计、票数状态统计和当前净收款。
- 只读接口，只接受管理员 session。

不包含：

- Excel/CSV 导出。
- 按产品、码头、日期分组的图表。
- 真实支付渠道对账。
- 财务口径收入确认。
- 前端页面实现。

## 3. API 契约

```http
GET /api/admin/reports/summary?dateFrom=2026-07-01&dateTo=2026-07-31
```

查询参数：

- `dateFrom`：可选，ISO 日期，按 `ticket_order.order_time::date >= dateFrom` 过滤。
- `dateTo`：可选，ISO 日期，按 `ticket_order.order_time::date <= dateTo` 过滤。

成功响应 `data`：

```json
{
  "dateFrom": "2026-07-01",
  "dateTo": "2026-07-31",
  "orderCount": 5,
  "paidOrderCount": 2,
  "completedOrderCount": 1,
  "refundedOrderCount": 1,
  "cancelledOrderCount": 1,
  "netPaidAmount": "384.00",
  "ticketCount": 7,
  "soldTicketCount": 3,
  "checkedInTicketCount": 1,
  "refundedTicketCount": 2
}
```

字段口径：

- `orderCount`：过滤范围内全部订单数。
- `paidOrderCount`：`payment_status = PAID` 的订单数。
- `completedOrderCount`：`order_status = COMPLETED` 的订单数。
- `refundedOrderCount`：`order_status = REFUNDED` 的订单数。
- `cancelledOrderCount`：`order_status = CANCELLED` 的订单数。
- `netPaidAmount`：过滤范围内订单当前 `paid_amount` 汇总；全单退款后该订单为 0。
- `ticketCount`：过滤范围内订单明细总数。
- `soldTicketCount`：`item_status IN (UNUSED, USED)` 的明细数。
- `checkedInTicketCount`：`item_status = USED` 的明细数。
- `refundedTicketCount`：`item_status = REFUNDED` 的明细数。

错误：

- 未登录：`401 ADMIN_AUTH_REQUIRED`。
- 游客 session：`403 ADMIN_FORBIDDEN`。
- `dateFrom > dateTo`：`422 ADMIN_REPORT_DATE_RANGE_INVALID`。

## 4. 权限与安全

- 只接受管理员 session。
- GET 只读接口，不要求 CSRF。
- 不接受前端提交管理员 id、订单状态或聚合字段。
- 响应不返回完整手机号、证件号、session、CSRF token、密码 hash、数据库内部 id 或审计字段。
- SQL 使用参数绑定日期条件，不拼接查询参数。

## 5. 数据与并发

- 报表只读，不锁订单。
- 统计以查询时数据库当前状态为准。
- 订单和明细聚合分开计算，避免 join 后订单金额被明细行重复放大。

## 6. 验收

目标测试：

```bash
.venv/bin/pytest backend/tests/test_admin_reports_api.py backend/tests/test_openapi_contract.py -q
```

覆盖：

- 管理员可带日期过滤读取汇总。
- GET 不需要 CSRF header。
- 匿名和游客 session 不能读取。
- 日期范围反向返回领域错误。
- DTO 不泄露手机号、证件号、session 或 CSRF。
- SQL 使用参数绑定日期过滤。
- OpenAPI 暴露 `AdminReportSummaryDTO` 和 `dateFrom` / `dateTo` 查询参数。
