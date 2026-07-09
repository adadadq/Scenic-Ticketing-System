# 后台订单 CSV 导出设计

日期：2026-06-30

## 问题定义

后台运营汇总报表已经能给管理台首页提供概览，但运营人员仍需要把订单明细导出到表格工具中核对、筛选和留档。这个切片先提供订单级 CSV 导出，不进入真实财务对账和复杂 BI。

## 边界

本切片实现：

- `GET /api/admin/reports/orders.csv`
- 可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤。
- 只允许管理员 session 访问；这是只读 GET，不要求 CSRF header。
- 返回 `text/csv; charset=utf-8`，并带 `Content-Disposition` 下载文件名。
- CSV 只导出订单级安全字段：订单号、买家姓名、脱敏手机号、订单状态、支付状态、订单总额、应付金额、下单时间、票数。
- 对每个 CSV 单元格做公式注入防护，避免以 `=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的内容被表格软件当公式执行。

本切片不实现：

- XLSX 导出。
- 异步导出任务、导出任务历史或对象存储。
- 产品维度分组图表。
- 真实支付渠道对账文件。
- 退款通知或部分退款。

## API 契约

```text
GET /api/admin/reports/orders.csv?dateFrom=2026-07-01&dateTo=2026-07-31
```

成功响应不是统一 JSON 成功壳，而是 CSV 文件：

- `Content-Type: text/csv; charset=utf-8`
- `Content-Disposition: attachment; filename="admin-orders-20260701-20260731.csv"`
- CSV 使用 UTF-8 BOM，降低中文在 Excel 中乱码的概率。

错误响应仍使用统一失败壳：

- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`
- 游客 session：`403 ADMIN_FORBIDDEN`
- `dateFrom > dateTo`：`422 ADMIN_REPORT_DATE_RANGE_INVALID`

## 安全边界

- 权限：必须先校验管理员 session；匿名和游客 session 不能触达 repository。
- 敏感字段：不导出完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。
- CSV 注入：所有单元格统一经过转义，危险开头或前导空格后的危险开头会加单引号。
- SQL：日期筛选只通过参数绑定进入 SQL，不拼接原始查询字符串。
- 日志：不新增业务日志，避免把导出查询参数或 CSV 内容写入日志。

## 数据流

1. Router 接收可选日期参数。
2. `AdminReportService` 校验管理员 session 和日期范围。
3. Repository 使用参数化 SQL 拉取订单导出行。
4. Service 把行转换成 CSV 文本，脱敏手机号并做 CSV 公式注入防护。
5. Router 以文件响应返回 CSV。

## 验收

- 管理员可在无 CSRF header 的情况下导出 CSV。
- 匿名和游客 session 被拒绝，且不会调用导出 repository。
- 日期范围非法返回 `ADMIN_REPORT_DATE_RANGE_INVALID`。
- CSV 不包含完整手机号、证件号、session、CSRF、密码 hash、数据库内部 id。
- 买家姓名等字段即使以 `=`、`+`、`-`、`@` 等开头，也不会原样作为公式开头进入 CSV。
- Postgres 导出 SQL 使用参数绑定，SQL 字符串不包含具体日期值。
- OpenAPI 记录该端点返回 `text/csv`，并且 endpoint 清单与后端实际路由一致。
