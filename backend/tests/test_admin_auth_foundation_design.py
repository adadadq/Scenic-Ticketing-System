from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = PROJECT_ROOT / "docs" / "superpowers" / "specs" / "2026-06-30-admin-auth-foundation-design.md"
DECISION_LOG_PATH = PROJECT_ROOT / "docs" / "decision-log.md"
API_CONTRACT_PATH = PROJECT_ROOT / "docs" / "api-contract.md"


def test_admin_auth_foundation_design_covers_required_workflow_sections():
    design = DESIGN_PATH.read_text(encoding="utf-8")

    required_sections = [
        "## 问题",
        "## 范围",
        "## API",
        "## DTO",
        "## 数据",
        "## 权限",
        "## 登录限速",
        "## CSRF 与 Cookie",
        "## 错误码",
        "## 安全测试",
        "## 验收命令",
        "## 前端协作",
    ]
    for section in required_sections:
        assert section in design

    required_contract_terms = [
        "POST /api/admin/auth/login",
        "GET  /api/admin/auth/me",
        "POST /api/admin/auth/logout",
        "AdminMeDTO",
        "admin_user",
        "require_admin_session",
        "session-bound CSRF",
        "HTTP-only Cookie",
        "pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>",
        "260000",
        "hmac.compare_digest",
        "client_host + hash(username)",
        "RATE_LIMITED",
        "ADMIN_LOGIN_FAILED",
        "ADMIN_AUTH_REQUIRED",
        "ADMIN_FORBIDDEN",
        "scripts/verify-backend.sh",
        "scripts/verify-integration.sh",
    ]
    for term in required_contract_terms:
        assert term in design


def test_admin_auth_foundation_design_keeps_scope_and_security_boundaries_clear():
    design = DESIGN_PATH.read_text(encoding="utf-8")
    decision_log = DECISION_LOG_PATH.read_text(encoding="utf-8")

    out_of_scope = [
        "管理员页面、React 组件或视觉设计",
        "线路产品 CRUD、时段维护、核销、退款、报表",
        "从旧 Node 代码逐行迁移",
    ]
    for boundary in out_of_scope:
        assert boundary in design

    security_boundaries = [
        "响应不返回 `passwordHash`、session token、CSRF token",
        "用户名不存在、密码错误、账号禁用",
        "统一 `401 ADMIN_LOGIN_FAILED`",
        "数据库只保存哈希",
        "不包含明文演示密码",
        "不能误清理游客会话",
        "不在本切片定义后台业务权限矩阵",
    ]
    for boundary in security_boundaries:
        assert boundary in design

    assert "确定第二阶段先做管理员权限基座" in decision_log


def test_admin_auth_foundation_design_admin_endpoints_are_published_after_implementation():
    design = DESIGN_PATH.read_text(encoding="utf-8")
    api_contract = API_CONTRACT_PATH.read_text(encoding="utf-8")

    planned_endpoints = {
        (match.group("method"), match.group("path"))
        for match in re.finditer(
            r"^\s*(?P<method>GET|POST)\s+(?P<path>/api/admin/auth/[^\s`]+)\s*$",
            design,
            flags=re.MULTILINE,
        )
    }

    assert planned_endpoints == {
        ("POST", "/api/admin/auth/login"),
        ("GET", "/api/admin/auth/me"),
        ("POST", "/api/admin/auth/logout"),
    }
    for _method, path in planned_endpoints:
        assert path in api_contract
