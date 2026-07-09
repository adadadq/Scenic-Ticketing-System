from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "docs" / "backend-acceptance-report.md"
README_PATH = PROJECT_ROOT / "README.md"
DECISION_LOG_PATH = PROJECT_ROOT / "docs" / "decision-log.md"


def test_backend_acceptance_report_tracks_phase8_evidence_and_boundaries():
    report = REPORT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "scripts/verify-integration.sh",
        "scripts/verify-backend.sh",
        "backend/tests/test_visitor_flow_api.py",
        "backend/tests",
        "680 passed",
        "scripts/export-openapi.py",
        "paths",
        "components.schemas",
        "npm run lint",
        "npm run build",
        "Vite",
        "chunk",
        "500 kB",
        "不影响当前后端 API 验收",
        "docs/backend-security-audit.md",
        "backend/tests/test_frontend_endpoint_contract.py",
        "docs/backend-milestone-status.md",
        "docs/superpowers/specs/2026-06-30-admin-auth-foundation-design.md",
        "backend/tests/test_admin_auth_api.py",
        "管理员权限基座已实现",
        "docs/superpowers/specs/2026-07-02-disabled-admin-session-boundary-design.md",
        "禁用管理员既有 session 边界已实现",
        "服务端 session 撤销",
        "docs/superpowers/specs/2026-06-30-admin-order-read-model-design.md",
        "backend/tests/test_admin_orders_api.py",
        "后台订单只读 API 已实现",
        "docs/superpowers/specs/2026-06-30-admin-check-in-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "后台票码核销 API 已实现",
        "docs/superpowers/specs/2026-06-30-admin-batch-check-in-design.md",
        "后台批量核销 API 已实现",
        "docs/superpowers/specs/2026-06-30-admin-undo-check-in-design.md",
        "后台撤销核销 API 已实现",
        "`UNDO_CHECK_IN` 审计",
        "docs/superpowers/specs/2026-06-30-admin-batch-undo-check-in-design.md",
        "后台批量撤销核销 API 已实现",
        "系统异常不伪装成逐票结果",
        "docs/superpowers/specs/2026-07-01-admin-undo-check-in-reason-audit-design.md",
        "database/migrations/2026-07-01-add-check-in-audit-log-reason.sql",
        "撤销核销原因审计已实现",
        "成功撤销审计 reason",
        "docs/superpowers/specs/2026-06-30-admin-check-in-audit-log-design.md",
        "核销审计日志已实现",
        "审计写入异常交给连接事务回滚",
        "docs/superpowers/specs/2026-07-01-admin-check-in-failure-audit-log-design.md",
        "database/migrations/2026-07-01-add-check-in-failure-audit-log.sql",
        "核销失败尝试审计已实现",
        "迁移 SQL",
        "单张/批量核销业务失败写入",
        "docs/superpowers/specs/2026-07-01-admin-undo-check-in-failure-audit-log-design.md",
        "database/migrations/2026-07-01-extend-check-in-failure-audit-log-for-undo.sql",
        "撤销核销失败尝试审计已实现",
        "单张/批量撤销业务失败写入",
        "docs/superpowers/specs/2026-07-01-admin-check-in-failure-audit-log-export-design.md",
        "核销/撤销失败尝试审计 CSV 导出已实现",
        "非法失败码",
        "OpenAPI 文件响应",
        "docs/superpowers/specs/2026-07-01-admin-check-in-failure-audit-log-xlsx-export-design.md",
        "核销/撤销失败尝试审计 XLSX 导出已实现",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "docs/superpowers/specs/2026-06-30-admin-check-in-audit-log-search-design.md",
        "核销审计日志检索已实现",
        "docs/superpowers/specs/2026-07-02-admin-check-in-audit-reason-filter-design.md",
        "核销审计日志原因筛选已实现",
        "公开 filters 脱敏",
        "docs/superpowers/specs/2026-06-30-admin-check-in-audit-log-export-design.md",
        "核销审计日志 CSV 导出已实现",
        "docs/superpowers/specs/2026-06-30-admin-check-in-audit-log-xlsx-export-design.md",
        "核销审计日志 XLSX 导出已实现",
        "docs/superpowers/specs/2026-06-30-admin-full-refund-design.md",
        "backend/tests/test_admin_refund_api.py",
        "后台全单模拟退款 API 已实现",
        "docs/superpowers/specs/2026-06-30-admin-partial-refund-design.md",
        "后台部分模拟退款 API 已实现",
        "docs/superpowers/specs/2026-07-02-admin-refund-super-admin-boundary-design.md",
        "退款写操作 SUPER_ADMIN 边界已实现",
        "docs/superpowers/specs/2026-06-30-admin-refund-audit-log-design.md",
        "退款审计日志已实现",
        "backend/tests/test_schema_contract.py",
        "docs/superpowers/specs/2026-06-30-admin-refund-audit-log-search-design.md",
        "退款审计日志检索已实现",
        "docs/superpowers/specs/2026-06-30-admin-refund-audit-log-export-design.md",
        "退款审计日志 CSV 导出已实现",
        "docs/superpowers/specs/2026-06-30-admin-refund-audit-log-xlsx-export-design.md",
        "退款审计日志 XLSX 导出已实现",
        "docs/superpowers/specs/2026-06-30-admin-report-summary-design.md",
        "backend/tests/test_admin_reports_api.py",
        "后台运营汇总报表 API 已实现",
        "docs/superpowers/specs/2026-07-01-admin-payment-reconciliation-report-design.md",
        "后台支付对账汇总 API 已实现",
        "`SUCCESS/REFUNDED` 支付记录口径",
        "docs/superpowers/specs/2026-07-01-admin-payment-reconciliation-csv-export-design.md",
        "后台支付对账汇总 CSV 导出已实现",
        "OpenAPI 文件响应",
        "docs/superpowers/specs/2026-07-01-admin-payment-reconciliation-xlsx-export-design.md",
        "后台支付对账汇总 XLSX 导出已实现",
        "inline string",
        "docs/superpowers/specs/2026-06-30-admin-product-breakdown-report-design.md",
        "后台产品维度报表 API 已实现",
        "docs/superpowers/specs/2026-07-01-admin-product-breakdown-csv-export-design.md",
        "后台产品维度报表 CSV 导出已实现",
        "docs/superpowers/specs/2026-07-01-admin-product-breakdown-xlsx-export-design.md",
        "后台产品维度报表 XLSX 导出已实现",
        "XML 1.0 非法控制字符清洗",
        "docs/superpowers/specs/2026-06-30-admin-daily-trend-report-design.md",
        "后台日报趋势报表 API 已实现",
        "docs/superpowers/specs/2026-07-01-admin-hourly-trend-report-design.md",
        "后台小时趋势报表 API 已实现",
        "docs/superpowers/specs/2026-06-30-admin-monthly-trend-report-design.md",
        "后台月度趋势报表 API 已实现",
        "docs/superpowers/specs/2026-07-01-admin-trend-zero-fill-design.md",
        "后台趋势报表补零已实现",
        "`includeEmpty` 参数",
        "缺少日期边界",
        "范围过大",
        "docs/superpowers/specs/2026-07-01-admin-trend-csv-export-design.md",
        "后台趋势报表 CSV 导出已实现",
        "三个 CSV 下载",
        "错误码复用",
        "docs/superpowers/specs/2026-07-01-admin-trend-xlsx-export-design.md",
        "后台趋势报表 XLSX 导出已实现",
        "三个 XLSX 下载",
        "docs/superpowers/specs/2026-07-01-admin-sync-export-row-limit-design.md",
        "后台同步导出行数上限已实现",
        "SYNC_EXPORT_ROW_LIMIT + 1",
        "413 ADMIN_EXPORT_TOO_LARGE",
        "参数化 `LIMIT`",
        "docs/superpowers/specs/2026-07-01-admin-export-job-foundation-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "后台异步导出任务基础已实现",
        "过滤条件大小限制",
        "本切片不生成文件",
        "docs/superpowers/specs/2026-07-02-admin-export-job-file-format-filter-design.md",
        "后台异步导出任务文件格式筛选已实现",
        "`fileFormat=CSV/XLSX`",
        "非法文件格式",
        "docs/superpowers/specs/2026-07-01-admin-export-job-filter-whitelist-design.md",
        "后台异步导出 filters 白名单已实现",
        "ADMIN_EXPORT_JOB_FILTERS_INVALID",
        "布尔归一化",
        "docs/superpowers/specs/2026-07-02-admin-export-job-filter-redaction-design.md",
        "后台异步导出公开 filters 脱敏已实现",
        "创建、列表、详情、重试响应脱敏",
        "worker filters 不受影响",
        "docs/superpowers/specs/2026-07-02-admin-export-worker-script-redaction-design.md",
        "后台异步导出 worker 脚本输出脱敏已实现",
        "`job.filters` 与 `lastJob.filters` 脱敏",
        "docs/superpowers/specs/2026-07-02-admin-export-job-request-id-design.md",
        "后台异步导出任务 requestId 已实现",
        "SQL 参数绑定和旧库迁移",
        "docs/superpowers/specs/2026-07-01-admin-export-job-worker-state-design.md",
        "后台异步导出 worker 状态机基础已实现",
        "PENDING -> RUNNING -> SUCCEEDED/FAILED",
        "FOR UPDATE SKIP LOCKED",
        "docs/superpowers/specs/2026-07-02-admin-export-job-error-field-lengths-design.md",
        "后台异步导出失败字段长度契约对齐已实现",
        "schema 列宽和旧库迁移",
        "docs/superpowers/specs/2026-07-02-admin-export-job-auto-retry-design.md",
        "后台异步导出失败任务自动重试已实现",
        "业务/校验失败、unsupported 和手动中断不自动重试",
        "docs/superpowers/specs/2026-07-02-admin-export-job-retry-backoff-design.md",
        "后台异步导出自动重试延迟领取已实现",
        "next_attempt_at",
        "延迟 60 秒",
        "docs/superpowers/specs/2026-07-02-admin-export-job-running-timeout-design.md",
        "后台异步导出 RUNNING 超时回收已实现",
        "ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
        "status + started_at",
        "docs/superpowers/specs/2026-07-02-admin-export-job-orphan-file-cleanup-design.md",
        "后台异步导出本地孤儿文件补偿清理已实现",
        "成功落库失败",
        "刚生成的本地文件",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-provider-boundary-design.md",
        "后台异步导出失败告警 provider 边界已补充",
        "`ADMIN_EXPORT_ALERT_PROVIDER` 当前只允许 `disabled`",
        "docs/superpowers/specs/2026-07-02-admin-export-job-alert-event-design.md",
        "后台异步导出最终失败告警事件记录已实现",
        "admin_export_job_alert_event",
        "retryable `PENDING` 不记录",
        "不发送真实通知也不新增前端页面",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-list-design.md",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-filter-design.md",
        "后台异步导出告警事件只读查询 API 已实现",
        "GET /api/admin/export-job-alert-events",
        "`jobId/exportType/fileFormat/errorCode/acknowledged/closed/dateFrom/dateTo` 筛选",
        "非法筛选拒绝",
        "DTO 防泄露",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-summary-design.md",
        "后台异步导出告警事件汇总 API 已实现",
        "GET /api/admin/export-job-alert-events/summary",
        "`exportType/fileFormat/closed/dateFrom/dateTo` 筛选",
        "`closed/open` 计数",
        "`byErrorCode` 聚合",
        "聚合 DTO 防泄露",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-acknowledge-design.md",
        "后台异步导出告警事件确认 API 已实现",
        "POST /api/admin/export-job-alert-events/{event_id}/acknowledge",
        "第一次确认获胜",
        "docs/superpowers/specs/2026-07-03-admin-export-alert-event-batch-acknowledge-design.md",
        "后台异步导出告警事件批量确认 API 已实现",
        "POST /api/admin/export-job-alert-events/batch-acknowledge",
        "逐项不存在失败",
        "重复/空列表/snake_case/额外字段拒绝",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-close-reopen-design.md",
        "后台异步导出告警事件关闭和重开 API 已实现",
        "POST /api/admin/export-job-alert-events/{event_id}/close",
        "/reopen",
        "第一次关闭获胜",
        "关闭备注长度",
        "docs/superpowers/specs/2026-07-03-admin-export-alert-event-batch-close-design.md",
        "后台异步导出告警事件批量关闭 API 已实现",
        "POST /api/admin/export-job-alert-events/batch-close",
        "逐项不存在失败",
        "重复/空列表/snake_case/额外字段拒绝",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-closed-filter-summary-design.md",
        "后台异步导出告警事件关闭筛选和汇总增强已实现",
        "`closed=true/false`",
        "错误码分组计数",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-dedupe-design.md",
        "后台异步导出告警事件去重静默已实现",
        "`occurrenceCount/lastSeenAt`",
        "关闭后重新创建",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-type-format-filter-design.md",
        "后台异步导出告警事件类型和格式筛选已实现",
        "非法文件格式",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-delete-design.md",
        "后台异步导出告警事件删除 API 已实现",
        "DELETE /api/admin/export-job-alert-events/{event_id}",
        "未关闭事件拒绝",
        "CORS DELETE 预检",
        "docs/superpowers/specs/2026-07-03-admin-export-alert-event-batch-delete-design.md",
        "后台异步导出告警事件批量删除 API 已实现",
        "POST /api/admin/export-job-alert-events/batch-delete",
        "逐项未关闭/不存在失败",
        "重复/空列表/额外字段拒绝",
        "docs/superpowers/specs/2026-07-02-admin-export-running-timeout-alert-event-design.md",
        "后台异步导出 RUNNING 超时最终失败告警事件记录已实现",
        "FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
        "WORKER_FINAL_FAILURE",
        "docs/superpowers/specs/2026-07-01-admin-export-job-download-design.md",
        "后台异步导出文件下载端点已实现",
        "GET /api/admin/export-jobs/{job_id}/download",
        "路径穿越",
        "ADMIN_EXPORT_FILE_NOT_FOUND",
        "docs/superpowers/specs/2026-07-01-admin-export-job-order-csv-worker-design.md",
        "后台异步订单明细 CSV 生成 worker 已实现",
        "ORDER_DETAIL + CSV",
        "后端派生 `storage_key`",
        "脚本 JSON 输出契约",
        "脚本启动异常脱敏",
        "docs/superpowers/specs/2026-07-01-admin-export-job-order-xlsx-worker-design.md",
        "后台异步订单明细 XLSX 生成 worker 已实现",
        "ORDER_DETAIL + XLSX",
        "CSV 路径不回归",
        "inline string",
        "docs/superpowers/specs/2026-07-01-admin-export-job-check-in-audit-csv-worker-design.md",
        "后台异步核销审计 CSV 生成 worker 已实现",
        "CHECK_IN_AUDIT + CSV",
        "核销审计 filters 传递",
        "docs/superpowers/specs/2026-07-01-admin-export-job-check-in-audit-xlsx-worker-design.md",
        "后台异步核销审计 XLSX 生成 worker 已实现",
        "CHECK_IN_AUDIT + XLSX",
        "CSV 路径不回归",
        "inline string",
        "docs/superpowers/specs/2026-07-01-admin-export-job-check-in-failure-audit-csv-worker-design.md",
        "后台异步核销失败审计 CSV 生成 worker 已实现",
        "CHECK_IN_FAILURE_AUDIT + CSV",
        "核销失败审计 filters 传递",
        "失败码枚举校验",
        "docs/superpowers/specs/2026-07-01-admin-export-job-check-in-failure-audit-xlsx-worker-design.md",
        "后台异步核销失败审计 XLSX 生成 worker 已实现",
        "CHECK_IN_FAILURE_AUDIT + XLSX",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "docs/superpowers/specs/2026-07-01-admin-export-job-refund-audit-csv-worker-design.md",
        "后台异步退款审计 CSV 生成 worker 已实现",
        "REFUND_AUDIT + CSV",
        "worker 脚本注入退款服务",
        "docs/superpowers/specs/2026-07-01-admin-export-job-refund-audit-xlsx-worker-design.md",
        "后台异步退款审计 XLSX 生成 worker 已实现",
        "REFUND_AUDIT + XLSX",
        "CSV 路径不回归",
        "退款类型枚举校验",
        "docs/superpowers/specs/2026-07-02-admin-export-job-payment-reconciliation-csv-worker-design.md",
        "后台异步支付对账 CSV 生成 worker 已实现",
        "PAYMENT_RECONCILIATION + CSV",
        "docs/superpowers/specs/2026-07-02-admin-export-job-payment-reconciliation-xlsx-worker-design.md",
        "后台异步支付对账 XLSX 生成 worker 已实现",
        "PAYMENT_RECONCILIATION + XLSX",
        "CSV 路径不回归",
        "docs/superpowers/specs/2026-07-02-admin-export-job-product-breakdown-csv-worker-design.md",
        "后台异步产品维度报表 CSV 生成 worker 已实现",
        "PRODUCT_BREAKDOWN + CSV",
        "日期 filters 传递",
        "docs/superpowers/specs/2026-07-02-admin-export-job-product-breakdown-xlsx-worker-design.md",
        "后台异步产品维度报表 XLSX 生成 worker 已实现",
        "PRODUCT_BREAKDOWN + XLSX",
        "docs/superpowers/specs/2026-07-02-admin-export-job-daily-trend-csv-worker-design.md",
        "后台异步日报趋势 CSV 生成 worker 已实现",
        "DAILY_TREND + CSV",
        "`includeEmpty` filters 传递",
        "补零范围校验",
        "docs/superpowers/specs/2026-07-02-admin-export-job-daily-trend-xlsx-worker-design.md",
        "后台异步日报趋势 XLSX 生成 worker 已实现",
        "DAILY_TREND + XLSX",
        "docs/superpowers/specs/2026-07-02-admin-export-job-hourly-trend-csv-worker-design.md",
        "后台异步小时趋势 CSV 生成 worker 已实现",
        "HOURLY_TREND + CSV",
        "31 天补零范围校验",
        "docs/superpowers/specs/2026-07-02-admin-export-job-hourly-trend-xlsx-worker-design.md",
        "后台异步小时趋势 XLSX 生成 worker 已实现",
        "HOURLY_TREND + XLSX",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "docs/superpowers/specs/2026-07-02-admin-export-job-monthly-trend-csv-worker-design.md",
        "后台异步月度趋势 CSV 生成 worker 已实现",
        "MONTHLY_TREND + CSV",
        "60 个月补零范围校验",
        "docs/superpowers/specs/2026-07-02-admin-export-job-monthly-trend-xlsx-worker-design.md",
        "后台异步月度趋势 XLSX 生成 worker 已实现",
        "MONTHLY_TREND + XLSX",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "docs/superpowers/specs/2026-06-30-mock-payment-callback-design.md",
        "backend/tests/test_mock_payment_callback_api.py",
        "模拟支付回调安全边界已实现",
        "短信 provider 边界已补充",
        "`SMS_PROVIDER=disabled`",
        "docs/superpowers/specs/2026-06-30-admin-order-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "后台订单 CSV 导出已实现",
        "docs/superpowers/specs/2026-06-30-admin-order-xlsx-export-design.md",
        "后台订单 XLSX 导出已实现",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "VERIFY_INTEGRATION_E2E=1 scripts/verify-integration.sh",
    ]
    for evidence in required_evidence:
        assert evidence in report

    out_of_scope = [
        "真实支付渠道",
        "退款通知",
        "真实渠道退款流水号",
        "真实渠道结算级财务对账",
        "真实告警",
        "异步大文件下载",
        "浏览器 E2E smoke 不是默认门禁",
        "前端视觉、响应式和页面交互验收由前端对话负责",
    ]
    for boundary in out_of_scope:
        assert boundary in report


def test_stage8_fact_sources_link_backend_acceptance_evidence():
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_readme_links = [
        "docs/backend-acceptance-report.md",
        "docs/backend-security-audit.md",
        "阶段 8 后端验收证据",
    ]
    for link in required_readme_links:
        assert link in readme

    required_decision_log_evidence = [
        "沉淀阶段 8 后端验收报告",
        "docs/backend-acceptance-report.md",
        "scripts/verify-integration.sh",
        "前端 lint/build",
        "docs/backend-security-audit.md",
    ]
    for evidence in required_decision_log_evidence:
        assert evidence in decision_log

    assert "后台同步导出行数上限" in readme
    assert "同步导出先加行数上限再做异步任务" in decision_log
    assert "后台异步导出任务基础" in readme
    assert "异步导出先落任务元数据" in decision_log
    assert "后台异步导出任务文件格式筛选" in readme
    assert "异步导出任务文件格式筛选" in decision_log
    assert "后台异步导出 filters 白名单" in readme
    assert "异步导出先收紧 filters 白名单" in decision_log
    assert "后台异步导出 worker 状态机基础" in readme
    assert "异步导出先铺 worker 状态机" in decision_log
    assert "后台异步导出失败字段长度契约对齐" in readme
    assert "异步导出失败字段长度契约对齐" in decision_log
    assert "后台异步导出失败任务手动/自动重试" in readme
    assert "后台异步导出自动重试延迟领取" in readme
    assert "后台异步导出 RUNNING 超时回收" in readme
    assert "后台异步导出本地孤儿文件补偿清理" in readme
    assert "异步导出失败任务自动重试" in decision_log
    assert "异步导出自动重试延迟领取" in decision_log
    assert "异步导出 RUNNING 超时回收" in decision_log
    assert "异步导出本地孤儿文件补偿清理" in decision_log
    assert "后台异步导出告警 provider 边界" in readme
    assert "异步导出失败告警 provider 边界" in decision_log
    assert "后台异步导出最终失败告警事件记录" in readme
    assert "异步导出最终失败告警事件记录" in decision_log
    assert "后台异步导出告警事件只读查询 API" in readme
    assert "异步导出告警事件只读查询 API" in decision_log
    assert "后台异步导出告警事件关闭筛选和汇总增强" in readme
    assert "异步导出告警事件关闭筛选和汇总增强" in decision_log
    assert "后台异步导出告警事件去重静默" in readme
    assert "异步导出告警事件去重静默" in decision_log
    assert "后台异步导出 RUNNING 超时最终失败告警事件记录" in readme
    assert "异步导出 RUNNING 超时最终失败告警事件记录" in decision_log
    assert "后台异步订单明细 CSV/XLSX 生成 worker" in readme
    assert "异步订单明细 worker 补齐 XLSX" in decision_log
    assert "后台异步核销审计 CSV/XLSX 生成 worker" in readme
    assert "CHECK_IN_AUDIT + CSV/XLSX" in readme
    assert "异步导出补核销审计 CSV" in decision_log
    assert "异步核销审计 worker 补齐 XLSX" in decision_log
    assert "后台异步核销失败审计 CSV/XLSX 生成 worker" in readme
    assert "后台异步退款审计 CSV/XLSX 生成 worker" in readme
    assert "后台异步支付对账 CSV/XLSX 生成 worker" in readme
    assert "后台异步产品维度报表 CSV/XLSX 生成 worker" in readme
    assert "后台异步日报趋势 CSV/XLSX 生成 worker" in readme
    assert "后台异步小时趋势 CSV/XLSX 生成 worker" in readme
    assert "后台异步月度趋势 CSV/XLSX 生成 worker" in readme
    assert "异步产品维度报表 worker 补齐 CSV" in decision_log
    assert "异步产品维度报表 worker 补齐 XLSX" in decision_log
    assert "异步日报趋势 worker 补齐 CSV" in decision_log
    assert "异步日报趋势 worker 补齐 XLSX" in decision_log
    assert "异步小时趋势 worker 补齐 CSV" in decision_log
    assert "异步小时趋势 worker 补齐 XLSX" in decision_log
    assert "异步月度趋势 worker 补齐 CSV" in decision_log
    assert "异步月度趋势 worker 补齐 XLSX" in decision_log
    assert "DAILY_TREND + CSV/XLSX" in readme
    assert "HOURLY_TREND + CSV/XLSX" in readme
    assert "MONTHLY_TREND + CSV/XLSX" in readme
    assert "CHECK_IN_FAILURE_AUDIT + CSV/XLSX" in readme
    assert "REFUND_AUDIT + CSV/XLSX" in readme
    assert "PAYMENT_RECONCILIATION + CSV/XLSX" in readme
    assert "异步支付对账 worker 先补 CSV" in decision_log
    assert "异步支付对账 worker 补齐 XLSX" in decision_log
    assert "异步导出补核销失败审计 CSV" in decision_log
    assert "异步核销失败审计 worker 补齐 XLSX" in decision_log
