# 后台异步日报趋势 CSV worker 设计

## 背景

同步日报趋势 CSV 已经支持日期筛选、`includeEmpty` 补零、聚合字段导出和 CSV 公式注入防护。异步导出任务也已经允许 `DAILY_TREND` 携带 `dateFrom`、`dateTo` 和 `includeEmpty` filters，但 worker 尚未生成日报趋势文件。

## 范围

- 支持单次 worker 处理一条 `DAILY_TREND + CSV` pending 任务。
- 复用同步日报趋势 CSV 的字段、日期校验、补零范围校验和公式注入防护。
- 由后端根据任务编号和文件名派生 `storage_key`，成功后标记 `SUCCEEDED`。
- 公开 DTO 继续不返回内部 `storageKey`。

## 非范围

- 不实现日报趋势 XLSX 异步导出。
- 不实现小时趋势或月度趋势异步导出。
- 不实现常驻队列、生产对象存储、重试、过期清理或大文件分片下载。

## 安全边界

- worker 只接受已持久化并归一化的 filters；`includeEmpty` 必须是布尔值。
- `includeEmpty=true` 时必须继续要求日期上下界，并限制日报补零范围不超过 366 天。
- 文件名和 `storage_key` 不信任前端输入，统一由后端派生。
- CSV 单元格继续复用统一表格安全函数，避免公式注入。

## 验收

- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_generates_daily_trend_csv_and_marks_job_succeeded`
- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_marks_unsupported_jobs_failed`
- `scripts/verify-backend.sh`
