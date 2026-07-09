# 异步支付对账 CSV worker 设计

日期：2026-07-02

## 问题

后台支付对账汇总已经支持同步 CSV/XLSX 下载，但异步导出任务还不能处理支付对账。运营在日期范围较大或希望统一从任务中心下载报表时，缺少 `PAYMENT_RECONCILIATION + CSV` 的 worker 支撑。

## 范围

- `POST /api/admin/export-jobs` 新增 `PAYMENT_RECONCILIATION` 任务类型。
- `PAYMENT_RECONCILIATION.filters` 只允许 `dateFrom`、`dateTo`。
- 内部 worker 支持 `PAYMENT_RECONCILIATION + CSV`。
- `admin_export_job` 类型约束和旧库迁移补齐 `PAYMENT_RECONCILIATION`。

## 决策

- CSV 内容复用同步支付对账 CSV 的单行汇总口径，不新增字段。
- 日期 filter 复用异步导出任务现有 `YYYY-MM-DD`、日期倒挂校验和 worker 二次校验。
- worker 从完整内部 filters 读取日期，调用报表 service 的 worker 专用方法生成 CSV。
- 文件名和 `storage_key` 仍由后端派生，成功后标记 `SUCCEEDED`。
- `PAYMENT_RECONCILIATION + XLSX` 本切片暂不支持，仍按现有 unsupported 机制标记 `FAILED`。

## 非目标

- 不接真实支付渠道结算文件、手续费或渠道退款通知。
- 不改变同步支付对账 API 的统计口径。
- 不在本切片实现支付对账 XLSX worker。

## 验收

- 管理员可创建 `PAYMENT_RECONCILIATION + CSV` 异步导出任务，filters 只保留合法日期。
- worker 可生成受控本地 CSV 文件，任务状态变为 `SUCCEEDED`，公开 DTO 不返回 `storageKey`。
- `PAYMENT_RECONCILIATION + XLSX` 暂不支持时必须失败落库，不能停留在 `RUNNING`。
- schema 和迁移都包含 `PAYMENT_RECONCILIATION` 类型约束。
