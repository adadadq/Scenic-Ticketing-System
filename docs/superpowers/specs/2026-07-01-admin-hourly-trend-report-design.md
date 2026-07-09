# 后台小时趋势报表设计

日期：2026-07-01

## 问题

后台已经有运营汇总、产品维度、日报趋势和月度趋势。日报适合看天级波动，月报适合长周期复盘，但运营排查当天入园、支付和退款波峰时，需要小时粒度趋势。

## 范围

- 新增 `GET /api/admin/reports/hourly-trend`。
- 复用现有报表日期筛选：`dateFrom`、`dateTo` 按订单创建日期过滤。
- 返回有订单活动的小时聚合行，不对无订单小时补零。
- 复用日报/月报统计口径：订单数、已支付订单数、完成订单数、退款订单数、取消订单数、净收款、票数、售出票数、核销量和退款票数。
- 只读管理员接口，不要求 CSRF，但必须校验管理员 session。

## 不做

- 小时序列补零。
- 小时趋势 CSV/XLSX 导出。
- 真实财务对账、真实支付渠道对账或退款通知。
- 前端页面实现。

## API

`GET /api/admin/reports/hourly-trend`

查询参数：

- `dateFrom?: YYYY-MM-DD`
- `dateTo?: YYYY-MM-DD`

成功响应：统一 `ApiSuccessDTO<AdminHourlyTrendDTO[]>`。

`AdminHourlyTrendDTO` 字段：

- `reportHour`: `YYYY-MM-DDTHH:00:00`
- `orderCount`
- `paidOrderCount`
- `completedOrderCount`
- `refundedOrderCount`
- `cancelledOrderCount`
- `netPaidAmount`
- `ticketCount`
- `soldTicketCount`
- `checkedInTicketCount`
- `refundedTicketCount`

错误：

- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`
- 游客 session：`403 ADMIN_FORBIDDEN`
- `dateFrom > dateTo`：`422 ADMIN_REPORT_DATE_RANGE_INVALID`

## 安全边界

- 只返回聚合数据，不返回手机号、证件号、visitor id、admin user id、session、CSRF、SQL 或内部数据库 id。
- SQL 查询只使用参数绑定，日期不能拼进 SQL 字符串。
- 金额聚合和票项聚合分开计算，避免订单金额因为 join 明细被重复放大。

## 验收

- `backend/tests/test_admin_reports_api.py` 覆盖权限、日期范围、DTO 防泄露和 SQL 参数绑定。
- `backend/tests/test_openapi_contract.py` 覆盖 OpenAPI 成功 DTO、查询参数和只读 GET 不声明 CSRF header。
- `backend/tests/test_backend_milestone_status.py` 覆盖里程碑事实源。
- `scripts/verify-backend.sh` 和 `scripts/verify-integration.sh` 作为提交前门禁。
