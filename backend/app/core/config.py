from dataclasses import dataclass, field
from functools import lru_cache
import os
import re
from urllib.parse import quote, urlparse


@dataclass(frozen=True)
class DatabaseSettings:
    host: str = "127.0.0.1"
    port: int = 15432
    database: str = "scenic_ticket"
    user: str = "scenic_app"
    password: str = field(default="", repr=False)
    sslmode: str = "disable"

    @property
    def dsn(self) -> str:
        password_part = f":{quote(self.password, safe='')}" if self.password else ""
        return (
            f"postgresql://{quote(self.user, safe='')}{password_part}"
            f"@{self.host}:{self.port}/{quote(self.database, safe='')}"
            f"?sslmode={quote(self.sslmode, safe='')}"
        )

    def safe_summary(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "sslmode": self.sslmode,
            "password": "***" if self.password else "",
        }


@dataclass(frozen=True)
class SecuritySettings:
    session_cookie_name: str = "scenic_session"
    admin_session_cookie_name: str = "scenic_admin_session"
    csrf_cookie_name: str = "scenic_csrf"
    csrf_header_name: str = "x-csrf-token"
    cookie_samesite: str = "lax"
    cookie_secure: bool = False
    session_ttl_seconds: int = 8 * 60 * 60
    sms_provider: str = "disabled"
    login_rate_limit_provider: str = "memory"
    login_rate_limit_max_attempts: int = 5
    login_rate_limit_window_seconds: int = 60
    mockpay_callback_secret: str = field(default="dev-mockpay-callback-secret", repr=False)
    mockpay_callback_tolerance_seconds: int = 300


@dataclass(frozen=True)
class CorsSettings:
    allowed_origins: tuple[str, ...] = ()
    allowed_origin_regex: str | None = r"^http://(localhost|127\.0\.0\.1):\d+$"


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "scenic-ticket-api"
    app_version: str = "0.1.0"
    environment: str = "development"
    payment_provider: str = "mock"
    admin_export_storage_provider: str = "local"
    admin_export_storage_dir: str = ".data/admin-exports"
    admin_export_queue_provider: str = "database"
    admin_export_alert_provider: str = "disabled"
    database: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    cors: CorsSettings = CorsSettings()


class SettingsValidationError(RuntimeError):
    pass


HTTP_TOKEN_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
MOCKPAY_CALLBACK_SECRET_PLACEHOLDERS = {
    "",
    SecuritySettings.mockpay_callback_secret,
    "replace-with-mockpay-callback-secret",
}
SUPPORTED_ADMIN_EXPORT_STORAGE_PROVIDERS = {"local"}
SUPPORTED_ADMIN_EXPORT_QUEUE_PROVIDERS = {"database"}
SUPPORTED_ADMIN_EXPORT_ALERT_PROVIDERS = {"disabled"}
SUPPORTED_PAYMENT_PROVIDERS = {"mock"}
SUPPORTED_SMS_PROVIDERS = {"disabled"}
SUPPORTED_LOGIN_RATE_LIMIT_PROVIDERS = {"memory"}


def parse_int_env(name: str, fallback: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return fallback
    try:
        return int(value)
    except ValueError:
        return fallback


def parse_csv_env(name: str) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None:
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def parse_bool_env(name: str, fallback: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return fallback
    return value.strip().lower() in ("1", "true", "yes", "on")


def parse_optional_env(name: str, fallback: str | None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return fallback
    stripped = value.strip()
    return stripped or None


def normalize_environment(value: str | None) -> str:
    return (value or AppSettings.environment).strip().lower() or AppSettings.environment


def normalize_payment_provider(value: str | None) -> str:
    return (value or AppSettings.payment_provider).strip().lower() or AppSettings.payment_provider


def normalize_sms_provider(value: str | None) -> str:
    default_provider = SecuritySettings.sms_provider
    return (value or default_provider).strip().lower() or default_provider


def normalize_login_rate_limit_provider(value: str | None) -> str:
    default_provider = SecuritySettings.login_rate_limit_provider
    return (value or default_provider).strip().lower() or default_provider


def normalize_admin_export_storage_provider(value: str | None) -> str:
    return (value or AppSettings.admin_export_storage_provider).strip().lower() or AppSettings.admin_export_storage_provider


def normalize_admin_export_queue_provider(value: str | None) -> str:
    return (value or AppSettings.admin_export_queue_provider).strip().lower() or AppSettings.admin_export_queue_provider


def normalize_admin_export_alert_provider(value: str | None) -> str:
    return (value or AppSettings.admin_export_alert_provider).strip().lower() or AppSettings.admin_export_alert_provider


def is_loopback_host(hostname: str | None) -> bool:
    if hostname is None:
        return True
    normalized = hostname.strip().lower()
    return normalized in {"localhost", "127.0.0.1", "::1", "0.0.0.0"} or normalized.startswith("127.")


def validate_production_origin(origin: str) -> str | None:
    stripped = origin.strip()
    if not stripped or "*" in stripped:
        return "must be an explicit HTTPS origin without wildcards"

    parsed = urlparse(stripped)
    if parsed.scheme != "https" or not parsed.hostname:
        return "must use https:// with a hostname"
    if parsed.path not in ("", "/") or parsed.params or parsed.query or parsed.fragment:
        return "must be an origin only, without path, query, or fragment"
    if is_loopback_host(parsed.hostname):
        return "must not use loopback or localhost in production"
    return None


def validate_http_token_name(name: str, value: str) -> str | None:
    if not value or not HTTP_TOKEN_RE.fullmatch(value):
        return f"{name} must be a non-empty HTTP token name"
    return None


def validate_settings(settings: AppSettings) -> None:
    violations: list[str] = []
    for name, value in (
        ("SESSION_COOKIE_NAME", settings.security.session_cookie_name),
        ("ADMIN_SESSION_COOKIE_NAME", settings.security.admin_session_cookie_name),
        ("CSRF_COOKIE_NAME", settings.security.csrf_cookie_name),
        ("CSRF_HEADER_NAME", settings.security.csrf_header_name),
    ):
        error = validate_http_token_name(name, value)
        if error:
            violations.append(error)

    if settings.security.mockpay_callback_tolerance_seconds <= 0:
        violations.append("MOCKPAY_CALLBACK_TOLERANCE_SECONDS must be positive")
    if settings.payment_provider not in SUPPORTED_PAYMENT_PROVIDERS:
        violations.append("PAYMENT_PROVIDER currently supports only mock")
    if settings.security.sms_provider not in SUPPORTED_SMS_PROVIDERS:
        violations.append("SMS_PROVIDER currently supports only disabled")
    if settings.security.login_rate_limit_provider not in SUPPORTED_LOGIN_RATE_LIMIT_PROVIDERS:
        violations.append("LOGIN_RATE_LIMIT_PROVIDER currently supports only memory")
    if settings.admin_export_storage_provider not in SUPPORTED_ADMIN_EXPORT_STORAGE_PROVIDERS:
        violations.append("ADMIN_EXPORT_STORAGE_PROVIDER currently supports only local")
    if settings.admin_export_queue_provider not in SUPPORTED_ADMIN_EXPORT_QUEUE_PROVIDERS:
        violations.append("ADMIN_EXPORT_QUEUE_PROVIDER currently supports only database")
    if settings.admin_export_alert_provider not in SUPPORTED_ADMIN_EXPORT_ALERT_PROVIDERS:
        violations.append("ADMIN_EXPORT_ALERT_PROVIDER currently supports only disabled")

    if settings.environment.lower() != "production":
        if violations:
            raise SettingsValidationError("; ".join(violations))
        return

    if not settings.security.cookie_secure:
        violations.append("COOKIE_SECURE=true is required in production")
    if not settings.database.password.strip():
        violations.append("DB_PASSWORD is required in production")
    if settings.security.mockpay_callback_secret.strip() in MOCKPAY_CALLBACK_SECRET_PLACEHOLDERS:
        violations.append("MOCKPAY_CALLBACK_SECRET must be set to a non-default value in production")
    if not settings.cors.allowed_origins:
        violations.append("CORS_ALLOWED_ORIGINS must list explicit production origins")
    for origin in settings.cors.allowed_origins:
        error = validate_production_origin(origin)
        if error:
            violations.append(f"CORS_ALLOWED_ORIGINS contains invalid origin {origin!r}: {error}")
    if settings.cors.allowed_origin_regex:
        violations.append("CORS_ALLOWED_ORIGIN_REGEX must be empty in production")

    if violations:
        raise SettingsValidationError("; ".join(violations))


@lru_cache
def get_settings() -> AppSettings:
    settings = AppSettings(
        app_name=os.getenv("APP_NAME", AppSettings.app_name),
        app_version=os.getenv("APP_VERSION", AppSettings.app_version),
        environment=normalize_environment(os.getenv("APP_ENV")),
        payment_provider=normalize_payment_provider(os.getenv("PAYMENT_PROVIDER")),
        admin_export_storage_provider=normalize_admin_export_storage_provider(
            os.getenv("ADMIN_EXPORT_STORAGE_PROVIDER"),
        ),
        admin_export_storage_dir=os.getenv("ADMIN_EXPORT_STORAGE_DIR", AppSettings.admin_export_storage_dir),
        admin_export_queue_provider=normalize_admin_export_queue_provider(os.getenv("ADMIN_EXPORT_QUEUE_PROVIDER")),
        admin_export_alert_provider=normalize_admin_export_alert_provider(os.getenv("ADMIN_EXPORT_ALERT_PROVIDER")),
        database=DatabaseSettings(
            host=os.getenv("DB_HOST", DatabaseSettings.host),
            port=parse_int_env("DB_PORT", DatabaseSettings.port),
            database=os.getenv("DB_NAME", DatabaseSettings.database),
            user=os.getenv("DB_USER", DatabaseSettings.user),
            password=os.getenv("DB_PASSWORD", DatabaseSettings.password),
            sslmode=os.getenv("DB_SSLMODE", DatabaseSettings.sslmode),
        ),
        security=SecuritySettings(
            session_cookie_name=os.getenv("SESSION_COOKIE_NAME", SecuritySettings.session_cookie_name),
            admin_session_cookie_name=os.getenv("ADMIN_SESSION_COOKIE_NAME", SecuritySettings.admin_session_cookie_name),
            csrf_cookie_name=os.getenv("CSRF_COOKIE_NAME", SecuritySettings.csrf_cookie_name),
            csrf_header_name=os.getenv("CSRF_HEADER_NAME", SecuritySettings.csrf_header_name),
            cookie_samesite=os.getenv("COOKIE_SAMESITE", SecuritySettings.cookie_samesite),
            cookie_secure=parse_bool_env("COOKIE_SECURE", SecuritySettings.cookie_secure),
            session_ttl_seconds=parse_int_env("SESSION_TTL_SECONDS", SecuritySettings.session_ttl_seconds),
            sms_provider=normalize_sms_provider(os.getenv("SMS_PROVIDER")),
            login_rate_limit_provider=normalize_login_rate_limit_provider(os.getenv("LOGIN_RATE_LIMIT_PROVIDER")),
            login_rate_limit_max_attempts=parse_int_env(
                "LOGIN_RATE_LIMIT_MAX_ATTEMPTS",
                SecuritySettings.login_rate_limit_max_attempts,
            ),
            login_rate_limit_window_seconds=parse_int_env(
                "LOGIN_RATE_LIMIT_WINDOW_SECONDS",
                SecuritySettings.login_rate_limit_window_seconds,
            ),
            mockpay_callback_secret=os.getenv(
                "MOCKPAY_CALLBACK_SECRET",
                SecuritySettings.mockpay_callback_secret,
            ),
            mockpay_callback_tolerance_seconds=parse_int_env(
                "MOCKPAY_CALLBACK_TOLERANCE_SECONDS",
                SecuritySettings.mockpay_callback_tolerance_seconds,
            ),
        ),
        cors=CorsSettings(
            allowed_origins=parse_csv_env("CORS_ALLOWED_ORIGINS"),
            allowed_origin_regex=parse_optional_env("CORS_ALLOWED_ORIGIN_REGEX", CorsSettings.allowed_origin_regex),
        ),
    )
    validate_settings(settings)
    return settings
