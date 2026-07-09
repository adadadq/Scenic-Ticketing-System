# 后台退款审计日志 CSV 导出设计

## 背景

后台已经支持订单维度退款审计日志和全局退款审计检索。运营复盘时还需要把同一批检索结果下载到表格工具中留档、筛选和交叉核对。本切片只做轻量 CSV 导出，延续当前审计检索口径。

## 范围

- 新增 `GET /api/admin/refund-logs.csv`。
- 只接受管理员 session；未登录返回 `401 ADMIN_AUTH_REQUIRED`，游客 session 返回 `403 ADMIN_FORBIDDEN`。
- 这是只读 GET，不要求 CSRF header。
- 支持 `refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo` 查询参数，与 `GET /api/admin/refund-logs` 保持一致。
- CSV 使用 UTF-8 BOM，列固定为 `orderNo`、`refundType`、`refundedAmount`、`refundedItemCount`、`refundedItemNos`、`reason`、`operatorUsername`、`operatorDisplayName`、`requestId`、`createdAt`。
- 所有 CSV 单元格统一做公式注入防护。

## 不做

- XLSX 导出。
- 异步导出任务、导出历史或对象存储。
- 真实渠道退款流水号、退款通知或财务对账。
- 导出权限细分和下载审计日志。

## API 契约

成功响应不是统一 JSON 成功壳，而是 CSV 文件：

- `Content-Type: text/csv; charset=utf-8`
- `Content-Disposition: attachment; filename="admin-refund-logs-<start>-<end>.csv"`
- 未传日期时文件名使用 `start` 和 `end` 占位。

错误响应继续使用统一失败壳。非法 `refundType` 返回 `422 ADMIN_REFUND_LOG_TYPE_INVALID`；`dateFrom > dateTo` 返回 `422 ADMIN_REFUND_LOG_DATE_RANGE_INVALID`。

## 安全边界

- 权限：必须经过管理员 session 校验，游客 session 不能访问。
- CSRF：只读 GET 不要求 CSRF。
- DTO：CSV 不包含完整手机号、证件号、session token、CSRF token、密码 hash、数据库内部 id、`adminUserId` 或 SQL。
- CSV 注入：`=`、`+`、`-`、`@`、制表符、回车、换行或前导空格后危险字符开头的单元格前加单引号。
- SQL：筛选参数只进入参数绑定，不拼接进 SQL 字符串。

## 数据流

1. Router 接收查询参数并调用 `AdminRefundService`。
2. Service 校验管理员 session、标准化筛选参数和日期范围。
3. Repository 使用同一套审计日志 where 条件按 `created_at DESC, id DESC` 查询完整导出行。
4. Service 把行转换成 CSV 文本，票项号用分号拼接，并做 CSV 公式注入防护。
5. Router 返回文件响应。

## 验收

- 管理员可无 CSRF header 下载退款审计 CSV。
- 匿名和游客 session 无法下载。
- 筛选参数、非法退款类型和非法日期范围行为与全局检索一致。
- CSV 文件头、文件名、UTF-8 BOM 和列顺序稳定。
- CSV 不包含认证材料、内部 id 或个人敏感字段。
- 公式开头的审计字段不会原样作为公式进入 CSV。
- Postgres 查询使用参数绑定，且导出排序为 `created_at DESC, id DESC`。
- OpenAPI 声明该接口为 `text/csv` 文件响应。
