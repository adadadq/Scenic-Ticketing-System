# 后台退款审计日志 XLSX 导出设计

## 问题

退款审计日志已有全局检索和 CSV 导出，但运营复盘、异常退款排查和留档也需要可直接用 Excel 打开的 `.xlsx` 文件。这个切片补齐同步 XLSX 下载能力，沿用 CSV 导出的筛选、字段和权限边界，不引入异步任务、对象存储或新运行时依赖。

## 范围

- 新增管理员只读导出接口 `GET /api/admin/refund-logs.xlsx`。
- 支持可选筛选：`refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo`。
- `refundType` 只允许 `FULL` 或 `PARTIAL`，大小写输入由服务层归一化。
- 导出列与 CSV 保持一致：`orderNo`、`refundType`、`refundedAmount`、`refundedItemCount`、`refundedItemNos`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- 返回 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`，并带 `Content-Disposition` 下载文件名。

## 权限和安全

- 仅管理员 session 可访问；未登录返回 `ADMIN_AUTH_REQUIRED`，游客 session 返回 `ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 非法退款类型返回 `ADMIN_REFUND_LOG_TYPE_INVALID`；日期范围非法返回 `ADMIN_REFUND_LOG_DATE_RANGE_INVALID`。
- 导出只包含审计日志安全字段，不返回完整手机号、证件号、session、CSRF、密码 hash、内部 id 或 `adminUserId`。
- 所有单元格写为 inline string，不生成公式节点；以 `=`、`+`、`-`、`@`、制表/换行/回车或空格后公式前缀开头的值统一加单引号。
- 写入 XML 前清理 XML 1.0 非法控制字符，避免损坏 XLSX 包。

## API

```http
GET /api/admin/refund-logs.xlsx?refundType=partial&orderNo=paid&operatorUsername=adm&dateFrom=2026-07-02&dateTo=2026-07-02
```

成功响应：

- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="admin-refund-logs-20260702-20260702.xlsx"`
- body 为最小 OOXML XLSX 文件。

## 验收

- `backend/tests/test_admin_refund_api.py` 覆盖 XLSX 下载、筛选透传、管理员权限、只读 GET 无 CSRF、非法退款类型、日期范围错误、敏感字段不外泄、无公式节点、inline string 和 XML 控制字符清洗。
- `backend/tests/test_openapi_contract.py` 覆盖 OpenAPI 文件响应、`refundType` 枚举和 no-CSRF GET 列表。
- `scripts/verify-integration.sh` 作为最终回归门禁。

## 暂不做

- 异步大文件导出、导出历史和对象存储。
- 真实渠道退款流水号、退款通知和财务对账。
- 失败尝试审计、退款审批流和人工复核流。
