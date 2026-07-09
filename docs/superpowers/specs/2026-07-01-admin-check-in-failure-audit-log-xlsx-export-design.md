# 后台核销失败尝试审计 XLSX 导出设计

日期：2026-07-01

## 问题定义

失败尝试审计已经支持检索和 CSV 导出，但运营复盘与安全留档通常会直接在 Excel 中筛选、排序和归档。这个切片补齐同步 XLSX 下载能力，沿用 CSV 导出的权限、筛选和字段边界，不新增异步任务、对象存储或运行时依赖。

## 边界

本切片实现：

- 新增 `GET /api/admin/check-in-failure-logs.xlsx`。
- 复用失败审计筛选条件：`ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo`。
- 成功响应为 XLSX 文件，不使用统一 JSON 成功壳。
- 导出字段与 CSV 一致：`ticketCode`、`action`、`failureCode`、`failureMessage`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- 所有单元格按 inline string 写入，并复用公式注入防护。
- XML 写入前清理 XML 1.0 非法控制字符，避免损坏 XLSX 包。
- 管理员只读 GET 不要求 CSRF，但必须有管理员 session。
- 复用现有失败码和日期范围校验。

本切片不实现：

- 异步大文件导出、导出历史或对象存储。
- 自动风控、告警、趋势报表。
- 新增筛选条件或改动前端页面。
- 把失败尝试导出混入成功核销审计导出。

## API 契约

```text
GET /api/admin/check-in-failure-logs.xlsx?failureCode=TICKET_NOT_CHECKED_IN&dateFrom=2026-07-01&dateTo=2026-07-31
```

成功响应：

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="admin-check-in-failure-logs-<start>-<end>.xlsx"`
- body 为最小 OOXML XLSX 文件。
- 未传日期时文件名中对应位置使用 `start` 或 `end`。

错误响应仍走统一失败壳：

- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`
- 游客 session：`403 ADMIN_FORBIDDEN`
- 非法失败码：`422 ADMIN_CHECK_IN_FAILURE_CODE_INVALID`
- `dateFrom > dateTo`：`422 ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID`

## 安全边界

- 导出只允许管理员 session；游客和匿名不能读取。
- GET 导出不要求 CSRF，因为不改变服务端状态。
- XLSX 不返回手机号、证件号、session token、CSRF token、密码 hash、内部 id、订单内部 id、`adminUserId` 或 SQL。
- 所有可控文本单元格都使用既有 `safe_csv_cell`，防止 `=`, `+`, `-`, `@`, tab, CR/LF 前缀或前导空格后的危险前缀触发表格公式。
- XLSX worksheet 不生成 `<f>` 公式节点，单元格统一写为 inline string。
- Repository 查询复用失败审计导出查询，必须参数绑定，不能拼接票码、失败码、操作人或日期。

## 数据流

1. Router 接收 GET 请求和筛选参数。
2. Service 校验管理员 session、失败码和日期范围。
3. Repository 复用失败审计表查询条件，按 `created_at DESC, id DESC` 导出全部匹配记录。
4. Service 复用 CSV 的安全行构造，生成 XLSX workbook bytes。
5. Router 返回文件响应。

## 验收

- 管理员不带 CSRF 可按筛选导出失败审计 XLSX。
- 匿名和游客 session 不能导出。
- 非法失败码和非法日期范围返回专门错误码。
- XLSX 字段不泄露敏感数据。
- XLSX 单元格覆盖公式注入防护，不生成公式节点。
- XLSX 清理 XML 1.0 非法控制字符。
- Postgres 导出查询继续使用参数绑定，并按 `created_at DESC, id DESC` 排序。
- OpenAPI 文档声明 XLSX 文件响应和 `Content-Disposition` header。
