# 后台核销审计日志 XLSX 导出设计

## 问题

核销审计日志已有全局检索和 CSV 导出，但运营复盘通常会在 Excel 中筛选、排序和留档。这个切片补齐同步 `.xlsx` 下载能力，沿用 CSV 导出的权限、筛选和字段边界，不引入异步任务、对象存储或新运行时依赖。

## 范围

- 新增管理员只读导出接口 `GET /api/admin/check-in-logs.xlsx`。
- 支持可选筛选：`ticketCode`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo`。
- 导出列与 CSV 保持一致：`orderNo`、`itemNo`、`ticketCode`、`action`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- 返回 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，并带 `Content-Disposition` 下载文件名。

## 权限和安全

- 仅管理员 session 可访问；未登录返回 `ADMIN_AUTH_REQUIRED`，游客 session 返回 `ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 日期范围非法时返回 `ADMIN_CHECK_IN_LOG_DATE_RANGE_INVALID`。
- 导出只包含审计日志安全字段，不返回完整手机号、证件号、session、CSRF、密码 hash、内部 id 或 `adminUserId`。
- 所有单元格写为 inline string，不生成公式节点；以 `=`、`+`、`-`、`@`、制表/换行/回车或空格后公式前缀开头的值统一加单引号。
- 写入 XML 前清理 XML 1.0 非法控制字符，避免损坏 XLSX 包。

## API

```http
GET /api/admin/check-in-logs.xlsx?ticketCode=unused&orderNo=paid&operatorUsername=adm&dateFrom=2026-07-02&dateTo=2026-07-02
```

成功响应：

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="admin-check-in-logs-20260702-20260702.xlsx"`
- body 为最小 OOXML XLSX 文件。

## 验收

- `backend/tests/test_admin_check_in_api.py` 覆盖 XLSX 下载、筛选透传、管理员权限、只读 GET 无 CSRF、日期范围错误、敏感字段不外泄、无公式节点和 XML 控制字符清洗。
- `backend/tests/test_openapi_contract.py` 覆盖 OpenAPI 文件响应和 no-CSRF GET 列表。
- `scripts/verify-integration.sh` 作为最终回归门禁。

## 暂不做

- 退款审计日志 XLSX 导出。
- 异步大文件导出、导出历史和对象存储。
- 失败尝试审计、撤销原因和审批流。
- 真实支付/退款渠道对账字段。
