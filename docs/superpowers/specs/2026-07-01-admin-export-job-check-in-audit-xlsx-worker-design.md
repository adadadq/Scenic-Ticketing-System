# 后台异步核销审计 XLSX 导出 worker 设计

## 背景

异步导出任务已经支持订单明细 CSV/XLSX 和核销审计 CSV。为了让前端同一个核销审计导出任务入口支持两种常用文件格式，本切片补齐 `CHECK_IN_AUDIT + XLSX`。

## 范围

- 支持内部 worker 处理一条 `CHECK_IN_AUDIT + XLSX` pending 任务。
- 复用同步核销审计 XLSX 的字段、日期范围校验、筛选语义、公式注入防护和 XML 1.0 非法控制字符清洗。
- 支持 `ticketCode`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo` 五个已白名单 filters。
- 继续由后端派生 `storage_key` 和文件名，通过现有下载端点取回文件。

## 不做

- 不实现核销失败审计、退款审计、产品维度或趋势异步生成。
- 不新增常驻队列、对象存储、重试、清理或生产级大文件传输。
- 不改变同步核销审计 XLSX 字段口径。

## 安全边界

- worker 只读取已白名单归一化的 filters；日期必须能解析为 `YYYY-MM-DD`，文本 filters 必须是字符串。
- XLSX 内容复用 `AdminCheckInService.to_check_in_audit_logs_xlsx`，只包含核销审计安全字段，不返回完整手机号、证件号、session、CSRF、密码 hash、内部 id、`adminUserId` 或 SQL。
- 单元格继续写成 inline string，不生成公式节点；危险公式前缀和前导空格后的危险公式前缀必须加单引号。
- 文本写入前继续清理 XML 1.0 非法控制字符，避免脏数据损坏工作簿。
- 不支持的其他导出类型仍标记为 `FAILED + ADMIN_EXPORT_JOB_UNSUPPORTED`，不能无限停留在 `RUNNING`。

## 验收

- `CHECK_IN_AUDIT + XLSX` pending 任务会生成 `.xlsx` 文件并标记 `SUCCEEDED`。
- 文件名使用 `admin-check-in-logs-<start>-<end>.xlsx`，未传日期时使用 `start` 或 `end`。
- DTO 不返回内部 `storageKey`。
- `ORDER_DETAIL + CSV/XLSX` 和 `CHECK_IN_AUDIT + CSV` 路径保持不变。
- 其他导出类型仍失败落库。
