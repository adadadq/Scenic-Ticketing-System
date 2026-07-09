# 后台异步导出告警事件批量关闭 API 设计

日期：2026-07-03

## 问题

单条关闭 API 已经能把不再活跃展示的内部告警关闭。前端管理台如果支持多选关闭，需要一个批量入口，避免逐条请求和复杂的局部失败状态管理。

## 范围

- 新增管理员 `POST /api/admin/export-job-alert-events/batch-close`。
- 请求体为 `{ "eventIds": [1, 2], "note": "已处理" }`，`eventIds` 至少 1 项、最多 100 项，必须是不重复正整数；`note` 可选，trim 后空白视为 `null`，最大 200 字符；拒绝额外字段和 snake_case 字段。
- 逐项复用单条关闭逻辑：未关闭事件写入关闭人、关闭时间和备注；已关闭事件返回成功但不覆盖第一次关闭记录；不存在事件作为逐项失败返回。
- 不新增数据库表或迁移。

## API 和 DTO

成功响应仍使用统一成功壳，`data` 为：

```json
{
  "totalCount": 3,
  "successCount": 2,
  "failureCount": 1,
  "results": [
    { "eventId": 1, "closed": true },
    { "eventId": 2, "closed": true },
    {
      "eventId": 404,
      "closed": false,
      "code": "ADMIN_EXPORT_JOB_ALERT_EVENT_NOT_FOUND",
      "message": "导出任务告警事件不存在"
    }
  ]
}
```

## 权限和安全

- 只接受管理员 session；匿名返回 `ADMIN_AUTH_REQUIRED`，游客 session 返回 `ADMIN_FORBIDDEN`。
- 状态变更接口必须携带 session-bound CSRF header。
- 前端不能提交 `adminUserId`、关闭时间、关闭人或内部字段。
- 响应不返回 `filters`、`storage_key`、本机路径、SQL、堆栈、session、CSRF token 或内部管理员 id。

## 验收

```bash
python3 -m py_compile backend/app/api/admin_exports.py backend/app/main.py backend/app/schemas/admin_exports.py backend/app/services/admin_exports.py
.venv/bin/pytest backend/tests/test_admin_export_jobs_api.py::test_admin_can_batch_close_export_job_alert_events_with_per_item_results backend/tests/test_admin_export_jobs_api.py::test_export_job_alert_event_batch_close_rejects_duplicate_empty_extra_and_bad_note backend/tests/test_admin_export_jobs_api.py::test_export_job_alert_event_batch_close_requires_admin_and_csrf backend/tests/test_openapi_contract.py::test_openapi_documents_success_wrapper_and_frontend_dtos backend/tests/test_openapi_contract.py::test_openapi_documents_admin_export_alert_event_note_limits backend/tests/test_openapi_contract.py::test_openapi_documents_csrf_header_as_required_for_state_changing_endpoints backend/tests/test_openapi_contract.py::test_openapi_uses_configured_csrf_header_name
scripts/verify-backend.sh
```
