# 后台异步月度趋势 CSV worker 设计

## 背景

日报和小时趋势已经支持异步 CSV/XLSX 生成，月度趋势同步 CSV 也已经固定了聚合字段、`includeEmpty` 补零口径和表格安全边界。前端异步导出任务流继续补齐月度趋势时，先接入 CSV 可以用最小改动打通长周期报表下载。

## 范围

- 支持单次 worker 处理一条 `MONTHLY_TREND + CSV` pending 任务。
- 复用同步月度趋势 CSV 的聚合字段、日期校验、`includeEmpty` 60 个月补零范围校验和公式注入防护。
- 文件名继续使用 `admin-monthly-trend-<start>-<end>.csv`，`storage_key` 仍由后端根据任务编号派生。
- 不实现 `MONTHLY_TREND + XLSX`、常驻队列、生产对象存储、重试或清理策略。

## 数据流

1. worker 原子领取最早的 `PENDING` 任务并切到 `RUNNING`。
2. 对 `MONTHLY_TREND + CSV` 读取已归一化的 `dateFrom`、`dateTo` 和 `includeEmpty` filters。
3. `AdminReportService.export_monthly_trend_csv_for_worker` 重新执行日期范围和补零范围校验，调用月度趋势 repository，转换 DTO，必要时补零，再生成 CSV。
4. worker 写入受控本地存储，并把任务标记为 `SUCCEEDED`。
5. 未支持的 `MONTHLY_TREND + XLSX` 仍标记为 `FAILED`，错误码为 `ADMIN_EXPORT_JOB_UNSUPPORTED`。

## 安全边界

- worker 不信任客户端传入的文件名或存储路径。
- 响应 DTO 不返回 `storageKey`。
- CSV 内容不导出完整手机号、证件号、session、CSRF、密码 hash、内部 id、SQL 或支付流水号。
- CSV 单元格继续复用表格安全函数，防止公式注入。

## 验收

- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_generates_monthly_trend_csv_and_marks_job_succeeded`
- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_marks_unsupported_jobs_failed`
- `backend/tests/test_backend_acceptance_report.py`
- `backend/tests/test_backend_milestone_status.py`
