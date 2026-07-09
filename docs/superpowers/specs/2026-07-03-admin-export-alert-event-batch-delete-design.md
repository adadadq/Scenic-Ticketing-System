# 后台异步导出告警事件批量删除 API 设计

日期：2026-07-03

## 问题

单条删除已关闭告警事件已经可用，但后台页面如果支持多选清理，逐条调用会增加前端状态处理和请求数量。这个切片只补后端批量入口，不新增真实外部通知、跨任务聚合、静默窗口或前端页面。

## 范围

- 新增管理员 `POST /api/admin/export-job-alert-events/batch-delete`。
- 请求体为 `{ "eventIds": [1, 2, 3] }`，至少 1 项、最多 100 项，事件 id 必须为正整数，不允许重复或额外字段。
- 只允许删除已关闭告警事件。未关闭事件和不存在事件作为逐项业务失败返回，不影响同批其他事件。
- 不新增数据库表或迁移，复用单条删除仓储方法里的 `closed_at IS NOT NULL` 条件。

## API 和 DTO

成功响应仍使用统一成功壳，`data` 为：

```json
{
  "totalCount": 3,
  "successCount": 1,
  "failureCount": 2,
  "results": [
    { "eventId": 1, "deleted": true },
    {
      "eventId": 2,
      "deleted": false,
      "code": "ADMIN_EXPORT_JOB_ALERT_EVENT_DELETE_NOT_ALLOWED",
      "message": "只有已关闭的导出任务告警事件可以删除"
    },
    {
      "eventId": 404,
      "deleted": false,
      "code": "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND",
      "message": "导出任务告警事件不存在"
    }
  ]
}
```

## 权限和安全

- 只接受管理员 session；匿名返回 `ADMIN_AUTH_REQUIRED`，游客 session 返回 `ADMIN_FORBIDDEN`。
- 状态变更接口必须携带 session-bound CSRF header。
- 响应不返回 `filters`、`storage_key`、本机路径、SQL、堆栈、session、CSRF token 或内部管理员 id。
- 单项删除继续使用参数化 SQL，且删除条件必须包含 `closed_at IS NOT NULL`。

## 验收

```bash
python3 -m py_compile backend/app/api/admin_exports.py backend/app/main.py backend/app/schemas/admin_exports.py backend/app/services/admin_exports.py
.venv/bin/pytest backend/tests/test_admin_export_jobs_api.py::test_admin_can_batch_delete_closed_export_job_alert_events_with_per_item_results backend/tests/test_admin_export_jobs_api.py::test_export_job_alert_event_batch_delete_rejects_duplicate_empty_and_extra_fields backend/tests/test_admin_export_jobs_api.py::test_export_job_alert_event_batch_delete_requires_admin_and_csrf backend/tests/test_openapi_contract.py::test_openapi_documents_success_wrapper_and_frontend_dtos backend/tests/test_openapi_contract.py::test_openapi_documents_csrf_header_as_required_for_state_changing_endpoints backend/tests/test_openapi_contract.py::test_openapi_uses_configured_csrf_header_name
scripts/verify-backend.sh
```
