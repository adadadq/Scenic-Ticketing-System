# 后台异步小时趋势 XLSX worker 设计

## 背景

小时趋势 CSV 已经接入异步导出任务。同步小时趋势 XLSX 已经固定聚合字段、`includeEmpty` 补零口径、表格安全边界和文件命名规则，可以继续复用到异步任务。

## 范围

- 支持单次 worker 处理一条 `HOURLY_TREND + XLSX` pending 任务。
- 复用同步小时趋势 XLSX 的字段、日期校验、补零范围校验、inline string、无公式节点和 XML 1.0 非法控制字符清洗。
- 由后端根据任务编号和文件名派生 `storage_key`，成功后标记 `SUCCEEDED`。
- 公开 DTO 继续不返回内部 `storageKey`。

## 非范围

- 不实现月度趋势异步导出。
- 不实现常驻队列、生产对象存储、重试、过期清理或大文件分片下载。

## 安全边界

- worker 只接受已持久化并归一化的 filters；`includeEmpty` 必须是布尔值。
- `includeEmpty=true` 时必须继续要求日期上下界，并限制小时趋势补零范围不超过 31 天。
- 文件名和 `storage_key` 不信任前端输入，统一由后端派生。
- XLSX 单元格继续写成 inline string，不生成公式节点，并清理 XML 1.0 非法控制字符。

## 验收

- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_generates_hourly_trend_xlsx_and_marks_job_succeeded`
- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_marks_unsupported_jobs_failed`
- `scripts/verify-backend.sh`
