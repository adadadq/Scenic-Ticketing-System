# 后台异步月度趋势 XLSX worker 设计

## 背景

`MONTHLY_TREND + CSV` 已经接入内部异步导出 worker。同步月度趋势 XLSX 已经固定聚合字段、`includeEmpty` 补零口径、inline string、无公式节点和 XML 1.0 非法控制字符清洗，可以继续复用到异步任务流。

## 范围

- 支持单次 worker 处理一条 `MONTHLY_TREND + XLSX` pending 任务。
- 复用同步月度趋势 XLSX 的聚合字段、日期校验、`includeEmpty` 60 个月补零范围校验、inline string、无公式节点和 XML 1.0 非法控制字符清洗。
- 文件名继续使用 `admin-monthly-trend-<start>-<end>.xlsx`，`storage_key` 仍由后端根据任务编号派生。
- 不实现常驻队列、生产对象存储、重试或清理策略。

## 数据流

1. worker 原子领取最早的 `PENDING` 任务并切到 `RUNNING`。
2. 对 `MONTHLY_TREND + XLSX` 读取已归一化的 `dateFrom`、`dateTo` 和 `includeEmpty` filters。
3. `AdminReportService.export_monthly_trend_xlsx_for_worker` 重新执行日期范围和补零范围校验，调用月度趋势 repository，转换 DTO，必要时补零，再生成 XLSX。
4. worker 写入受控本地存储，并把任务标记为 `SUCCEEDED`。
5. 异常任务元数据中的未知导出类型仍标记为 `FAILED`，错误码为 `ADMIN_EXPORT_JOB_UNSUPPORTED`。

## 安全边界

- worker 不信任客户端传入的文件名或存储路径。
- 响应 DTO 不返回 `storageKey`。
- XLSX 内容不导出完整手机号、证件号、session、CSRF、密码 hash、内部 id、SQL 或支付流水号。
- XLSX 单元格继续写成 inline string，不生成公式节点，并清洗 XML 1.0 非法控制字符。

## 验收

- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_generates_monthly_trend_xlsx_and_marks_job_succeeded`
- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_marks_unsupported_jobs_failed`
- `backend/tests/test_backend_acceptance_report.py`
- `backend/tests/test_backend_milestone_status.py`
