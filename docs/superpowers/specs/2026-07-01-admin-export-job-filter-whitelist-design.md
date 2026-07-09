# 后台异步导出任务 filters 白名单设计

## 问题

后台异步导出任务基础已经支持创建 `PENDING` 任务，但 `filters` 仍是任意 JSON。后续 worker 会根据任务元数据生成 CSV/XLSX，如果现在不固定每类导出的筛选字段，前端可能提交无效字段、过长文本或敏感客户端控制字段，后续生成文件时会扩大安全和联调成本。

## 范围

- 创建任务时按 `exportType` 校验 `filters` 白名单。
- 接受并归一化日期、短文本、枚举和布尔字段。
- 保留已有 `filters` 总大小限制和额外顶层字段拒绝。
- 不实现 worker、队列、文件生成、对象存储、下载链接或任务重试。

## filters 约定

- `ORDER_DETAIL`、`PRODUCT_BREAKDOWN`：允许 `dateFrom`、`dateTo`。
- `DAILY_TREND`、`HOURLY_TREND`、`MONTHLY_TREND`：允许 `dateFrom`、`dateTo`、`includeEmpty`。
- `CHECK_IN_AUDIT`：允许 `ticketCode`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo`。
- `CHECK_IN_FAILURE_AUDIT`：允许 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo`。
- `REFUND_AUDIT`：允许 `refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo`。

日期必须是 `YYYY-MM-DD` 且 `dateFrom <= dateTo`。短文本字段会 trim，空字符串会被丢弃，长度不超过 64；`failureCode` 长度不超过 40 并归一化为大写；`refundType` 只允许 `FULL` 或 `PARTIAL`。`includeEmpty` 只允许布尔值或 `true/false` 字符串，并归一化为布尔值。

## 错误和安全

- 未知字段、类型不匹配、非法日期、非法枚举或日期倒挂统一返回 `422 ADMIN_EXPORT_JOB_FILTERS_INVALID`。
- 响应 DTO 只回显归一化后的公开 filters，不返回内部 id、`storage_key`、`requested_by_admin_user_id`、session、CSRF、SQL 或文件路径。
- GET 列表/详情仍只要求管理员 session，不要求 CSRF；POST 仍要求管理员 session 和 session-bound CSRF。

## 验收

- `backend/tests/test_admin_export_jobs_api.py` 覆盖有效 filters 归一化、未知字段、非法日期、非法枚举、非法布尔和过长文本。
- `backend/tests/test_openapi_contract.py`、`backend/tests/test_backend_milestone_status.py`、`backend/tests/test_backend_acceptance_report.py` 覆盖契约和证据文档。
- `scripts/verify-backend.sh` 继续通过。
