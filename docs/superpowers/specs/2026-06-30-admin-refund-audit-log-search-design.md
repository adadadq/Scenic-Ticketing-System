# 后台退款审计日志检索设计

日期：2026-06-30

## 1. 问题

后台已经能在订单详情维度读取退款审计日志，但运营复盘时经常需要跨订单查找“某天谁做了哪些退款”“某个管理员处理了哪些退款”“全部部分退款记录在哪里”。只按订单号进入详情再查看日志，无法支撑审计检索页或异常退款排查。

## 2. 范围

本切片只做：

- 新增管理员只读检索接口 `GET /api/admin/refund-logs`。
- 支持按退款类型、订单号、操作人、审计创建日期范围筛选。
- 支持 `page`、`pageSize` 分页。
- 复用已有 `AdminRefundAuditLogDTO` 作为列表项，并新增分页壳 DTO。
- DTO 不返回数据库内部 id、`adminUserId`、完整手机号、证件号、session、CSRF、密码 hash 或 SQL。

本切片不做：

- 独立前端页面或 React 组件。
- 审计日志导出。
- 全业务操作日志检索。
- 真实渠道退款流水号、退款通知或财务对账。

## 3. API

```text
GET /api/admin/refund-logs
```

查询参数：

- `refundType`：可选，`FULL` 或 `PARTIAL`。
- `orderNo`：可选，模糊匹配订单号。
- `operatorUsername`：可选，模糊匹配操作人用户名。
- `dateFrom`：可选，按审计日志 `createdAt` 日期下界筛选。
- `dateTo`：可选，按审计日志 `createdAt` 日期上界筛选。
- `page`：默认 1，最小 1。
- `pageSize`：默认 20，1 到 100。

成功返回 `AdminRefundAuditLogListDTO`：

- `items: AdminRefundAuditLogDTO[]`
- `total`
- `page`
- `pageSize`

按 `createdAt DESC, id DESC` 排序。

## 4. 权限与安全

- 只接受管理员 session。
- 这是只读 GET，不要求 CSRF header。
- 匿名返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 返回 `403 ADMIN_FORBIDDEN`。
- `refundType` 非空但不是 `FULL/PARTIAL` 时返回 `422 ADMIN_REFUND_LOG_TYPE_INVALID`。
- `dateFrom > dateTo` 时返回 `422 ADMIN_REFUND_LOG_DATE_RANGE_INVALID`。
- 只使用参数化 SQL，不能拼接用户输入。

## 5. 验收

```bash
.venv/bin/pytest backend/tests/test_admin_refund_api.py backend/tests/test_openapi_contract.py backend/tests/test_schema_contract.py -q
scripts/verify-integration.sh
```

验收点：

- 管理员可无 CSRF 读取全局退款审计日志分页列表。
- 筛选参数能传到 repository，并使用参数化 SQL。
- 匿名、游客、非法退款类型和非法日期范围都有明确错误码。
- 响应不泄露敏感字段或内部 id。
- OpenAPI、`docs/api-contract.md`、安全清单和里程碑事实源包含该接口。
