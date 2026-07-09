# 后台异步退款审计 XLSX 导出 worker 设计

## 背景

退款审计 CSV 已接入异步导出任务。为了让后台同一个退款审计异步导出入口支持 Excel 友好的文件，本切片补齐 `REFUND_AUDIT + XLSX`。

## 范围

- 支持内部 worker 处理一条 `REFUND_AUDIT + XLSX` pending 任务。
- 复用同步退款审计 XLSX 的字段、日期范围校验、退款类型归一化、筛选语义、公式注入防护和 XML 1.0 非法控制字符清洗。
- 支持 `refundType`、`orderNo`、`operatorUsername`、`dateFrom`、`dateTo` 五个已白名单 filters。
- 继续由后端派生 `storage_key` 和文件名，通过现有下载端点取回文件。

## 不做

- 不实现产品维度、趋势或其他报表异步生成。
- 不新增常驻队列、对象存储、重试、清理或生产级大文件传输。
- 不改变同步退款审计 XLSX 字段口径。

## 安全边界

- worker 只读取已白名单归一化的 filters；日期必须能解析为 `YYYY-MM-DD`，文本 filters 必须是字符串。
- `refundType` 继续复用同步退款审计枚举校验，只允许 `FULL` 或 `PARTIAL`。
- XLSX 内容复用 `AdminRefundService.to_refund_audit_logs_xlsx`，只包含退款审计安全字段，不返回完整手机号、证件号、session、CSRF、密码 hash、内部 id、`adminUserId`、支付流水号或渠道交易号。
- 单元格继续写成 inline string，不生成公式节点；危险公式前缀和前导空格后的危险公式前缀必须加单引号。
- 文本写入前继续清理 XML 1.0 非法控制字符，避免脏数据损坏工作簿。
- 不支持的其他导出类型仍标记为 `FAILED + ADMIN_EXPORT_JOB_UNSUPPORTED`，不能无限停留在 `RUNNING`。

## 验收

- `REFUND_AUDIT + XLSX` pending 任务会生成 `.xlsx` 文件并标记 `SUCCEEDED`。
- 文件名使用 `admin-refund-logs-<start>-<end>.xlsx`，未传日期时使用 `start` 或 `end`。
- DTO 不返回内部 `storageKey`。
- `REFUND_AUDIT + CSV` 路径保持不变。
- 其他未支持类型仍失败落库。
