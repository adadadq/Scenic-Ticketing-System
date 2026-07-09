from pathlib import Path

import pytest

from app.core.config import (
    DatabaseSettings,
    SettingsValidationError,
    get_settings,
    normalize_admin_export_alert_provider,
    normalize_admin_export_queue_provider,
    normalize_admin_export_storage_provider,
    normalize_environment,
    normalize_login_rate_limit_provider,
    normalize_payment_provider,
    normalize_sms_provider,
    parse_bool_env,
    parse_csv_env,
    parse_optional_env,
    validate_http_token_name,
    validate_production_origin,
)
from app.core.db import ping_database, transaction

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class FakeCursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row=(1,)):
        self.row = row
        self.committed = False
        self.rolled_back = False
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))
        return FakeCursor(self.row)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        pass


def test_database_settings_builds_dsn_and_masks_password():
    settings = DatabaseSettings(
        host="db.example.test",
        port=15432,
        database="scenic ticket",
        user="scenic user",
        password="secret/pass",
        sslmode="require",
    )

    assert settings.dsn == (
        "postgresql://scenic%20user:secret%2Fpass@db.example.test:15432/"
        "scenic%20ticket?sslmode=require"
    )
    assert settings.safe_summary()["password"] == "***"
    assert "secret/pass" not in str(settings.safe_summary())
    assert "secret/pass" not in repr(settings)


def test_default_database_settings_are_local_placeholders():
    settings = DatabaseSettings()

    assert settings.host in {"127.0.0.1", "localhost"}
    assert settings.database == "scenic_ticket"
    assert settings.user == "scenic_app"
    assert settings.password == ""


def test_env_example_uses_placeholder_database_values():
    env_values = {}
    env_example = PROJECT_ROOT / ".env.example"
    env_text = env_example.read_text(encoding="utf-8")
    for line in env_text.splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_values[key] = value

    assert env_values["DB_HOST"] in {"127.0.0.1", "localhost"}
    assert env_values["DB_NAME"] == "scenic_ticket"
    assert env_values["DB_USER"] == "scenic_app"
    assert env_values["DB_PASSWORD"] == "replace-with-password"
    assert env_values["PAYMENT_PROVIDER"] == "mock"
    assert env_values["SMS_PROVIDER"] == "disabled"
    assert env_values["LOGIN_RATE_LIMIT_PROVIDER"] == "memory"
    assert env_values["ADMIN_EXPORT_STORAGE_PROVIDER"] == "local"
    assert env_values["ADMIN_EXPORT_QUEUE_PROVIDER"] == "database"
    assert env_values["ADMIN_EXPORT_ALERT_PROVIDER"] == "disabled"
    assert env_values["MOCKPAY_CALLBACK_SECRET"] == "replace-with-mockpay-callback-secret"


def test_get_settings_reads_database_environment(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("PAYMENT_PROVIDER", " MOCK ")
    monkeypatch.setenv("DB_HOST", "127.0.0.2")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "ticket_test")
    monkeypatch.setenv("DB_USER", "ticket_user")
    monkeypatch.setenv("DB_PASSWORD", "ticket_password")
    monkeypatch.setenv("DB_SSLMODE", "require")

    settings = get_settings()

    assert settings.payment_provider == "mock"
    assert settings.database.host == "127.0.0.2"
    assert settings.database.port == 5433
    assert settings.database.database == "ticket_test"
    assert settings.database.user == "ticket_user"
    assert settings.database.password == "ticket_password"
    assert settings.database.sslmode == "require"
    get_settings.cache_clear()


def test_get_settings_reads_admin_export_storage_environment(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_EXPORT_STORAGE_PROVIDER", " LOCAL ")
    monkeypatch.setenv("ADMIN_EXPORT_STORAGE_DIR", "/tmp/scenic-admin-exports")
    monkeypatch.setenv("ADMIN_EXPORT_QUEUE_PROVIDER", " DATABASE ")
    monkeypatch.setenv("ADMIN_EXPORT_ALERT_PROVIDER", " DISABLED ")

    settings = get_settings()

    assert settings.admin_export_storage_provider == "local"
    assert settings.admin_export_storage_dir == "/tmp/scenic-admin-exports"
    assert settings.admin_export_queue_provider == "database"
    assert settings.admin_export_alert_provider == "disabled"
    get_settings.cache_clear()


def test_get_settings_reads_cors_environment(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173, http://127.0.0.1:4173")
    monkeypatch.setenv("CORS_ALLOWED_ORIGIN_REGEX", r"^http://localhost:\d+$")

    settings = get_settings()

    assert settings.cors.allowed_origins == ("http://localhost:5173", "http://127.0.0.1:4173")
    assert settings.cors.allowed_origin_regex == r"^http://localhost:\d+$"
    get_settings.cache_clear()


def test_get_settings_reads_login_rate_limit_environment(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SMS_PROVIDER", " DISABLED ")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_PROVIDER", " MEMORY ")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "9")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "120")

    settings = get_settings()

    assert settings.security.sms_provider == "disabled"
    assert settings.security.login_rate_limit_provider == "memory"
    assert settings.security.login_rate_limit_max_attempts == 9
    assert settings.security.login_rate_limit_window_seconds == 120
    get_settings.cache_clear()


def test_get_settings_reads_mockpay_callback_environment(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("MOCKPAY_CALLBACK_SECRET", "test-callback-secret")
    monkeypatch.setenv("MOCKPAY_CALLBACK_TOLERANCE_SECONDS", "120")

    settings = get_settings()

    assert settings.security.mockpay_callback_secret == "test-callback-secret"
    assert settings.security.mockpay_callback_tolerance_seconds == 120
    get_settings.cache_clear()


def test_parse_csv_env_ignores_empty_values(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", " http://localhost:5173, ,http://127.0.0.1:4173 ")

    assert parse_csv_env("CORS_ALLOWED_ORIGINS") == ("http://localhost:5173", "http://127.0.0.1:4173")


def test_parse_optional_env_maps_blank_to_none(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGIN_REGEX", "   ")

    assert parse_optional_env("CORS_ALLOWED_ORIGIN_REGEX", "fallback") is None


def test_parse_bool_env_strips_and_uses_fallback(monkeypatch):
    monkeypatch.setenv("COOKIE_SECURE", " true ")
    assert parse_bool_env("COOKIE_SECURE", False) is True

    monkeypatch.setenv("COOKIE_SECURE", " ")
    assert parse_bool_env("COOKIE_SECURE", True) is True


def test_normalize_environment_strips_and_lowercases_value():
    assert normalize_environment(" Production ") == "production"
    assert normalize_environment(" ") == "development"


def test_normalize_payment_provider_strips_and_lowercases_value():
    assert normalize_payment_provider(" MOCK ") == "mock"
    assert normalize_payment_provider(" ") == "mock"


def test_normalize_sms_provider_strips_and_lowercases_value():
    assert normalize_sms_provider(" DISABLED ") == "disabled"
    assert normalize_sms_provider(" ") == "disabled"


def test_normalize_login_rate_limit_provider_strips_and_lowercases_value():
    assert normalize_login_rate_limit_provider(" MEMORY ") == "memory"
    assert normalize_login_rate_limit_provider(" ") == "memory"


def test_normalize_admin_export_storage_provider_strips_and_lowercases_value():
    assert normalize_admin_export_storage_provider(" LOCAL ") == "local"
    assert normalize_admin_export_storage_provider(" ") == "local"


def test_normalize_admin_export_queue_provider_strips_and_lowercases_value():
    assert normalize_admin_export_queue_provider(" DATABASE ") == "database"
    assert normalize_admin_export_queue_provider(" ") == "database"


def test_normalize_admin_export_alert_provider_strips_and_lowercases_value():
    assert normalize_admin_export_alert_provider(" DISABLED ") == "disabled"
    assert normalize_admin_export_alert_provider(" ") == "disabled"


@pytest.mark.parametrize(
    ("value", "expected_error"),
    [
        ("x-csrf-token", None),
        ("scenic_session", None),
        ("", "HTTP token name"),
        ("csrf token", "HTTP token name"),
        ("x-csrf-token\r\nx-injected: 1", "HTTP token name"),
    ],
)
def test_validate_http_token_name(value, expected_error):
    assert validate_http_token_name("CSRF_HEADER_NAME", value) == (
        f"CSRF_HEADER_NAME must be a non-empty HTTP token name" if expected_error else None
    )


@pytest.mark.parametrize(
    ("env_name", "env_value"),
    [
        ("SESSION_COOKIE_NAME", "scenic session"),
        ("CSRF_COOKIE_NAME", "scenic;csrf"),
        ("CSRF_HEADER_NAME", "x-csrf-token\r\nx-injected: 1"),
    ],
)
def test_settings_reject_invalid_cookie_and_csrf_header_names(monkeypatch, env_name, env_value):
    get_settings.cache_clear()
    monkeypatch.setenv(env_name, env_value)

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    assert env_name in str(error.value)
    assert "HTTP token name" in str(error.value)
    get_settings.cache_clear()


def test_settings_reject_unknown_payment_provider(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("PAYMENT_PROVIDER", "wechat")

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    assert "PAYMENT_PROVIDER currently supports only mock" in str(error.value)
    get_settings.cache_clear()


def test_settings_reject_unknown_sms_provider(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("SMS_PROVIDER", "aliyun")

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    assert "SMS_PROVIDER currently supports only disabled" in str(error.value)
    get_settings.cache_clear()


def test_settings_reject_unknown_login_rate_limit_provider(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("LOGIN_RATE_LIMIT_PROVIDER", "redis")

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    assert "LOGIN_RATE_LIMIT_PROVIDER currently supports only memory" in str(error.value)
    get_settings.cache_clear()


def test_settings_reject_unknown_admin_export_storage_provider(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_EXPORT_STORAGE_PROVIDER", "s3")

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    assert "ADMIN_EXPORT_STORAGE_PROVIDER currently supports only local" in str(error.value)
    get_settings.cache_clear()


def test_settings_reject_unknown_admin_export_queue_provider(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_EXPORT_QUEUE_PROVIDER", "redis")

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    assert "ADMIN_EXPORT_QUEUE_PROVIDER currently supports only database" in str(error.value)
    get_settings.cache_clear()


def test_settings_reject_unknown_admin_export_alert_provider(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_EXPORT_ALERT_PROVIDER", "webhook")

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    assert "ADMIN_EXPORT_ALERT_PROVIDER currently supports only disabled" in str(error.value)
    get_settings.cache_clear()


@pytest.mark.parametrize(
    ("origin", "message"),
    [
        ("*", "wildcards"),
        ("https://*.example.com", "wildcards"),
        ("http://tickets.example.com", "https://"),
        ("https://localhost:5173", "loopback"),
        ("https://127.0.0.1:5173", "loopback"),
        ("https://tickets.example.com/path", "origin only"),
    ],
)
def test_validate_production_origin_rejects_non_production_origins(origin, message):
    assert message in validate_production_origin(origin)


def test_validate_production_origin_accepts_https_origin():
    assert validate_production_origin("https://tickets.example.com") is None


def test_development_settings_allow_loopback_cors_defaults(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGIN_REGEX", raising=False)
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    settings = get_settings()

    assert settings.environment == "development"
    assert settings.security.cookie_secure is False
    assert settings.cors.allowed_origin_regex
    get_settings.cache_clear()


def test_production_settings_reject_insecure_deployment_defaults(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("CORS_ALLOWED_ORIGIN_REGEX", raising=False)

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    message = str(error.value)
    assert "COOKIE_SECURE=true" in message
    assert "DB_PASSWORD is required" in message
    assert "MOCKPAY_CALLBACK_SECRET" in message
    assert "CORS_ALLOWED_ORIGINS" in message
    assert "CORS_ALLOWED_ORIGIN_REGEX" in message
    get_settings.cache_clear()


def test_production_settings_reject_blank_password_and_local_cors(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", " Production ")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    monkeypatch.setenv("DB_PASSWORD", "   ")
    monkeypatch.setenv("MOCKPAY_CALLBACK_SECRET", "production-callback-secret")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,*")
    monkeypatch.setenv("CORS_ALLOWED_ORIGIN_REGEX", "")

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    message = str(error.value)
    assert "DB_PASSWORD is required" in message
    assert "localhost" in message
    assert "wildcards" in message
    get_settings.cache_clear()


@pytest.mark.parametrize(
    "placeholder_secret",
    ["", "dev-mockpay-callback-secret", "replace-with-mockpay-callback-secret"],
)
def test_production_settings_reject_default_or_placeholder_mockpay_callback_secret(monkeypatch, placeholder_secret):
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    monkeypatch.setenv("DB_PASSWORD", "production-secret")
    monkeypatch.setenv("MOCKPAY_CALLBACK_SECRET", placeholder_secret)
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://tickets.example.com")
    monkeypatch.setenv("CORS_ALLOWED_ORIGIN_REGEX", "")

    with pytest.raises(SettingsValidationError) as error:
        get_settings()

    assert "MOCKPAY_CALLBACK_SECRET" in str(error.value)
    get_settings.cache_clear()


def test_production_settings_accept_explicit_secure_deployment_config(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("PAYMENT_PROVIDER", "mock")
    monkeypatch.setenv("SMS_PROVIDER", "disabled")
    monkeypatch.setenv("LOGIN_RATE_LIMIT_PROVIDER", "memory")
    monkeypatch.setenv("ADMIN_EXPORT_STORAGE_PROVIDER", "local")
    monkeypatch.setenv("ADMIN_EXPORT_QUEUE_PROVIDER", "database")
    monkeypatch.setenv("ADMIN_EXPORT_ALERT_PROVIDER", "disabled")
    monkeypatch.setenv("COOKIE_SECURE", " true ")
    monkeypatch.setenv("DB_PASSWORD", "production-secret")
    monkeypatch.setenv("MOCKPAY_CALLBACK_SECRET", "production-callback-secret")
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://tickets.example.com")
    monkeypatch.setenv("CORS_ALLOWED_ORIGIN_REGEX", "")

    settings = get_settings()

    assert settings.environment == "production"
    assert settings.security.cookie_secure is True
    assert settings.database.password == "production-secret"
    assert settings.security.mockpay_callback_secret == "production-callback-secret"
    assert settings.admin_export_alert_provider == "disabled"
    assert settings.cors.allowed_origins == ("https://tickets.example.com",)
    assert settings.cors.allowed_origin_regex is None
    get_settings.cache_clear()


def test_transaction_commits_on_success():
    connection = FakeConnection()

    with transaction(connection) as active:
        active.execute("SELECT 1")

    assert connection.committed is True
    assert connection.rolled_back is False


def test_transaction_rolls_back_on_error():
    connection = FakeConnection()

    with pytest.raises(RuntimeError):
        with transaction(connection):
            raise RuntimeError("boom")

    assert connection.committed is False
    assert connection.rolled_back is True


def test_ping_database_maps_select_one_result():
    connection = FakeConnection(row=(1,))

    assert ping_database(connection) is True
    assert connection.queries == [("SELECT 1 AS ok", None)]
