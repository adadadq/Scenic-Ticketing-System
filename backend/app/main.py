import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.admin_audit_logs import router as admin_audit_logs_router
from app.api.admin_auth import router as admin_auth_router
from app.api.admin_check_ins import check_in_failure_logs_router as admin_check_in_failure_logs_router
from app.api.admin_check_ins import check_in_logs_router as admin_check_in_logs_router
from app.api.admin_check_ins import router as admin_check_ins_router
from app.api.admin_exports import alert_events_router as admin_export_alert_events_router
from app.api.admin_exports import router as admin_exports_router
from app.api.admin_orders import router as admin_orders_router
from app.api.admin_reports import router as admin_reports_router
from app.api.admin_refunds import refund_logs_export_router as admin_refund_logs_export_router
from app.api.admin_refunds import refund_logs_router as admin_refund_logs_router
from app.api.admin_refunds import router as admin_refunds_router
from app.api.admin_settings import router as admin_settings_router
from app.api.admin_tickets import router as admin_tickets_router
from app.api.announcements import router as announcements_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.health import router as health_router
from app.api.orders import router as orders_router
from app.api.passengers import router as passengers_router
from app.api.payment_callbacks import router as payment_callbacks_router
from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from app.core.request_logging import elapsed_ms, log_request_summary
from app.schemas.common import ApiFailureDTO
from app.services.auth import InMemoryFailedLoginRateLimiter, InMemoryLoginRateLimiter
from app.services.admin_exports import (
    ADMIN_EXPORT_JOB_FILE_FORMAT_OPTIONS,
    ADMIN_EXPORT_JOB_STATUS_OPTIONS,
    ADMIN_EXPORT_JOB_TYPE_OPTIONS,
)
from app.services.orders import (
    ADMIN_ORDER_STATUS_FILTER_OPTIONS,
    ADMIN_PAYMENT_STATUS_FILTER_OPTIONS,
    ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS,
    CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS,
    ORDER_STATUS_FILTER_OPTIONS,
)


CSRF_PROTECTED_POST_PATHS = (
    "/api/auth/visitor/login",
    "/api/auth/visitor/register",
    "/api/auth/logout",
    "/api/admin/auth/login",
    "/api/admin/auth/logout",
    "/api/admin/announcements/current",
    "/api/admin/check-ins",
    "/api/admin/check-ins/batch",
    "/api/admin/check-ins/batch/undo",
    "/api/admin/check-ins/{ticket_code}/undo",
    "/api/admin/export-job-alert-events/{event_id}/acknowledge",
    "/api/admin/export-job-alert-events/batch-acknowledge",
    "/api/admin/export-job-alert-events/batch-delete",
    "/api/admin/export-job-alert-events/{event_id}/close",
    "/api/admin/export-job-alert-events/batch-close",
    "/api/admin/export-job-alert-events/{event_id}/reopen",
    "/api/admin/export-jobs",
    "/api/admin/export-jobs/{job_id}/retry",
    "/api/admin/orders/{order_no}/refund",
    "/api/admin/orders/{order_no}/refund/items",
    "/api/admin/tickets",
    "/api/orders",
    "/api/me/passenger-templates",
    "/api/orders/{order_no}/pay",
    "/api/orders/{order_no}/cancel",
)

CSRF_PROTECTED_DELETE_PATHS = (
    "/api/admin/export-job-alert-events/{event_id}",
    "/api/admin/tickets/{ticket_id}",
    "/api/me/passenger-templates/{template_id}",
)

CSRF_PROTECTED_PATCH_PATHS = (
    "/api/admin/auth/profile",
    "/api/admin/settings",
    "/api/admin/tickets/{ticket_id}",
    "/api/me/passenger-templates/{template_id}",
)


def api_failure_response(description: str) -> dict:
    return {
        "description": description,
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/ApiFailureDTO"},
            },
        },
    }


def request_id_response_header() -> dict:
    return {
        "description": "Request id echoed in the response body request_id field.",
        "schema": {"type": "string"},
    }


def install_openapi_contract(app: FastAPI, title: str, version: str, csrf_header_name: str) -> None:
    def mark_header_required(openapi_schema: dict, path: str, method: str, header_name: str) -> None:
        operation = openapi_schema.get("paths", {}).get(path, {}).get(method)
        if not operation:
            return
        parameters = operation.setdefault("parameters", [])
        for parameter in parameters:
            if parameter.get("in") == "header" and parameter.get("name") == header_name:
                parameter["required"] = True
                return
        parameters.append(
            {
                "name": header_name,
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
            }
        )

    def mark_query_string_enum(
        openapi_schema: dict,
        path: str,
        method: str,
        parameter_name: str,
        enum_values: list[str],
    ) -> None:
        operation = openapi_schema.get("paths", {}).get(path, {}).get(method)
        if not operation:
            return
        for parameter in operation.get("parameters", []):
            if parameter.get("in") != "query" or parameter.get("name") != parameter_name:
                continue
            schema = parameter.setdefault("schema", {})
            candidate_schemas = schema.get("anyOf") if isinstance(schema.get("anyOf"), list) else [schema]
            for candidate_schema in candidate_schemas:
                if candidate_schema.get("type") == "string":
                    candidate_schema["enum"] = enum_values
                    return
            schema["enum"] = enum_values
            return

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=title,
            version=version,
            routes=app.routes,
        )
        schemas = openapi_schema.setdefault("components", {}).setdefault("schemas", {})
        schemas["ApiFailureDTO"] = ApiFailureDTO.model_json_schema(ref_template="#/components/schemas/{model}")
        schemas.pop("HTTPValidationError", None)
        schemas.pop("ValidationError", None)

        for path_item in openapi_schema.get("paths", {}).values():
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                responses = operation.setdefault("responses", {})
                if "422" in responses:
                    responses["422"] = api_failure_response("Validation Error")
                responses.setdefault("default", api_failure_response("Error Response"))
                for response in responses.values():
                    if not isinstance(response, dict):
                        continue
                    response.setdefault("headers", {})["x-request-id"] = request_id_response_header()
        for path in CSRF_PROTECTED_POST_PATHS:
            mark_header_required(openapi_schema, path, "post", csrf_header_name)
        for path in CSRF_PROTECTED_PATCH_PATHS:
            mark_header_required(openapi_schema, path, "patch", csrf_header_name)
        for path in CSRF_PROTECTED_DELETE_PATHS:
            mark_header_required(openapi_schema, path, "delete", csrf_header_name)
        mark_header_required(openapi_schema, "/api/orders/{order_no}/pay", "post", "Idempotency-Key")
        mark_header_required(openapi_schema, "/api/payments/mock/callback", "post", "X-Mockpay-Timestamp")
        mark_header_required(openapi_schema, "/api/payments/mock/callback", "post", "X-Mockpay-Signature")
        mark_query_string_enum(
            openapi_schema,
            "/api/me/orders",
            "get",
            "status",
            list(ORDER_STATUS_FILTER_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/orders",
            "get",
            "status",
            list(ADMIN_ORDER_STATUS_FILTER_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/orders",
            "get",
            "paymentStatus",
            list(ADMIN_PAYMENT_STATUS_FILTER_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/refund-logs",
            "get",
            "refundType",
            list(ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/refund-logs.csv",
            "get",
            "refundType",
            list(ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/refund-logs.xlsx",
            "get",
            "refundType",
            list(ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/check-in-failure-logs",
            "get",
            "failureCode",
            list(CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/check-in-failure-logs.csv",
            "get",
            "failureCode",
            list(CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/check-in-failure-logs.xlsx",
            "get",
            "failureCode",
            list(CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/export-jobs",
            "get",
            "exportType",
            list(ADMIN_EXPORT_JOB_TYPE_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/export-jobs",
            "get",
            "fileFormat",
            list(ADMIN_EXPORT_JOB_FILE_FORMAT_OPTIONS),
        )
        mark_query_string_enum(
            openapi_schema,
            "/api/admin/export-jobs",
            "get",
            "status",
            list(ADMIN_EXPORT_JOB_STATUS_OPTIONS),
        )

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.state.login_rate_limiter = InMemoryLoginRateLimiter.from_settings(settings.security)
    app.state.admin_login_rate_limiter = InMemoryFailedLoginRateLimiter.from_settings(settings.security)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors.allowed_origins),
        allow_origin_regex=settings.cors.allowed_origin_regex,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Content-Type",
            "Idempotency-Key",
            settings.security.csrf_header_name,
            "x-request-id",
        ],
        expose_headers=["x-request-id", "Content-Disposition"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id") or f"req-{uuid4().hex}"
        request.state.request_id = request_id
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            log_request_summary(request, 500, elapsed_ms(start_time))
            raise
        response.headers["x-request-id"] = request_id
        log_request_summary(request, response.status_code, elapsed_ms(start_time))
        return response

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.include_router(admin_auth_router)
    app.include_router(admin_audit_logs_router)
    app.include_router(admin_check_in_failure_logs_router)
    app.include_router(admin_check_in_logs_router)
    app.include_router(admin_check_ins_router)
    app.include_router(admin_export_alert_events_router)
    app.include_router(admin_exports_router)
    app.include_router(admin_orders_router)
    app.include_router(admin_reports_router)
    app.include_router(admin_refund_logs_export_router)
    app.include_router(admin_refund_logs_router)
    app.include_router(admin_refunds_router)
    app.include_router(admin_settings_router)
    app.include_router(admin_tickets_router)
    app.include_router(announcements_router)
    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(orders_router)
    app.include_router(passengers_router)
    app.include_router(payment_callbacks_router)
    app.include_router(health_router)
    install_openapi_contract(app, settings.app_name, settings.app_version, settings.security.csrf_header_name)
    return app


app = create_app()
