# 后台核销失败尝试审计 CSV 导出设计

日期：2026-07-01

## 问题定义

后台已经能检索核销/撤销核销业务失败尝试，但运营排查和安全复盘通常需要把同一批失败记录下载到表格工具中留档。当前成功核销审计和退款审计都已有 CSV 导出，本切片给失败尝试审计补齐同级别的最小导出能力。

## 边界

本切片实现：

- 新增 `GET /api/admin/check-in-failure-logs.csv`。
- 复用现有失败审计筛选条件：`ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo`。
- 成功响应为 CSV 文件，不使用统一 JSON 成功壳。
- 导出字段：`ticketCode`、`action`、`failureCode`、`failureMessage`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- 所有单元格经过公式注入防护。
- 管理员只读 GET 不要求 CSRF，但必须有管理员 session。
- 复用现有失败码和日期范围校验。

本切片不实现：

- XLSX 导出、异步大文件导出或对象存储。
- 自动风控、告警、趋势报表。
- 新增筛选条件或改动前端页面。
- 把失败尝试导出混入成功核销审计导出。

## API 契约

```text
GET /api/admin/check-in-failure-logs.csv?failureCode=TICKET_NOT_CHECKED_IN&dateFrom=2026-07-01&dateTo=2026-07-31
```

成功响应：

- `Content-Type: text/csv; charset=utf-8`
- `Content-Disposition: attachment; filename="admin-check-in-failure-logs-<start>-<end>.csv"`
- CSV 第一行是固定表头。
- 未传日期时文件名中对应位置使用 `start` 或 `end`。

错误响应仍走统一失败壳：

- 未登录管理员：`401 ADMIN_AUTH_REQUIRED`
- 游客 session：`403 ADMIN_FORBIDDEN`
- 非法失败码：`422 ADMIN_CHECK_IN_FAILURE_CODE_INVALID`
- `dateFrom > dateTo`：`422 ADMIN_CHECK_IN_FAILURE_LOG_DATE_RANGE_INVALID`

## 安全边界

- 导出只允许管理员 session；游客和匿名不能读取。
- GET 导出不要求 CSRF，因为不改变服务端状态。
- CSV 不返回手机号、证件号、session token、CSRF token、密码 hash、内部 id、订单内部 id、`adminUserId` 或 SQL。
- 所有可控文本单元格都使用既有 `safe_csv_cell`，防止 `=`, `+`, `-`, `@`, tab, CR/LF 前缀触发表格公式。
- Repository 查询必须参数绑定，不能拼接票码、失败码、操作人或日期。

## 数据流

1. Router 接收 GET 请求和筛选参数。
2. Service 校验管理员 session、失败码和日期范围。
3. Repository 复用失败审计表查询条件，按 `created_at DESC, id DESC` 导出全部匹配记录。
4. Service 转成 CSV 文本并加 UTF-8 BOM，便于 Excel 识别中文。
5. Router 返回文件响应。

## 验收

- 管理员不带 CSRF 可按筛选导出失败审计 CSV。
- 匿名和游客 session 不能导出。
- 非法失败码和非法日期范围返回专门错误码。
- CSV 字段不泄露敏感数据。
- CSV 单元格覆盖公式注入防护。
- Postgres 导出 SQL 使用参数绑定，并按 `created_at DESC, id DESC` 排序。
- OpenAPI 文档声明 CSV 文件响应。
