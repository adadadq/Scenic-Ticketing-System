# 后台异步退款审计 CSV 导出 worker 设计

## 背景

异步导出任务已经支持订单明细、核销审计和核销失败审计。退款审计已经有同步 CSV/XLSX 导出和 `REFUND_AUDIT` filters 白名单，本切片先补齐 `REFUND_AUDIT + CSV`，让后台退款留档可以走同一套异步任务与下载链路。

## 范围

- 支持内部 worker 处理一条 `REFUND_AUDIT + CSV` pending 任务。
- 复用同步退款审计 CSV 的字段、日期范围校验、退款类型归一化、筛选语义和公式注入防护。
- 支持 `refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo` 五个已白名单 filters。
- 继续由后端派生 `storage_key` 和文件名，通过现有下载端点取回文件。

## 不做

- 不在本 CSV 切片实现 `REFUND_AUDIT + XLSX`；XLSX 已由后续独立切片补齐。
- 不实现产品维度、趋势或其他报表异步生成。
- 不新增常驻队列、对象存储、重试、清理或生产级大文件传输。
- 不改变同步退款审计 CSV 字段口径。

## 安全边界

- worker 只读取已白名单归一化的 filters；日期必须能解析为 `YYYY-MM-DD`，文本 filters 必须是字符串。
- `refundType` 继续复用同步退款审计枚举校验，只允许 `FULL` 或 `PARTIAL`。
- CSV 内容复用 `AdminRefundService.to_refund_audit_logs_csv`，只包含退款审计安全字段，不返回完整手机号、证件号、session、CSRF、密码 hash、内部 id、`adminUserId`、支付流水号或渠道交易号。
- 所有单元格继续做 CSV 公式注入防护。
- 不支持的其他导出类型或格式仍标记为 `FAILED + ADMIN_EXPORT_JOB_UNSUPPORTED`，不能无限停留在 `RUNNING`。

## 验收

- `REFUND_AUDIT + CSV` pending 任务会生成 `.csv` 文件并标记 `SUCCEEDED`。
- 文件名使用 `admin-refund-logs-<start>-<end>.csv`，未传日期时使用 `start` 或 `end`。
- DTO 不返回内部 `storageKey`。
- `ORDER_DETAIL + CSV/XLSX`、`CHECK_IN_AUDIT + CSV/XLSX` 和 `CHECK_IN_FAILURE_AUDIT + CSV/XLSX` 路径保持不变。
- 其他未支持类型仍失败落库；`REFUND_AUDIT + XLSX` 已由后续独立切片补齐。
