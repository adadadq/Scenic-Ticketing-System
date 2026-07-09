# 后台产品维度报表 XLSX 导出设计

日期：2026-07-01

## 问题

后台产品维度报表已经提供 JSON 和 CSV，前端管理台还需要一个适合直接交给运营人员打开、筛选和归档的 XLSX 下载入口。这个切片只补同一报表口径的文件导出，不改变聚合 SQL、统计口径或前端页面。

## 范围

- 新增 `GET /api/admin/reports/product-breakdown.xlsx`。
- 复用 `GET /api/admin/reports/product-breakdown` 的管理员权限、日期过滤、日期范围校验和产品/票种分组口径。
- 输出固定列：`productId`、`ticketTypeId`、`productName`、`ticketName`、`orderCount`、`ticketCount`、`soldTicketCount`、`checkedInTicketCount`、`refundedTicketCount`、`netPaidAmount`。
- 成功响应是 XLSX 文件，`Content-Type` 为 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，`Content-Disposition` 使用 `attachment; filename="admin-product-breakdown-<start>-<end>.xlsx"`。

## 边界

- 这是只读 GET，不要求 CSRF header。
- 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- `dateFrom > dateTo` 返回 `422 ADMIN_REPORT_DATE_RANGE_INVALID`，并且不访问 repository。
- 不返回买家姓名、完整手机号、证件号、支付流水号、渠道交易号、session token、CSRF token、密码 hash、SQL、审计明细或内部审计字段。
- 单元格统一写成 inline string，不生成公式节点；文本复用表格公式注入防护并清理 XML 1.0 非法控制字符。

## 验收

- `backend/tests/test_admin_report_export_api.py` 覆盖 XLSX 下载、管理员权限、只读 GET 无 CSRF、日期范围错误、敏感字段防泄露、inline string、无公式节点和 XML 清洗。
- `backend/tests/test_openapi_contract.py` 覆盖 OpenAPI 文件响应和只读 GET 无 CSRF 契约。
- `scripts/verify-backend.sh` 作为提交前默认后端验收入口。
