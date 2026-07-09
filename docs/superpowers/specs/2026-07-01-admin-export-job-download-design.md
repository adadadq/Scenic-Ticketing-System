# 后台异步导出文件下载端点设计

## 问题

异步导出任务已经支持登记、查询和 worker 状态流转，但管理员还不能通过稳定接口下载 worker 已经写入 `file_name` 和内部 `storage_key` 的文件。

## 边界

- 新增 `GET /api/admin/export-jobs/{job_id}/download`。
- 只接受管理员 session；这是只读 GET，不要求 CSRF header。
- 只有状态为 `SUCCEEDED` 且存在 `file_name`、`storage_key` 的任务可以下载。
- 成功响应是文件流，不包 `ApiSuccessDTO`。
- CSV 返回 `text/csv; charset=utf-8`；XLSX 返回 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`。
- `storage_key` 只在服务端内部使用，不进入公开 DTO、OpenAPI DTO 或响应 JSON。
- 当前只读取已存在的本地导出文件，不实现文件生成、对象存储、重试、清理或生产级大文件分片下载。

## 安全约束

- `storage_key` 必须解析到配置的 `ADMIN_EXPORT_STORAGE_DIR` 内，拒绝 `../` 或绝对路径穿越。
- 下载响应的 `Content-Disposition` 文件名不能包含换行、回车或双引号；非 ASCII 文件名必须通过 `filename*` 使用 UTF-8 百分号编码，避免响应头编码异常。
- 数据库查询使用 `job_id = %s` 参数绑定，不拼接任务编号或存储路径。
- 未生成或元数据不完整返回 `409 ADMIN_EXPORT_JOB_FILE_NOT_READY`。
- 文件元数据存在但物理文件缺失返回 `404 ADMIN_EXPORT_FILE_NOT_FOUND`。

## 验收

- 管理员可无 CSRF 下载成功任务文件。
- 匿名和游客不能下载。
- 未成功任务不能下载。
- 文件缺失和路径穿越有明确错误，并且错误响应不暴露真实文件路径。
- OpenAPI 声明文件响应和 `Content-Disposition` header。
