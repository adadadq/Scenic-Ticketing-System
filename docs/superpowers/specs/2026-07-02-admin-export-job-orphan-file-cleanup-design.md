# 后台异步导出本地孤儿文件补偿清理设计

## 背景

后台异步导出 worker 生成文件时，顺序是先把内容写入受控本地存储，再把任务标记为 `SUCCEEDED` 并记录文件名与内部 `storage_key`。如果文件已经写出，但成功落库返回 `None` 或抛出异常，刚生成的文件不会被任务元数据引用，后续过期成功任务清理也无法发现它，形成本地孤儿文件。

## 范围

- `AdminExportJobWorkerService.write_file_and_mark_succeeded` 在写出文件后，如果 `mark_export_job_succeeded` 返回 `None`，必须尽力删除刚生成的 `storage_key`。
- 如果 `mark_export_job_succeeded` 抛出异常，必须先尽力删除刚生成的 `storage_key`，再保留原异常向外抛出。
- 补偿删除失败不能掩盖原始落库失败；worker 后续失败标记、自动重试或最终失败语义继续由既有状态机处理。
- Postgres 仓储必须在数据库连接上下文退出前完成成功返回行转换，避免数据库已经提交 `SUCCEEDED + storage_key` 后才抛出转换异常，导致外层误删成功任务文件。
- 正常成功落库时必须保留生成文件和任务元数据，不能误删已成功导出文件。
- 本切片不改变公开 API、DTO 字段、OpenAPI 契约或前端调用方式。

## 非目标

- 不扫描历史孤儿文件。
- 不把数据库事务和本地文件系统做强事务绑定。
- 不接入生产对象存储生命周期、外部队列、分布式租约或跨节点垃圾回收。
- 不改变过期 `SUCCEEDED` 文件清理脚本的清理范围。

## 安全边界

- 要删除的 `storage_key` 只来自后端按任务编号和文件名派生的内部值，不接受客户端输入。
- 公开 DTO 仍不返回 `storage_key`，前端也不能提交或覆盖存储路径。
- 实际文件删除继续通过 `AdminExportFileStorage.delete_file` 和 `resolve_storage_key` 限制在 `ADMIN_EXPORT_STORAGE_DIR` 内，路径穿越仍被拒绝。
- 补偿删除只处理刚写出的文件，不扩大为目录扫描或通配删除。

## 验收

- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_deletes_generated_file_when_success_mark_returns_none` 覆盖成功落库返回 `None` 时删除刚生成文件。
- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_deletes_generated_file_when_success_mark_raises` 覆盖成功落库抛异常时删除刚生成文件并保留原异常。
- `backend/tests/test_admin_export_jobs_api.py::test_postgres_export_job_success_row_conversion_happens_before_connection_exit` 覆盖 Postgres 成功返回行转换发生在连接上下文退出前。
- `backend/tests/test_admin_export_jobs_api.py::test_export_job_worker_generates_order_detail_csv_and_marks_job_succeeded` 覆盖正常成功路径仍保留文件和任务元数据。
