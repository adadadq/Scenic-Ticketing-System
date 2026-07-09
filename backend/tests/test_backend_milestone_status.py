from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MILESTONE_PATH = PROJECT_ROOT / "docs" / "backend-milestone-status.md"
README_PATH = PROJECT_ROOT / "README.md"
DECISION_LOG_PATH = PROJECT_ROOT / "docs" / "decision-log.md"
API_CONTRACT_PATH = PROJECT_ROOT / "docs" / "api-contract.md"
SECURITY_AUDIT_PATH = PROJECT_ROOT / "docs" / "backend-security-audit.md"

EXPECTED_PHASES = [
    "阶段 0：冻结旧基线",
    "阶段 1：工程骨架",
    "阶段 2：数据库和会话基础",
    "阶段 3：游客认证和实名注册",
    "阶段 4：票种和时段目录",
    "阶段 5：创建待支付订单",
    "阶段 6：模拟支付和库存事务",
    "阶段 7：取消订单和我的订单体验",
    "阶段 8：端到端验收和清理",
]

ALLOWED_STATUSES = {
    "已完成",
    "后端完成，前端另线推进",
    "第二阶段",
}


def _milestone_rows():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    rows = []
    for line in status.splitlines():
        if not re.match(r"^\| 阶段 \d", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        assert len(cells) == 4
        rows.append(
            {
                "phase": cells[0],
                "status": cells[1],
                "evidence": cells[2],
                "boundary": cells[3],
            }
        )
    return rows


def test_backend_milestone_status_tracks_all_plan_phases_and_evidence():
    rows = _milestone_rows()

    assert [row["phase"] for row in rows] == EXPECTED_PHASES
    assert {row["status"] for row in rows} <= ALLOWED_STATUSES

    required_evidence = [
        "legacy-node/README.md",
        "docs/architecture.md",
        "backend/tests/test_health.py",
        "database/schema.sql",
        "backend/tests/test_auth_api.py",
        "backend/tests/test_catalog_api.py",
        "backend/tests/test_order_create_api.py",
        "backend/tests/test_payment_api.py",
        "backend/tests/test_my_orders_api.py",
        "scripts/verify-backend.sh",
        "scripts/verify-integration.sh",
        "docs/backend-acceptance-report.md",
        "docs/backend-security-audit.md",
    ]
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    for evidence in required_evidence:
        assert evidence in status

    evidence_paths = set()
    for row in rows:
        evidence_paths.update(re.findall(r"`([^`]+)`", row["evidence"]))

    for evidence_path in evidence_paths:
        assert (PROJECT_ROOT / evidence_path).exists(), evidence_path


def test_backend_milestone_status_keeps_frontend_and_second_phase_boundaries_clear():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_boundaries = [
        "前端页面设计、视觉验收和 React 组件实现仍由前端对话负责",
        "第二阶段功能不能直接写代码",
        "管理员、退款、核销、真实支付、报表或生产部署",
        "前端视觉验收不作为本对话默认门禁",
    ]
    for boundary in required_boundaries:
        assert boundary in status

    assert "docs/backend-milestone-status.md" in readme
    assert "沉淀后端里程碑状态矩阵" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_auth_foundation():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "## 第二阶段进展",
        "管理员权限基座",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-auth-foundation-design.md",
        "docs/superpowers/specs/2026-07-02-disabled-admin-session-boundary-design.md",
        "backend/tests/test_admin_auth_api.py",
        "docs/backend-security-audit.md",
        "docs/security-checklist.md",
        "禁用管理员既有 session 撤销",
        "统一未登录错误",
        "后台业务 API 继续按只读、核销、退款、报表逐片建模",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "禁用管理员既有 session 立即失效" in decision_log
    assert "禁用管理员既有 session 失效" in security_audit
    assert "已禁用管理员的既有 session" in security_checklist


def test_backend_milestone_status_tracks_second_stage_login_rate_limit_provider_boundary():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "登录限流 provider 边界",
        "docs/superpowers/specs/2026-07-02-login-rate-limit-provider-boundary-design.md",
        "backend/app/core/config.py",
        "backend/tests/test_config_db.py",
        "docs/backend-security-audit.md",
        "docs/security-checklist.md",
        "`LOGIN_RATE_LIMIT_PROVIDER=memory`",
        "大小写归一化",
        "未知 provider 启动拒绝",
        "真实 Redis/网关/负载均衡层全局限流 provider",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "LOGIN_RATE_LIMIT_PROVIDER=memory" in readme
    assert "登录限流 provider 防误配边界" in security_audit
    assert "登录限流 provider 边界" in decision_log


def test_backend_milestone_status_tracks_second_stage_sms_provider_boundary():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "短信 provider 边界",
        "docs/superpowers/specs/2026-07-02-sms-provider-boundary-design.md",
        "backend/app/core/config.py",
        "backend/tests/test_config_db.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "docs/security-checklist.md",
        "`SMS_PROVIDER=disabled`",
        "大小写归一化",
        "未知 provider 启动拒绝",
        "真实短信验证码、短信签名、发送频率、验证码过期和供应商回调",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "SMS_PROVIDER=disabled" in readme
    assert "短信 provider 防误配边界" in security_audit
    assert "短信 provider 边界" in decision_log
    assert "SMS_PROVIDER=disabled" in api_contract


def test_backend_milestone_status_tracks_second_stage_admin_order_read_model():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台订单只读 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-order-read-model-design.md",
        "backend/tests/test_admin_orders_api.py",
        "docs/backend-security-audit.md",
        "已支撑核销入口",
        "后续退款和报表继续单独建模",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_check_in():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台票码核销 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-check-in-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "docs/backend-security-audit.md",
        "已支撑退款前置状态判断",
        "核销审计日志、批量核销和撤销核销已单独建模",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_batch_check_in():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台批量核销 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-batch-check-in-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑同批逐票核销和逐票业务失败结果",
        "批量撤销和核销失败尝试审计已单独建模，异步导入仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_undo_check_in():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台撤销核销 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-undo-check-in-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑已核销票码恢复为未使用、核销量回退和 `UNDO_CHECK_IN` 审计",
        "批量撤销、撤销失败尝试审计和撤销原因审计已单独建模",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_batch_undo_check_in():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台批量撤销核销 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-batch-undo-check-in-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑同批逐票撤销、业务失败逐票返回和成功票码 `UNDO_CHECK_IN` 审计",
        "撤销失败尝试审计和撤销原因审计已单独建模，审批流仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_check_in_failure_audit_log():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台核销失败尝试审计",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-check-in-failure-audit-log-design.md",
        "database/migrations/2026-07-01-add-check-in-failure-audit-log.sql",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "backend/tests/test_schema_contract.py",
        "docs/backend-security-audit.md",
        "已记录单张/批量核销的业务失败尝试并支持管理员检索",
        "撤销失败尝试审计、CSV 导出和 XLSX 导出已单独建模，自动风控、告警和异步导出仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_undo_check_in_failure_audit_log():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台撤销核销失败尝试审计",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-undo-check-in-failure-audit-log-design.md",
        "database/migrations/2026-07-01-extend-check-in-failure-audit-log-for-undo.sql",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "backend/tests/test_schema_contract.py",
        "docs/backend-security-audit.md",
        "已记录单张/批量撤销核销的业务失败尝试并支持现有失败审计检索",
        "CSV 导出、XLSX 导出和撤销原因审计已单独建模，自动风控、告警、异步导出和审批流仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_undo_check_in_reason_audit():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台撤销核销原因审计",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-undo-check-in-reason-audit-design.md",
        "database/migrations/2026-07-01-add-check-in-audit-log-reason.sql",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_schema_contract.py",
        "docs/backend-security-audit.md",
        "已支撑单张/批量撤销核销保存可选原因",
        "核销审计日志检索、CSV 和 XLSX 导出中返回",
        "强制原因、按原因聚合和审批流仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_check_in_failure_audit_log_csv_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台核销/撤销失败尝试审计 CSV 导出",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-check-in-failure-audit-log-export-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一失败审计筛选条件下载包含核销与撤销失败尝试的 CSV",
        "敏感字段防泄露、公式注入防护和 SQL 参数绑定",
        "XLSX 已单独建模，异步大文件导出、自动风控和告警仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_check_in_failure_audit_log_xlsx_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台核销/撤销失败尝试审计 XLSX 导出",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-check-in-failure-audit-log-xlsx-export-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一失败审计筛选条件下载包含核销与撤销失败尝试的 XLSX",
        "敏感字段防泄露、无公式节点、XML 1.0 非法控制字符清洗和 SQL 参数绑定",
        "异步大文件导出、自动风控和告警仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_check_in_audit_log():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台核销审计日志",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-check-in-audit-log-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_schema_contract.py",
        "docs/backend-security-audit.md",
        "已记录单张、批量成功核销和撤销核销的操作人、票码、票项、动作和 request id",
        "全局核销日志检索已单独建模",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_check_in_audit_log_search():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台核销审计日志检索",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-check-in-audit-log-search-design.md",
        "docs/superpowers/specs/2026-07-02-admin-check-in-audit-reason-filter-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按票码、订单号、操作人、撤销原因和日期检索核销与撤销动作",
        "CSV 导出已单独建模",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_check_in_audit_log_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台核销审计日志 CSV 导出",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-check-in-audit-log-export-design.md",
        "docs/superpowers/specs/2026-07-02-admin-check-in-audit-reason-filter-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一审计筛选条件下载包含核销与撤销动作的 CSV",
        "可按撤销原因筛选",
        "XLSX 已单独建模，异步大文件导出仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_check_in_audit_log_xlsx_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台核销审计日志 XLSX 导出",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-check-in-audit-log-xlsx-export-design.md",
        "docs/superpowers/specs/2026-07-02-admin-check-in-audit-reason-filter-design.md",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一审计筛选条件下载包含核销与撤销动作的 XLSX",
        "可按撤销原因筛选",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "异步大文件导出仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_full_refund():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台全单模拟退款 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-full-refund-design.md",
        "docs/superpowers/specs/2026-07-02-admin-refund-super-admin-boundary-design.md",
        "backend/tests/test_admin_refund_api.py",
        "docs/backend-security-audit.md",
        "已支撑报表净收款口径",
        "限制只有 `SUPER_ADMIN` 可执行退款写操作",
        "退款审计日志已单独建模",
        "真实渠道退款仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_partial_refund():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台部分模拟退款 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-partial-refund-design.md",
        "docs/superpowers/specs/2026-07-02-admin-refund-super-admin-boundary-design.md",
        "backend/tests/test_admin_refund_api.py",
        "docs/backend-security-audit.md",
        "已支撑按票项退款",
        "PARTIAL_REFUND",
        "限制只有 `SUPER_ADMIN` 可执行退款写操作",
        "退款审计日志已单独建模",
        "退款通知和真实渠道退款仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_refund_audit_log():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台退款审计日志",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-refund-audit-log-design.md",
        "backend/tests/test_admin_refund_api.py",
        "database/schema.sql",
        "docs/backend-security-audit.md",
        "已记录整单/部分退款操作人、原因、金额、票项和 request id",
        "全局审计检索已单独建模",
        "真实渠道退款通知和对账流水号仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_refund_audit_log_search():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台退款审计日志检索",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-refund-audit-log-search-design.md",
        "backend/tests/test_admin_refund_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按退款类型、订单号、操作人和日期检索",
        "CSV 导出已单独建模",
        "真实渠道退款流水号和退款通知仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_refund_audit_log_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台退款审计日志 CSV 导出",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-refund-audit-log-export-design.md",
        "backend/tests/test_admin_refund_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一审计筛选条件下载 CSV",
        "XLSX 已单独建模，异步大文件导出、真实渠道退款流水号和退款通知仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_refund_audit_log_xlsx_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台退款审计日志 XLSX 导出",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-refund-audit-log-xlsx-export-design.md",
        "backend/tests/test_admin_refund_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一审计筛选条件下载 XLSX",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "异步大文件导出、真实渠道退款流水号和退款通知仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_report_summary():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台运营汇总报表 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-report-summary-design.md",
        "backend/tests/test_admin_reports_api.py",
        "docs/backend-security-audit.md",
        "已支撑首页运营概览",
        "产品维度分组图表已单独建模",
        "真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_payment_reconciliation():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台支付对账汇总 API",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-payment-reconciliation-report-design.md",
        "backend/tests/test_admin_reports_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按订单创建日期比较订单净收款、已捕获支付金额和退款审计金额",
        "管理员权限",
        "只读 GET 无 CSRF",
        "敏感字段防泄露",
        "SQL 参数绑定",
        "真实支付渠道结算文件、手续费和退款通知仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_payment_reconciliation_csv_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台支付对账汇总 CSV 导出",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-payment-reconciliation-csv-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一日期口径下载支付对账汇总 CSV",
        "管理员权限",
        "只读 GET 无 CSRF",
        "敏感字段防泄露",
        "公式注入防护",
        "OpenAPI 文件响应",
        "XLSX、异步大文件导出、真实支付渠道结算文件、手续费和退款通知仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_payment_reconciliation_xlsx_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台支付对账汇总 XLSX 导出",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-payment-reconciliation-xlsx-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一日期口径下载支付对账汇总 XLSX",
        "管理员权限",
        "只读 GET 无 CSRF",
        "敏感字段防泄露",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "OpenAPI 文件响应",
        "异步大文件导出、真实支付渠道结算文件、手续费和退款通知仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_product_breakdown():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台产品维度报表 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-product-breakdown-report-design.md",
        "backend/tests/test_admin_reports_api.py",
        "docs/backend-security-audit.md",
        "已支撑管理台产品分组图表",
        "日报趋势已单独建模",
        "真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_product_breakdown_csv_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台产品维度报表 CSV 导出",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-product-breakdown-csv-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一日期口径下载产品/票种分组 CSV",
        "管理员权限",
        "只读 GET 无 CSRF",
        "敏感字段防泄露",
        "公式注入防护",
        "OpenAPI 文件响应",
        "XLSX 已完成",
        "异步大文件导出和真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_product_breakdown_xlsx_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台产品维度报表 XLSX 导出",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-product-breakdown-xlsx-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑按同一日期口径下载产品/票种分组 XLSX",
        "管理员权限",
        "只读 GET 无 CSRF",
        "敏感字段防泄露",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "OpenAPI 文件响应",
        "异步大文件导出和真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_daily_trend():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台日报趋势报表 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-daily-trend-report-design.md",
        "backend/tests/test_admin_reports_api.py",
        "docs/backend-security-audit.md",
        "已支撑管理台日维度时间序列趋势",
        "月度趋势、小时趋势和趋势补零已单独建模",
        "真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_hourly_trend():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台小时趋势报表 API",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-hourly-trend-report-design.md",
        "backend/tests/test_admin_reports_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑管理台小时粒度时间序列趋势",
        "趋势补零、趋势 CSV 导出和趋势 XLSX 导出已单独建模",
        "真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_monthly_trend():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台月度趋势报表 API",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-monthly-trend-report-design.md",
        "backend/tests/test_admin_reports_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑管理台长周期月度趋势",
        "趋势补零、趋势 CSV 导出和趋势 XLSX 导出已单独建模",
        "真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_trend_zero_fill():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台趋势报表补零序列",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-trend-zero-fill-design.md",
        "backend/tests/test_admin_reports_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑日报、小时和月度趋势按 `includeEmpty=true` 返回连续时间桶",
        "趋势 CSV 导出已完成",
        "真实财务对账和补零范围策略变更仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_trend_csv_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台趋势报表 CSV 导出",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-trend-csv-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑日报、小时和月度趋势按同一筛选和 `includeEmpty` 口径下载 CSV",
        "管理员权限",
        "公式注入防护",
        "OpenAPI 文件响应",
        "趋势 XLSX 导出已完成",
        "异步大文件导出和真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_trend_xlsx_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台趋势报表 XLSX 导出",
        "已完成",
        "docs/superpowers/specs/2026-07-01-admin-trend-xlsx-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑日报、小时和月度趋势按同一筛选和 `includeEmpty` 口径下载 XLSX",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "OpenAPI 文件响应",
        "异步大文件导出和真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_order_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台订单 CSV 导出",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-order-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "docs/backend-security-audit.md",
        "已支撑运营订单明细 CSV 下载",
        "XLSX 已单独建模，异步大文件导出和真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_order_xlsx_export():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台订单 XLSX 导出",
        "已完成",
        "docs/superpowers/specs/2026-06-30-admin-order-xlsx-export-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/backend-security-audit.md",
        "已支撑运营订单明细 XLSX 下载、敏感字段脱敏和公式注入防护",
        "异步大文件导出和真实财务对账仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_mock_payment_callback():
    status = MILESTONE_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "模拟支付回调安全边界",
        "已完成",
        "docs/superpowers/specs/2026-06-30-mock-payment-callback-design.md",
        "backend/tests/test_mock_payment_callback_api.py",
        "docs/backend-security-audit.md",
        "下一步可继续建模真实支付渠道、退款通知或对账文件",
        "回调 IP 白名单仍需接入真实渠道后设计",
    ]
    for evidence in required_evidence:
        assert evidence in status


def test_backend_milestone_status_tracks_second_stage_admin_sync_export_row_limit():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台同步导出行数上限",
        "docs/superpowers/specs/2026-07-01-admin-sync-export-row-limit-design.md",
        "backend/tests/test_admin_report_export_api.py",
        "backend/tests/test_admin_check_in_api.py",
        "backend/tests/test_admin_refund_api.py",
        "超过上限返回 `ADMIN_EXPORT_TOO_LARGE`",
        "参数化 `LIMIT`",
        "真正异步任务、文件存储和下载链接仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台同步导出行数上限" in readme
    assert "同步导出先加行数上限再做异步任务" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_foundation():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出任务基础",
        "docs/superpowers/specs/2026-07-01-admin-export-job-foundation-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_contract.py",
        "backend/tests/test_schema_contract.py",
        "任务状态从 `PENDING` 开始",
        "后台 worker、文件生成、存储和下载链接仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出任务基础" in readme
    assert "异步导出先落任务元数据" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_file_format_filter():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出任务文件格式筛选",
        "docs/superpowers/specs/2026-07-02-admin-export-job-file-format-filter-design.md",
        "backend/app/api/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_contract.py",
        "`fileFormat=CSV/XLSX`",
        "非法文件格式",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出任务文件格式筛选" in readme
    assert "`exportType`、`fileFormat`、`status`" in api_contract
    assert "异步导出任务文件格式筛选" in decision_log
    assert "文件格式或状态" in security_audit
    assert "`exportType/fileFormat/status` 筛选" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_delete():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件删除 API",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-delete-design.md",
        "DELETE /api/admin/export-job-alert-events/{event_id}",
        "未关闭事件拒绝",
        "CORS DELETE 预检",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件删除 API" in readme
    assert "DELETE /api/admin/export-job-alert-events/{event_id}" in api_contract
    assert "异步导出告警事件删除 API" in decision_log
    assert "后台异步导出告警事件删除 API" in security_audit
    assert "只能删除已关闭事件" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_batch_delete():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件批量删除 API",
        "docs/superpowers/specs/2026-07-03-admin-export-alert-event-batch-delete-design.md",
        "POST /api/admin/export-job-alert-events/batch-delete",
        "逐项未关闭/不存在失败",
        "重复/空列表/额外字段拒绝",
        "复用单删 SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件批量删除 API" in readme
    assert "POST /api/admin/export-job-alert-events/batch-delete" in api_contract
    assert "异步导出告警事件批量删除 API" in decision_log
    assert "后台异步导出告警事件批量删除 API" in security_audit
    assert "1-100 个不重复正整数 `eventIds`" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_job_filter_whitelist():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出 filters 白名单",
        "docs/superpowers/specs/2026-07-01-admin-export-job-filter-whitelist-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "未知字段、非法日期、非法枚举、非法布尔、过长文本和日期倒挂",
        "后台 worker、文件生成、存储和下载链接仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出 filters 白名单" in readme
    assert "异步导出先收紧 filters 白名单" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_filter_redaction():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出公开 filters 脱敏",
        "docs/superpowers/specs/2026-07-02-admin-export-job-filter-redaction-design.md",
        "backend/app/services/admin_exports.py",
        "backend/app/api/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "`ticketCode`、`orderNo`、`operatorUsername`",
        "脱敏为 `***`",
        "worker 内部仍使用完整 `filters`",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "AdminExportJobDTO.filters" in api_contract
    assert "异步导出公开 filters 脱敏" in decision_log
    assert "后台异步导出任务公开 filters 脱敏" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_worker_script_redaction():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出 worker 脚本输出脱敏",
        "docs/superpowers/specs/2026-07-02-admin-export-worker-script-redaction-design.md",
        "scripts/process-admin-export-job.py",
        "scripts/run-admin-export-worker.py",
        "backend/tests/test_openapi_export_script.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "单次 worker `job.filters`",
        "循环 worker `lastJob.filters`",
        "worker 内部仍使用完整 `filters`",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "脚本输出 JSON" in api_contract
    assert "异步导出 worker 脚本输出也复用公开 filters 脱敏" in decision_log
    assert "后台异步导出 worker 脚本公开任务输出 filters 脱敏" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_job_request_id():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出任务 requestId 关联",
        "docs/superpowers/specs/2026-07-02-admin-export-job-request-id-design.md",
        "backend/app/repositories/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/app/schemas/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_schema_contract.py",
        "database/migrations/2026-07-02-add-admin-export-job-request-id.sql",
        "公开 DTO 返回 `requestId`",
        "`requestId` 不参与权限、幂等、任务领取或文件生成",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "AdminExportJobDTO.requestId" in api_contract
    assert "异步导出任务保存创建 requestId" in decision_log
    assert "后台异步导出任务 requestId 关联边界" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_job_worker_state():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出 worker 状态机基础",
        "docs/superpowers/specs/2026-07-01-admin-export-job-worker-state-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "内部 worker 原子领取最早 `PENDING` 任务",
        "行锁、状态条件、DTO 防泄露、worker 输入长度限制和 SQL 参数绑定",
        "文件生成、对象存储、下载链接、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出 worker 状态机基础" in readme
    assert "异步导出先铺 worker 状态机" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_error_field_lengths():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出失败字段长度契约对齐",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-job-error-field-lengths-design.md",
        "database/migrations/2026-07-02-align-admin-export-job-error-field-lengths.sql",
        "database/schema.sql",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_schema_contract.py",
        "错误码/错误信息列宽对齐服务层限制",
        "不改变失败 DTO、错误码语义或真实告警",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "errorCode` 最长 80" in api_contract
    assert "errorMessage` 最长 500" in api_contract
    assert "后台异步导出失败字段长度契约对齐" in readme
    assert "异步导出失败字段长度契约对齐" in decision_log
    assert "后台异步导出失败字段长度契约对齐" in security_audit
    assert "服务层限制必须与数据库列宽一致" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_job_download():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出文件下载端点",
        "docs/superpowers/specs/2026-07-01-admin-export-job-download-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_contract.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "GET /api/admin/export-jobs/{job_id}/download",
        "路径穿越",
        "文件生成、生产对象存储、重试、清理和生产级大文件传输仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出文件下载端点" in readme
    assert "异步导出先补受控下载端点" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_order_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步订单明细 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-01-admin-export-job-order-csv-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_export_script.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "ORDER_DETAIL + CSV",
        "后端派生 `storage_key`",
        "暂不支持格式失败落库",
        "XLSX 已单独补齐，常驻队列、其他导出类型、生产对象存储、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步订单明细 CSV/XLSX 生成 worker" in readme
    assert "scripts/process-admin-export-job.py" in readme
    assert "异步导出先跑通订单 CSV 生成" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_order_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步订单明细 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-01-admin-export-job-order-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "ORDER_DETAIL + XLSX",
        "后端派生 `storage_key`",
        "CSV 路径不回归",
        "未支持类型失败落库",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "常驻队列、其他导出类型、生产对象存储、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步订单明细 CSV/XLSX 生成 worker" in readme
    assert "ORDER_DETAIL + CSV/XLSX" in readme
    assert "异步订单明细 worker 补齐 XLSX" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_check_in_audit_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步核销审计 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-01-admin-export-job-check-in-audit-csv-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "CHECK_IN_AUDIT + CSV",
        "核销审计 filters 传递（含撤销原因）",
        "后端派生 `storage_key`",
        "核销审计 filters 传递",
        "订单导出路径不回归",
        "同步核销审计 CSV 的安全字段与公式注入防护",
        "XLSX 已单独补齐，常驻队列、其他导出类型、生产对象存储、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步核销审计 CSV/XLSX 生成 worker" in readme
    assert "CHECK_IN_AUDIT + CSV" in readme
    assert "异步导出补核销审计 CSV" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_check_in_audit_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步核销审计 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-01-admin-export-job-check-in-audit-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "CHECK_IN_AUDIT + XLSX",
        "核销审计 filters 传递（含撤销原因）",
        "后端派生 `storage_key`",
        "核销审计 filters 传递",
        "CSV 路径不回归",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "常驻队列、其他导出类型、生产对象存储、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步核销审计 CSV/XLSX 生成 worker" in readme
    assert "CHECK_IN_AUDIT + CSV/XLSX" in readme
    assert "异步核销审计 worker 补齐 XLSX" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_check_in_failure_audit_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步核销失败审计 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-01-admin-export-job-check-in-failure-audit-csv-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "CHECK_IN_FAILURE_AUDIT + CSV",
        "后端派生 `storage_key`",
        "核销失败审计 filters 传递",
        "核销审计路径不回归",
        "未支持类型失败落库",
        "失败码枚举校验",
        "公式注入防护",
        "XLSX 已单独补齐，常驻队列、其他导出类型、生产对象存储、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步核销失败审计 CSV/XLSX 生成 worker" in readme
    assert "CHECK_IN_FAILURE_AUDIT + CSV" in readme
    assert "异步导出补核销失败审计 CSV" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_check_in_failure_audit_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步核销失败审计 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-01-admin-export-job-check-in-failure-audit-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "CHECK_IN_FAILURE_AUDIT + XLSX",
        "后端派生 `storage_key`",
        "核销失败审计 filters 传递",
        "CSV 路径不回归",
        "未支持类型失败落库",
        "失败码枚举校验",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "常驻队列、其他导出类型、生产对象存储、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步核销失败审计 CSV/XLSX 生成 worker" in readme
    assert "CHECK_IN_FAILURE_AUDIT + CSV/XLSX" in readme
    assert "异步核销失败审计 worker 补齐 XLSX" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_refund_audit_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步退款审计 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-01-admin-export-job-refund-audit-csv-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_export_script.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "REFUND_AUDIT + CSV",
        "后端派生 `storage_key`",
        "退款审计 filters 传递",
        "脚本注入退款服务",
        "非法 filters 失败落库",
        "退款类型枚举校验",
        "公式注入防护",
        "XLSX 已单独补齐，常驻队列、其他导出类型、生产对象存储、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步退款审计 CSV/XLSX 生成 worker" in readme
    assert "REFUND_AUDIT + CSV" in readme
    assert "异步退款审计 worker 补齐 CSV" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_refund_audit_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步退款审计 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-01-admin-export-job-refund-audit-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "REFUND_AUDIT + XLSX",
        "后端派生 `storage_key`",
        "退款审计 filters 传递",
        "CSV 路径不回归",
        "未支持类型失败落库",
        "退款类型枚举校验",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "常驻队列、其他导出类型、生产对象存储、重试和清理仍需单独设计",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步退款审计 CSV/XLSX 生成 worker" in readme
    assert "REFUND_AUDIT + CSV/XLSX" in readme
    assert "异步退款审计 worker 补齐 XLSX" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_auto_retry():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出失败任务自动重试",
        "docs/superpowers/specs/2026-07-02-admin-export-job-auto-retry-design.md",
        "database/migrations/2026-07-02-add-admin-export-job-auto-retry.sql",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_schema_contract.py",
        "retry_count/max_retries",
        "第一次失败自动回到 `PENDING`",
        "耗尽一次重试后落为 `FAILED`",
        "`KeyboardInterrupt` 不自动重试",
        "unsupported 不自动重试",
        "手动 retry 重置计数",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出失败任务手动/自动重试" in readme
    assert "未预期异常会自动重试一次" in readme
    assert "异步导出失败任务自动重试" in decision_log
    assert "retry_count/max_retries" in api_contract
    assert "后台异步导出未预期异常自动重试有次数上限" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_job_retry_backoff():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出自动重试延迟领取",
        "docs/superpowers/specs/2026-07-02-admin-export-job-retry-backoff-design.md",
        "database/migrations/2026-07-02-add-admin-export-job-retry-backoff.sql",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_schema_contract.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "next_attempt_at",
        "延迟 60 秒",
        "领取 SQL 到期条件",
        "手动 retry 清空延迟",
        "成功/最终失败清空延迟",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出自动重试延迟领取" in readme
    assert "自动重试一次，重试前延迟 60 秒" in readme
    assert "异步导出自动重试延迟领取" in decision_log
    assert "next_attempt_at" in api_contract
    assert "延迟 60 秒" in api_contract
    assert "next_attempt_at" in security_audit
    assert "立即处理拿不到任务" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_job_running_timeout():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出 RUNNING 超时回收",
        "docs/superpowers/specs/2026-07-02-admin-export-job-running-timeout-design.md",
        "database/migrations/2026-07-02-add-admin-export-job-running-timeout.sql",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_schema_contract.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "超过 30 分钟",
        "ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
        "status + started_at",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出 RUNNING 超时回收" in readme
    assert "超过 30 分钟仍处于 `RUNNING`" in readme
    assert "异步导出 RUNNING 超时回收" in decision_log
    assert "ADMIN_EXPORT_JOB_WORKER_TIMEOUT" in api_contract
    assert "超过 30 分钟" in api_contract
    assert "后台异步导出 RUNNING 超时回收使用状态条件和参数绑定" in security_audit
    assert "status = 'RUNNING'" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_job_orphan_file_cleanup():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出本地孤儿文件补偿清理",
        "docs/superpowers/specs/2026-07-02-admin-export-job-orphan-file-cleanup-design.md",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/backend-security-audit.md",
        "成功落库返回 `None`",
        "抛异常",
        "保留原失败语义",
        "正常成功路径不删除文件",
        "成功返回行转换发生在连接上下文退出前",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "worker 写出文件后若成功落库失败会尽力删除刚生成的本地文件" in readme
    assert "异步导出本地孤儿文件补偿清理" in decision_log
    assert "成功落库返回 `None`" in api_contract
    assert "刚生成的本地文件" in api_contract
    assert "后台异步导出本地孤儿文件补偿清理" in security_audit
    assert "落库异常时删除刚写文件并保留原异常" in security_audit
    assert "避免提交成功后才抛异常导致误删成功任务文件" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_job_product_breakdown_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步产品维度报表 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-product-breakdown-csv-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "PRODUCT_BREAKDOWN + CSV",
        "后端派生 `storage_key`",
        "日期 filters 传递",
        "公式注入防护",
        "XLSX 已单独补齐",
        "剩余报表导出类型",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步产品维度报表 CSV/XLSX 生成 worker" in readme
    assert "异步产品维度报表 worker 补齐 CSV" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_payment_reconciliation_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步支付对账 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-payment-reconciliation-csv-worker-design.md",
        "database/migrations/2026-07-02-extend-admin-export-job-payment-reconciliation.sql",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_schema_contract.py",
        "PAYMENT_RECONCILIATION + CSV",
        "后端派生 `storage_key`",
        "日期 filters 传递",
        "单行汇总口径",
        "公式注入防护",
        "XLSX 已单独补齐",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步支付对账 CSV/XLSX 生成 worker" in readme
    assert "PAYMENT_RECONCILIATION + CSV/XLSX" in readme
    assert "异步支付对账 worker 先补 CSV" in decision_log
    assert "PAYMENT_RECONCILIATION" in api_contract
    assert "后台异步支付对账 CSV/XLSX worker 使用受控存储和既有导出口径" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_job_payment_reconciliation_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步支付对账 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-payment-reconciliation-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "PAYMENT_RECONCILIATION + XLSX",
        "后端派生 `storage_key`",
        "日期 filters 传递",
        "CSV 路径不回归",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "PAYMENT_RECONCILIATION + CSV/XLSX" in readme
    assert "异步支付对账 worker 补齐 XLSX" in decision_log
    assert "PAYMENT_RECONCILIATION + CSV/XLSX" in api_contract
    assert "后台异步支付对账 CSV/XLSX worker 使用受控存储和既有导出口径" in security_audit


def test_backend_milestone_status_tracks_second_stage_admin_export_job_product_breakdown_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步产品维度报表 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-product-breakdown-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "PRODUCT_BREAKDOWN + XLSX",
        "后端派生 `storage_key`",
        "日期 filters 传递",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "剩余报表导出类型",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步产品维度报表 CSV/XLSX 生成 worker" in readme
    assert "异步产品维度报表 worker 补齐 XLSX" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_daily_trend_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步日报趋势 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-daily-trend-csv-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "DAILY_TREND + CSV",
        "后端派生 `storage_key`",
        "日期 filters",
        "`includeEmpty` filters 传递",
        "补零范围校验",
        "公式注入防护",
        "日报趋势 XLSX",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步日报趋势 CSV/XLSX 生成 worker" in readme
    assert "DAILY_TREND + CSV/XLSX" in readme
    assert "异步日报趋势 worker 补齐 CSV" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_daily_trend_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步日报趋势 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-daily-trend-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "DAILY_TREND + XLSX",
        "后端派生 `storage_key`",
        "日期 filters",
        "`includeEmpty` filters 传递",
        "补零范围校验",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "小时趋势 CSV/XLSX",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步日报趋势 CSV/XLSX 生成 worker" in readme
    assert "DAILY_TREND + CSV/XLSX" in readme
    assert "异步日报趋势 worker 补齐 XLSX" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_hourly_trend_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步小时趋势 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-hourly-trend-csv-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "HOURLY_TREND + CSV",
        "后端派生 `storage_key`",
        "日期 filters",
        "`includeEmpty` filters 传递",
        "31 天补零范围校验",
        "公式注入防护",
        "XLSX 已单独补齐",
        "月度趋势 CSV/XLSX 已单独补齐",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步小时趋势 CSV/XLSX 生成 worker" in readme
    assert "HOURLY_TREND + CSV/XLSX" in readme
    assert "异步小时趋势 worker 补齐 CSV" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_hourly_trend_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步小时趋势 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-hourly-trend-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "HOURLY_TREND + XLSX",
        "后端派生 `storage_key`",
        "日期 filters",
        "`includeEmpty` filters 传递",
        "31 天补零范围校验",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
        "月度趋势 CSV/XLSX 已单独补齐",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步小时趋势 CSV/XLSX 生成 worker" in readme
    assert "HOURLY_TREND + CSV/XLSX" in readme
    assert "异步小时趋势 worker 补齐 XLSX" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_monthly_trend_csv_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步月度趋势 CSV 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-monthly-trend-csv-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "MONTHLY_TREND + CSV",
        "后端派生 `storage_key`",
        "日期 filters",
        "`includeEmpty` filters 传递",
        "60 个月补零范围校验",
        "公式注入防护",
        "XLSX 已单独补齐",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步月度趋势 CSV/XLSX 生成 worker" in readme
    assert "MONTHLY_TREND + CSV/XLSX" in readme
    assert "异步月度趋势 worker 补齐 CSV" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_monthly_trend_xlsx_worker():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步月度趋势 XLSX 生成 worker",
        "docs/superpowers/specs/2026-07-02-admin-export-job-monthly-trend-xlsx-worker-design.md",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "MONTHLY_TREND + XLSX",
        "后端派生 `storage_key`",
        "日期 filters",
        "`includeEmpty` filters 传递",
        "60 个月补零范围校验",
        "inline string",
        "无公式节点",
        "XML 1.0 非法控制字符清洗",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步月度趋势 CSV/XLSX 生成 worker" in readme
    assert "MONTHLY_TREND + CSV/XLSX" in readme
    assert "异步月度趋势 worker 补齐 XLSX" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_local_file_cleanup():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出本地文件清理",
        "scripts/cleanup-admin-export-files.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_export_script.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "过期 `SUCCEEDED` 导出文件",
        "路径穿越拒绝",
        "缺失文件元数据清理",
        "SQL 参数绑定",
        "错误脱敏",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "scripts/cleanup-admin-export-files.py --older-than-days 7 --limit 100" in readme
    assert "scripts/cleanup-admin-export-files.py --older-than-days 7 --limit 100" in api_contract
    assert "后台异步导出本地文件清理限制存储路径和 SQL 参数绑定" in security_audit
    assert "异步导出本地文件清理" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_worker_loop():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出 worker 循环入口",
        "scripts/run-admin-export-worker.py",
        "backend/tests/test_openapi_export_script.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "循环处理 pending 导出任务",
        "最大处理数",
        "空闲退出",
        "空闲 sleep",
        "参数错误脱敏",
        "启动异常脱敏",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "scripts/run-admin-export-worker.py --max-idle-loops 12 --idle-sleep-seconds 5" in readme
    assert "scripts/run-admin-export-worker.py --max-idle-loops 12 --idle-sleep-seconds 5" in api_contract
    assert "后台异步导出 worker 循环脚本错误输出脱敏" in security_audit
    assert "异步导出 worker 循环入口" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_worker_systemd_template():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出 worker 进程守护模板",
        "deploy/systemd/scenic-ticket-admin-export-worker.service",
        "backend/tests/test_openapi_export_script.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "非 root 用户",
        "环境文件",
        "受控导出目录",
        "自动重启",
        "SIGINT 停止信号",
        "基础加固项",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "deploy/systemd/scenic-ticket-admin-export-worker.service" in readme
    assert "deploy/systemd/scenic-ticket-admin-export-worker.service" in api_contract
    assert "后台异步导出 worker 进程守护模板权限边界" in security_audit
    assert "异步导出 worker 进程守护模板" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_cleanup_systemd_timer():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出清理定时器模板",
        "deploy/systemd/scenic-ticket-admin-export-cleanup.service",
        "deploy/systemd/scenic-ticket-admin-export-cleanup.timer",
        "backend/tests/test_openapi_export_script.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "oneshot",
        "每日触发",
        "随机延迟",
        "错过补跑",
        "受控导出目录",
        "基础加固项",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "deploy/systemd/scenic-ticket-admin-export-cleanup.timer" in readme
    assert "deploy/systemd/scenic-ticket-admin-export-cleanup.timer" in api_contract
    assert "后台异步导出清理定时器模板权限边界" in security_audit
    assert "异步导出清理定时器模板" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_storage_provider_boundary():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出存储 provider 边界",
        "docs/superpowers/specs/2026-07-02-admin-export-storage-provider-boundary-design.md",
        "backend/app/core/config.py",
        "backend/app/services/admin_exports.py",
        "backend/tests/test_config_db.py",
        "backend/tests/test_openapi_export_script.py",
        "`ADMIN_EXPORT_STORAGE_PROVIDER=local`",
        "大小写归一化",
        "未知 provider 启动拒绝",
        "统一 storage factory",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "ADMIN_EXPORT_STORAGE_PROVIDER=local" in readme
    assert "ADMIN_EXPORT_STORAGE_PROVIDER=local" in api_contract
    assert "后台异步导出存储 provider 防误配边界" in security_audit
    assert "异步导出存储 provider 边界" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_queue_provider_boundary():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出队列 provider 边界",
        "docs/superpowers/specs/2026-07-02-admin-export-queue-provider-boundary-design.md",
        "backend/app/core/config.py",
        "backend/tests/test_config_db.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "`ADMIN_EXPORT_QUEUE_PROVIDER=database`",
        "大小写归一化",
        "未知 provider 启动拒绝",
        "Redis/Celery/RQ/消息队列",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "ADMIN_EXPORT_QUEUE_PROVIDER=database" in readme
    assert "ADMIN_EXPORT_QUEUE_PROVIDER=database" in api_contract
    assert "后台异步导出队列 provider 防误配边界" in security_audit
    assert "异步导出队列 provider 边界" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_provider_boundary():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出失败告警 provider 边界",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-provider-boundary-design.md",
        "backend/app/core/config.py",
        "backend/tests/test_config_db.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "`ADMIN_EXPORT_ALERT_PROVIDER=disabled`",
        "大小写归一化",
        "未知 provider 启动拒绝",
        "email/Slack/Webhook",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "ADMIN_EXPORT_ALERT_PROVIDER=disabled" in readme
    assert "ADMIN_EXPORT_ALERT_PROVIDER=disabled" in api_contract
    assert "后台异步导出失败告警 provider 防误配边界" in security_audit
    assert "异步导出失败告警 provider 边界" in decision_log


def test_backend_milestone_status_tracks_second_stage_admin_export_job_alert_event():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出最终失败告警事件记录",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-job-alert-event-design.md",
        "database/migrations/2026-07-02-add-admin-export-job-alert-event.sql",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_schema_contract.py",
        "retryable `PENDING` 不记录",
        "真实 email/Slack/Webhook 通知",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出最终失败告警事件记录" in readme
    assert "admin_export_job_alert_event" in api_contract
    assert "异步导出最终失败告警事件记录" in decision_log
    assert "后台异步导出最终失败告警事件记录" in security_audit
    assert "不得写入 `filters`、`storage_key`" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_running_timeout_alert_event():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出 RUNNING 超时最终失败告警事件记录",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-running-timeout-alert-event-design.md",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "可重试回 `PENDING` 不记录",
        "FAILED + ADMIN_EXPORT_JOB_WORKER_TIMEOUT",
        "WORKER_FINAL_FAILURE",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出 RUNNING 超时最终失败告警事件记录" in readme
    assert "ADMIN_EXPORT_JOB_WORKER_TIMEOUT" in api_contract
    assert "异步导出 RUNNING 超时最终失败告警事件记录" in decision_log
    assert "后台异步导出 RUNNING 超时最终失败告警事件记录" in security_audit
    assert "可重试回 `PENDING` 不记录" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_list_api():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件只读查询 API",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-list-design.md",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-filter-design.md",
        "backend/app/api/admin_exports.py",
        "backend/app/schemas/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_contract.py",
        "GET /api/admin/export-job-alert-events",
        "`jobId/errorCode/acknowledged/closed/dateFrom/dateTo` 筛选",
        "DTO 防泄露",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件只读查询 API" in readme
    assert "GET  /api/admin/export-job-alert-events" in api_contract
    assert "acknowledged" in api_contract
    assert "dateFrom" in api_contract
    assert "异步导出告警事件只读查询 API" in decision_log
    assert "异步导出告警事件筛选增强" in decision_log
    assert "后台异步导出告警事件只读查询 API" in security_audit
    assert "告警事件只读查询 API 只能接受管理员 session" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_summary_api():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件汇总 API",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-summary-design.md",
        "backend/app/api/admin_exports.py",
        "backend/app/schemas/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_contract.py",
        "GET /api/admin/export-job-alert-events/summary",
        "`closed/dateFrom/dateTo` 筛选",
        "`byErrorCode`",
        "聚合 DTO 防泄露",
        "SQL 参数绑定",
        "无 CSRF 只读 GET",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件汇总 API" in readme
    assert "GET  /api/admin/export-job-alert-events/summary" in api_contract
    assert "AdminExportJobAlertEventSummaryDTO" in api_contract
    assert "异步导出告警事件汇总 API" in decision_log
    assert "后台异步导出告警事件汇总 API" in security_audit
    assert "告警事件汇总 API 只能接受管理员 session" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_acknowledge_api():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件确认 API",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-acknowledge-design.md",
        "database/migrations/2026-07-02-add-admin-export-job-alert-event-acknowledgement.sql",
        "backend/app/api/admin_exports.py",
        "backend/app/schemas/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_contract.py",
        "backend/tests/test_schema_contract.py",
        "POST /api/admin/export-job-alert-events/{event_id}/acknowledge",
        "第一次确认获胜",
        "DTO 防泄露",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件确认 API" in readme
    assert "POST /api/admin/export-job-alert-events/{event_id}/acknowledge" in api_contract
    assert "异步导出告警事件确认 API" in decision_log
    assert "后台异步导出告警事件确认 API" in security_audit
    assert "告警事件确认只能由管理员 session 访问" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_batch_acknowledge():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件批量确认 API",
        "docs/superpowers/specs/2026-07-03-admin-export-alert-event-batch-acknowledge-design.md",
        "POST /api/admin/export-job-alert-events/batch-acknowledge",
        "第一次确认获胜",
        "逐项不存在失败",
        "重复/空列表/snake_case/额外字段拒绝",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件批量确认 API" in readme
    assert "POST /api/admin/export-job-alert-events/batch-acknowledge" in api_contract
    assert "异步导出告警事件批量确认 API" in decision_log
    assert "后台异步导出告警事件批量确认 API" in security_audit
    assert "已确认事件不能覆盖第一次确认记录" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_close_reopen_api():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件关闭和重开 API",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-close-reopen-design.md",
        "database/migrations/2026-07-02-add-admin-export-job-alert-event-close.sql",
        "backend/app/api/admin_exports.py",
        "backend/app/schemas/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_openapi_contract.py",
        "backend/tests/test_schema_contract.py",
        "POST /api/admin/export-job-alert-events/{event_id}/close",
        "/reopen",
        "第一次关闭获胜",
        "DTO 防泄露",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件关闭和重开 API" in readme
    assert "POST /api/admin/export-job-alert-events/{event_id}/close" in api_contract
    assert "POST /api/admin/export-job-alert-events/{event_id}/reopen" in api_contract
    assert "异步导出告警事件关闭和重开 API" in decision_log
    assert "后台异步导出告警事件关闭和重开 API" in security_audit
    assert "告警事件关闭和重开 API 只能接受管理员 session" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_batch_close_api():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件批量关闭 API",
        "docs/superpowers/specs/2026-07-03-admin-export-alert-event-batch-close-design.md",
        "POST /api/admin/export-job-alert-events/batch-close",
        "第一次关闭获胜",
        "逐项不存在失败",
        "重复/空列表/snake_case/额外字段拒绝",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件批量关闭 API" in readme
    assert "POST /api/admin/export-job-alert-events/batch-close" in api_contract
    assert "异步导出告警事件批量关闭 API" in decision_log
    assert "后台异步导出告警事件批量关闭 API" in security_audit
    assert "已关闭事件不能覆盖第一次关闭记录" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_closed_filter_summary():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件关闭筛选和汇总增强",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-closed-filter-summary-design.md",
        "backend/app/api/admin_exports.py",
        "backend/app/schemas/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "`closed=true/false`",
        "`closed/open` 顶层计数",
        "`byErrorCode` 分组计数",
        "非法关闭状态",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件关闭筛选和汇总增强" in readme
    assert "`closed`" in api_contract
    assert "`closed`、`open`" in api_contract
    assert "异步导出告警事件关闭筛选和汇总增强" in decision_log
    assert "非法关闭状态" in security_audit
    assert "acknowledged/closed/dateFrom/dateTo" in status
    assert "closed/dateFrom/dateTo" in status


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_type_format_filter():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件类型和格式筛选",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-type-format-filter-design.md",
        "backend/app/api/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/app/repositories/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "docs/api-contract.md",
        "`exportType/fileFormat`",
        "大小写归一化",
        "非法导出类型",
        "非法文件格式",
        "SQL 参数绑定",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件类型和格式筛选" in readme
    assert "`exportType`、`fileFormat`" in api_contract
    assert "异步导出告警事件类型和格式筛选" in decision_log
    assert "非法导出类型" in security_audit
    assert "jobId/exportType/fileFormat/errorCode" in security_checklist
    assert "exportType/fileFormat/closed/dateFrom/dateTo" in security_checklist


def test_backend_milestone_status_tracks_second_stage_admin_export_alert_event_dedupe():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")
    security_checklist = SECURITY_AUDIT_PATH.with_name("security-checklist.md").read_text(encoding="utf-8")

    required_evidence = [
        "后台异步导出告警事件去重静默",
        "已完成",
        "docs/superpowers/specs/2026-07-02-admin-export-alert-event-dedupe-design.md",
        "database/migrations/2026-07-02-add-admin-export-job-alert-event-dedupe.sql",
        "database/schema.sql",
        "backend/app/repositories/admin_exports.py",
        "backend/app/schemas/admin_exports.py",
        "backend/app/services/admin_exports.py",
        "backend/tests/test_admin_export_jobs_api.py",
        "backend/tests/test_schema_contract.py",
        "`job_id/error_code/alert_source`",
        "`occurrenceCount/lastSeenAt`",
        "关闭后再次失败会创建新事件",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "后台异步导出告警事件去重静默" in readme
    assert "occurrenceCount" in api_contract
    assert "lastSeenAt" in api_contract
    assert "异步导出告警事件去重静默" in decision_log
    assert "test_export_job_alert_event_deduplicates_open_events_but_not_closed_events" in security_audit
    assert "同一个 `job_id/error_code/alert_source`" in security_checklist


def test_backend_milestone_status_tracks_second_stage_payment_provider_boundary():
    status = MILESTONE_PATH.read_text(encoding="utf-8")
    readme = README_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")
    security_audit = SECURITY_AUDIT_PATH.read_text(encoding="utf-8")

    required_evidence = [
        "支付 provider 边界",
        "docs/superpowers/specs/2026-07-02-payment-provider-boundary-design.md",
        "backend/app/core/config.py",
        "backend/tests/test_config_db.py",
        "docs/api-contract.md",
        "docs/backend-security-audit.md",
        "`PAYMENT_PROVIDER=mock`",
        "大小写归一化",
        "未知 provider 启动拒绝",
        "真实微信/支付宝/Stripe/银联支付 provider",
    ]
    for evidence in required_evidence:
        assert evidence in status

    assert "PAYMENT_PROVIDER=mock" in readme
    assert "PAYMENT_PROVIDER=mock" in api_contract
    assert "支付 provider 防误配边界" in security_audit
    assert "支付 provider 边界" in decision_log
