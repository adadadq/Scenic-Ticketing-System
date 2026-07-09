# 后台异步核销审计 CSV 导出 worker 设计

## 背景

后台异步导出任务已经跑通订单明细 CSV/XLSX 的创建、领取、生成、落本地受控存储和下载闭环。前端管理台也会把核销审计日志作为导出任务提交，下一步先补 `CHECK_IN_AUDIT + CSV`，让运营可以在异步任务流里导出核销与撤销核销审计。

## 范围

- 支持内部 worker 处理一条 `CHECK_IN_AUDIT + CSV` pending 任务。
- 复用同步核销审计 CSV 的字段、日期范围校验、筛选语义和公式注入防护。
- 支持 `ticketCode`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo` 五个已白名单 filters。
- 继续由后端派生 `storage_key` 和文件名，通过现有下载端点取回文件。

## 不做

- 不实现 `CHECK_IN_AUDIT + XLSX`，它作为后续单独切片。
- 不实现核销失败审计、退款审计、产品维度或趋势异步生成。
- 不新增常驻队列、对象存储、重试、清理或生产级大文件传输。

## 安全边界

- worker 只读取已白名单归一化的 filters；日期必须能解析为 `YYYY-MM-DD`，文本 filters 必须是字符串。
- CSV 内容复用 `AdminCheckInService.to_check_in_audit_logs_csv`，只包含审计安全字段，不返回完整手机号、证件号、session、CSRF、密码 hash、内部 id、`adminUserId` 或 SQL。
- 所有 CSV 单元格继续做表格公式注入防护。
- 不支持的其他导出类型或格式仍标记为 `FAILED + ADMIN_EXPORT_JOB_UNSUPPORTED`，不能无限停留在 `RUNNING`。

## 验收

- `CHECK_IN_AUDIT + CSV` pending 任务会生成 `.csv` 文件并标记 `SUCCEEDED`。
- 文件名使用 `admin-check-in-logs-<start>-<end>.csv`，未传日期时使用 `start` 或 `end`。
- DTO 不返回内部 `storageKey`。
- `ORDER_DETAIL + CSV/XLSX` 路径保持不变。
- `CHECK_IN_AUDIT + XLSX` 和其他导出类型仍失败落库。
