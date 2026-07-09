# 后台异步导出任务基础设计

## 问题

同步 CSV/XLSX 导出已经有 `SYNC_EXPORT_ROW_LIMIT` 保护，但超过上限后只能提示用户缩小筛选范围。下一步需要为大文件导出提供稳定任务流，让前端可以先创建任务、查询任务状态，后续再接真正的后台 worker、文件存储和下载链接。

## 范围

- 新增 `admin_export_job` 数据表和幂等迁移，记录任务编号、导出类型、文件格式、筛选条件、状态、创建管理员、错误码、文件名和完成时间。
- 新增管理端 API：
  - `POST /api/admin/export-jobs` 创建异步导出任务。
  - `GET /api/admin/export-jobs` 分页查看当前任务。
  - `GET /api/admin/export-jobs/{job_id}` 查看任务详情。
- 本切片只创建 `PENDING` 任务，不生成文件、不启动后台 worker、不提供下载链接。
- 允许任务类型覆盖已存在的多行导出：订单明细、核销审计、核销失败审计、退款审计、产品维度、日报趋势、小时趋势、月度趋势。
- 文件格式仅允许 `CSV`、`XLSX`。

## 安全和契约

- 创建任务是状态变更，必须是管理员 session 且通过 CSRF。
- 列表和详情是只读 GET，不要求 CSRF，但必须是管理员 session。
- 请求体拒绝额外字段；前端不能提交 `adminUserId`、内部数据库 id、文件路径或状态。
- `filters` 只允许 JSON object，并限制序列化后大小，避免把大对象写入数据库。
- 响应 DTO 不返回存储路径、完整手机号、证件号、session token、CSRF token、密码 hash 或数据库内部 id；只返回 `jobId` 作为公开任务标识。
- 不存在的任务返回 `404 ADMIN_EXPORT_JOB_NOT_FOUND`；非法任务类型或格式由 DTO 校验走统一 `422 VALIDATION_ERROR`。

## 验收

- `backend/tests/test_admin_export_jobs_api.py` 覆盖创建、列表、详情、权限、CSRF、额外字段拒绝、过滤条件大小限制和 SQL 参数绑定。
- `backend/tests/test_openapi_contract.py` 覆盖新接口进入 OpenAPI 和创建任务 CSRF header。
- `backend/tests/test_schema_contract.py` 覆盖 schema 和迁移。
- `scripts/verify-backend.sh` 作为提交前后端验收入口。
