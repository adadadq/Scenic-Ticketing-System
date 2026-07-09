# 后台退款审计日志设计

日期：2026-06-30

## 1. 问题

后台已经支持整单模拟退款和按票项部分模拟退款，但退款是高风险状态变更：它会影响订单金额、票项状态、库存售出量和支付状态。系统需要留下可追溯记录，说明谁在什么时候退了哪张订单、哪些票项、多少钱、为什么退，以及这次请求的 request id。

## 2. 范围

本切片只做：

- 新增 `refund_audit_log` 数据库表。
- 整单退款成功时，在同一事务写入 `FULL` 审计日志。
- 部分退款成功时，在同一事务写入 `PARTIAL` 审计日志。
- 提供订单维度只读查询接口。
- 审计日志 DTO 不返回数据库内部 id、`adminUserId`、session、CSRF、密码 hash、完整手机号或证件号。

本切片不做：

- 真实支付渠道退款。
- 退款通知回调。
- 真实渠道退款流水号。
- 独立审计检索页、全局审计列表或导出。
- 前端页面或 React 组件。

## 3. API

```text
GET /api/admin/orders/{order_no}/refund-logs
```

返回 `AdminRefundAuditLogDTO[]`，按 `createdAt` 倒序：

- `orderNo`
- `refundType`：`FULL` 或 `PARTIAL`
- `refundedAmount`
- `refundedItemCount`
- `refundedItemNos`
- `reason`
- `operatorUsername`
- `operatorDisplayName`
- `requestId`
- `createdAt`

其中 `reason` 和 `requestId` 可为 `null`；写入审计表的 `requestId` 最长保存 64 字符，避免客户端超长 header 影响退款事务。

订单不存在返回 `404 ADMIN_ORDER_NOT_FOUND`。订单存在但没有退款日志时返回空数组。

## 4. 写入规则

- 审计日志只由后端退款事务写入，前端不能提交操作人、金额、状态或时间。
- 操作人来自管理员 session：`admin.id` 只入库用于外键，不进入响应 DTO。
- `operatorUsername` 和 `operatorDisplayName` 做展示冗余，避免后续管理员显示名变化后历史日志失真。
- `requestId` 来自服务端请求上下文，便于和请求日志关联；审计表只保留前 64 字符。
- `refundedItemNos` 使用 JSONB 保存，读取时转成数组 DTO。
- 如果审计日志写入失败，退款事务整体失败并回滚。

## 5. 权限与安全

- 查询接口只接受管理员 session。
- 这是只读 GET，不要求 CSRF header。
- 匿名返回 `401 ADMIN_AUTH_REQUIRED`。
- 游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 响应不返回完整手机号、证件号、session、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。

## 6. 验收

```bash
.venv/bin/pytest backend/tests/test_admin_refund_api.py backend/tests/test_schema_contract.py backend/tests/test_openapi_contract.py -q
scripts/verify-integration.sh
```

验收点：

- 整单退款成功后可读到 `FULL` 审计日志。
- 部分退款成功后可读到 `PARTIAL` 审计日志。
- 审计日志记录操作人展示字段、原因、金额、票项号和 request id。
- 查询接口要求管理员 session，但不要求 CSRF。
- SQL 成功路径写入 `refund_audit_log`；失败路径不产生审计副作用。
- OpenAPI 和 `docs/api-contract.md` 均包含新 GET 接口。
