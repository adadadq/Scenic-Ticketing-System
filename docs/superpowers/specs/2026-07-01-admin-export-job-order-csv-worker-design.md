# 后台异步订单明细 CSV 导出 worker 设计

## 问题

异步导出任务已经支持创建、领取、状态流转和下载已生成文件，但还没有任何后端 worker 真的把任务生成成文件，前端只能看到任务停留在 `PENDING/RUNNING` 或下载已有测试文件。

## 本切片目标

- 增加内部 worker 服务，单次处理一条 `PENDING` 导出任务。
- 首个支持类型为 `ORDER_DETAIL + CSV`。
- 复用同步订单 CSV 导出的表头、脱敏、公式注入防护和日期校验。
- 生成文件写入 `ADMIN_EXPORT_STORAGE_DIR` 下的受控本地路径。
- 处理成功后把任务标记为 `SUCCEEDED`，写入 `file_name` 和内部 `storage_key`。
- 暂不支持的导出类型或格式标记为 `FAILED`，错误码为 `ADMIN_EXPORT_JOB_UNSUPPORTED`。
- 提供 `scripts/process-admin-export-job.py`，用于本地或部署环境单次处理一条任务。

## 非目标

- 不做常驻队列、调度器、并发 worker 池或重试。
- 不做 XLSX、核销、退款、产品维度或趋势异步生成。
- 不接生产对象存储，不做文件过期清理。
- 不新增公共 HTTP worker 触发接口。

## 安全约束

- worker 只能通过仓储的 `claim_next_pending_job()` 原子领取任务，继续复用行锁边界。
- `storage_key` 由后端根据 `job_id` 和生成文件名派生，不能来自前端。
- 写文件必须经过 `AdminExportFileStorage.resolve_storage_key()`，确保路径在 `ADMIN_EXPORT_STORAGE_DIR` 内。
- 订单 CSV 内容继续复用 `AdminReportService` 的手机号脱敏和 spreadsheet 公式前缀防护。
- worker 异常写入统一失败码，不把 SQL、文件路径、堆栈或异常文本写给前端。
- 单次处理脚本在 build/claim 阶段异常时也必须输出固定错误 JSON，不打印 Python traceback。

## 验收

- `ORDER_DETAIL + CSV` pending 任务会生成 CSV 文件并标记 `SUCCEEDED`。
- 生成后的任务可通过既有下载端点下载。
- `ORDER_DETAIL + XLSX` 等未支持任务会标记 `FAILED`，不会无限停留在 `RUNNING`。
- 无 pending 任务时 worker 返回空结果。
- 单次处理脚本输出 JSON，说明是否处理了任务和处理后的公开任务 DTO。
