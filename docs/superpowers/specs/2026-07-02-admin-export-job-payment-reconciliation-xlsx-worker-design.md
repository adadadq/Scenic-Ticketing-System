# 异步支付对账 XLSX worker 设计

日期：2026-07-02

## 问题

后台支付对账已经支持同步 XLSX 下载，异步导出任务也已经支持 `PAYMENT_RECONCILIATION + CSV`。任务中心仍缺少 `PAYMENT_RECONCILIATION + XLSX`，导致运营想用统一异步任务下载表格文件时只能退回同步导出。

## 范围

- 内部 worker 支持 `PAYMENT_RECONCILIATION + XLSX`。
- `PAYMENT_RECONCILIATION.filters` 继续只允许 `dateFrom`、`dateTo`。
- 文件内容复用同步支付对账 XLSX 的单行汇总字段。
- 文件名使用现有 `admin-payment-reconciliation-<start>-<end>.xlsx` 规则。

## 决策

- 不新增 API、DTO、数据库字段或导出类型。
- worker 从内部完整 filters 读取日期，复用 worker 专用 service 方法生成 XLSX bytes。
- XLSX 安全边界沿用同步导出：inline string、无公式节点、XML 1.0 非法控制字符清洗、只输出对账汇总字段。
- 文件写入仍使用受控本地 storage，`storage_key` 由后端派生，公开 DTO 不返回。

## 非目标

- 不接真实支付渠道结算文件、手续费、税费或渠道退款通知。
- 不实现多 sheet 财务对账工作簿。
- 不改变同步支付对账 API、CSV/XLSX 字段和统计口径。
- 不改生产对象存储、外部队列、重试和清理策略。

## 验收

- worker 可处理 `PAYMENT_RECONCILIATION + XLSX` pending 任务，生成受控本地 `.xlsx` 文件并标记 `SUCCEEDED`。
- 日期 filters 会传入支付对账导出口径。
- CSV 路径保持不回归。
- 未知导出类型或格式仍按 unsupported 失败落库。
