# 后台核销审计日志 CSV 导出设计

日期：2026-06-30

## 1. 问题

后台已经支持全局核销审计检索，能在页面上按票码、订单号、操作人和日期查日志。运营复盘、异常核销排查和线下留档还需要把同一批检索结果下载到表格工具中核对。本切片先做轻量 CSV 导出，延续当前检索口径。

## 2. 范围

本切片只做：

- 新增管理员只读导出接口 `GET /api/admin/check-in-logs.csv`。
- 复用全局核销审计检索筛选：`ticketCode`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo`。
- CSV 只导出安全字段：订单号、票项号、票码、动作、操作人展示字段、request id 和审计时间。
- 对所有 CSV 单元格做公式注入防护。
- 使用 `text/csv; charset=utf-8` 文件响应，文件名包含日期范围。

本切片不做：

- XLSX 导出。
- 异步导出任务、导出历史或对象存储。
- 撤销核销。
- 批量核销。
- 导出权限细分和下载审计日志。

## 3. API

```text
GET /api/admin/check-in-logs.csv
```

查询参数：

- `ticketCode`：可选，模糊匹配票码。
- `orderNo`：可选，模糊匹配订单号。
- `operatorUsername`：可选，模糊匹配操作人用户名。
- `dateFrom`：可选，按审计日志 `createdAt` 日期下界筛选。
- `dateTo`：可选，按审计日志 `createdAt` 日期上界筛选。

成功响应：

- `Content-Type: text/csv; charset=utf-8`
- `Content-Disposition: attachment; filename="admin-check-in-logs-<start>-<end>.csv"`
- 未传日期时文件名使用 `start` 和 `end` 占位。

CSV 表头：

```text
orderNo,itemNo,ticketCode,action,operatorUsername,operatorDisplayName,requestId,createdAt
```

## 4. 权限与安全

- 只接受管理员 session。
- 这是只读 GET，不要求 CSRF header。
- 匿名返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 返回 `403 ADMIN_FORBIDDEN`。
- `dateFrom > dateTo` 时返回 `422 ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID`。
- 不导出数据库内部 id、`adminUserId`、完整手机号、证件号、session、CSRF、密码 hash 或 SQL。
- Postgres 查询使用参数绑定，且导出排序为 `created_at DESC, id DESC`。
- 对 `=`, `+`, `-`, `@`, tab、回车、换行开头，以及前导空白后出现这些字符的单元格加单引号。

## 5. 验收

```bash
.venv/bin/pytest backend/tests/test_admin_check_in_api.py backend/tests/test_openapi_contract.py -q
scripts/verify-integration.sh
```

验收点：

- 管理员可无 CSRF 下载核销审计 CSV。
- 匿名和游客 session 被拒绝。
- 非法日期范围返回专门错误码。
- CSV 不泄露敏感字段或内部 id。
- CSV 公式注入防护覆盖所有导出列。
- Postgres 导出 SQL 使用参数绑定，SQL 字符串不包含具体筛选值。
- OpenAPI 和 `docs/api-contract.md` 声明文件响应。
