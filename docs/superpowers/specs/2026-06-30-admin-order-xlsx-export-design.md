# 后台订单 XLSX 导出设计

日期：2026-06-30

## 问题定义

后台订单 CSV 导出已经能满足基础留档，但运营人员更常使用 Excel 打开 `.xlsx` 文件。这个切片在不引入异步任务和对象存储的前提下，补一个同步 XLSX 下载端点，复用已有订单导出查询、权限和安全字段边界。

## 边界

本切片实现：

- `GET /api/admin/reports/orders.xlsx`
- 可选 `dateFrom`、`dateTo` 查询参数，按订单创建日期过滤。
- 只允许管理员 session 访问；这是只读 GET，不要求 CSRF header。
- 返回 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，并带 `Content-Disposition` 下载文件名。
- XLSX 只导出订单级安全字段：订单号、买家姓名、脱敏手机号、订单状态、支付状态、订单总额、应付金额、下单时间、票数。
- XLSX 单元格统一写成字符串单元格，不写公式；危险公式开头的文本继续加单引号，和 CSV 导出保持一致。
- 使用 Python 标准库生成最小 Office Open XML 工作簿，不新增运行时依赖。

本切片不实现：

- 核销审计或退款审计 XLSX。
- 异步导出任务、导出任务历史或对象存储。
- 大文件分页流式生成。
- 产品维度 XLSX、真实支付渠道对账文件或财务结算口径。

## API 契约

```text
GET /api/admin/reports/orders.xlsx?dateFrom=2026-07-01&dateTo=2026-07-31
```

成功响应不是统一 JSON 成功壳，而是 XLSX 文件：

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="admin-orders-20260701-20260731.xlsx"`

错误响应仍使用统一失败壳：

- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`
- 游客 session：`403 ADMIN_FORBIDDEN`
- `dateFrom > dateTo`：`422 ADMIN_REPORT_DATE_RANGE_INVALID`

## 安全边界

- 权限：必须先校验管理员 session；匿名和游客 session 不能触达 repository。
- 敏感字段：不导出完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、SQL 或审计字段。
- 公式注入：所有 XLSX 单元格写成 inline string，不生成 `<f>` 公式节点；危险开头或前导空格后的危险开头继续加单引号。
- 文件合法性：写入 worksheet 前移除 XML 1.0 非法控制字符，避免单条脏数据损坏整个 XLSX。
- SQL：复用 `list_admin_order_export_rows`，日期筛选只通过参数绑定进入 SQL，不拼接原始查询字符串。
- 日志：不新增业务日志，避免把导出查询参数或 XLSX 内容写入日志。

## 数据流

1. Router 接收可选日期参数。
2. `AdminReportService` 校验管理员 session 和日期范围。
3. Repository 使用参数化 SQL 拉取订单导出行。
4. Service 把行转换成 XLSX bytes，脱敏手机号并做公式注入防护。
5. Router 以文件响应返回 XLSX。

## 验收

- 管理员可在无 CSRF header 的情况下导出 XLSX。
- 匿名和游客 session 被拒绝，且不会调用导出 repository。
- 日期范围非法返回 `ADMIN_REPORT_DATE_RANGE_INVALID`。
- XLSX 不包含完整手机号、证件号、session、CSRF、密码 hash、数据库内部 id。
- 买家姓名等字段即使以 `=`、`+`、`-`、`@` 等开头，也不会作为公式节点进入 XLSX。
- 买家姓名等字段包含 XML 1.0 非法控制字符时，导出的 worksheet 仍能被 XML 解析器读取。
- OpenAPI 记录该端点返回 XLSX 文件，并且 endpoint 清单与后端实际路由一致。
