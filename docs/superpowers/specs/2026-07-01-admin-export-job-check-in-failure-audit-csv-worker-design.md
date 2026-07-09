# 后台异步核销失败审计 CSV 导出 worker 设计

## 背景

异步导出任务已经支持订单明细 CSV/XLSX 和核销审计 CSV/XLSX。核销失败审计记录了核销与撤销核销的业务失败尝试，是运营排查和安全复盘常用导出。本切片先补齐 `CHECK_IN_FAILURE_AUDIT + CSV`，继续沿用单次 worker 模式。

## 范围

- 支持内部 worker 处理一条 `CHECK_IN_FAILURE_AUDIT + CSV` pending 任务。
- 复用同步核销失败审计 CSV 的字段、日期范围校验、失败码归一化、筛选语义和公式注入防护。
- 支持 `ticketCode`、`failureCode`、`operatorUsername`、`dateFrom`、`dateTo` 五个已白名单 filters。
- 继续由后端派生 `storage_key` 和文件名，通过现有下载端点取回文件。

## 不做

- 不在本 CSV 切片内实现 `CHECK_IN_FAILURE_AUDIT + XLSX`；XLSX 已由后续单独切片补齐。
- 不实现退款审计、产品维度或趋势异步生成。
- 不新增常驻队列、对象存储、重试、清理或生产级大文件传输。
- 不改变同步核销失败审计 CSV 字段口径。

## 安全边界

- worker 只读取已白名单归一化的 filters；日期必须能解析为 `YYYY-MM-DD`，文本 filters 必须是字符串。
- `failureCode` 继续复用同步核销失败审计枚举校验，只允许已知核销/撤销核销业务失败码。
- CSV 内容复用 `AdminCheckInService.to_check_in_failure_audit_logs_csv`，只包含核销失败审计安全字段，不返回完整手机号、证件号、session、CSRF、密码 hash、内部 id、`adminUserId` 或 SQL。
- CSV 单元格继续做公式注入防护。
- 不支持的其他导出类型或格式仍标记为 `FAILED + ADMIN_EXPORT_JOB_UNSUPPORTED`，不能无限停留在 `RUNNING`。

## 验收

- `CHECK_IN_FAILURE_AUDIT + CSV` pending 任务会生成 `.csv` 文件并标记 `SUCCEEDED`。
- 文件名使用 `admin-check-in-failure-logs-<start>-<end>.csv`，未传日期时使用 `start` 或 `end`。
- DTO 不返回内部 `storageKey`。
- `ORDER_DETAIL + CSV/XLSX`、`CHECK_IN_AUDIT + CSV/XLSX` 路径保持不变。
- 其他未支持类型仍失败落库。
