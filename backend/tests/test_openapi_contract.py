import re
from pathlib import Path

from app.core.config import get_settings
from app.main import CSRF_PROTECTED_DELETE_PATHS, CSRF_PROTECTED_PATCH_PATHS, CSRF_PROTECTED_POST_PATHS, create_app
from app.services.admin_exports import (
    ADMIN_EXPORT_JOB_FILE_FORMAT_OPTIONS,
    ADMIN_EXPORT_JOB_STATUS_OPTIONS,
    ADMIN_EXPORT_JOB_TYPE_OPTIONS,
)
from app.services.orders import (
    ADMIN_ORDER_STATUS_FILTER_OPTIONS,
    ADMIN_PAYMENT_STATUS_FILTER_OPTIONS,
    CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS,
    ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS,
    ORDER_STATUS_FILTER_OPTIONS,
)


API_CONTRACT_PATH = Path(__file__).resolve().parents[2] / "docs" / "api-contract.md"


def response_schema(openapi: dict, path: str, method: str) -> dict:
    return openapi["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]


def resolve_ref(openapi: dict, schema: dict) -> dict:
    ref = schema["$ref"]
    name = ref.removeprefix("#/components/schemas/")
    return openapi["components"]["schemas"][name]


def assert_success_wrapper(schema: dict) -> dict:
    properties = schema["properties"]

    assert schema["type"] == "object"
    assert schema["required"] == ["success", "data", "request_id"]
    assert properties["success"]["const"] is True
    assert properties["request_id"]["type"] == "string"
    return properties["data"]


def assert_data_ref(openapi: dict, path: str, method: str, expected_ref: str) -> None:
    schema = resolve_ref(openapi, response_schema(openapi, path, method))
    data_schema = assert_success_wrapper(schema)

    assert data_schema == {"$ref": f"#/components/schemas/{expected_ref}"}


def assert_data_list_ref(openapi: dict, path: str, method: str, expected_ref: str) -> None:
    schema = resolve_ref(openapi, response_schema(openapi, path, method))
    data_schema = assert_success_wrapper(schema)

    assert data_schema["type"] == "array"
    assert data_schema["items"] == {"$ref": f"#/components/schemas/{expected_ref}"}


def assert_optional_string(schema: dict, *, min_length: int | None = None, max_length: int | None = None) -> None:
    string_schema = next(candidate for candidate in schema["anyOf"] if candidate.get("type") == "string")

    assert {"type": "null"} in schema["anyOf"]
    if min_length is not None:
        assert string_schema["minLength"] == min_length
    if max_length is not None:
        assert string_schema["maxLength"] == max_length


def test_openapi_documents_success_wrapper_and_frontend_dtos():
    openapi = create_app().openapi()

    assert_data_ref(openapi, "/api/health", "get", "HealthDTO")
    assert_data_ref(openapi, "/api/health/db", "get", "DatabaseHealthDTO")
    assert_data_ref(openapi, "/api/auth/csrf", "get", "CsrfPayloadDTO")
    assert_data_ref(openapi, "/api/auth/visitor/login", "post", "VisitorMeDTO")
    assert_data_ref(openapi, "/api/auth/visitor/register", "post", "VisitorMeDTO")
    assert_data_ref(openapi, "/api/auth/me", "get", "VisitorMeDTO")
    assert_data_ref(openapi, "/api/auth/logout", "post", "LogoutPayloadDTO")
    assert_data_ref(openapi, "/api/admin/auth/login", "post", "AdminMeDTO")
    assert_data_ref(openapi, "/api/admin/auth/me", "get", "AdminMeDTO")
    assert_data_ref(openapi, "/api/admin/auth/profile", "patch", "AdminMeDTO")
    assert_data_ref(openapi, "/api/admin/auth/logout", "post", "LogoutPayloadDTO")
    assert_data_ref(openapi, "/api/admin/export-jobs", "post", "AdminExportJobDTO")
    assert_data_ref(openapi, "/api/admin/export-jobs", "get", "AdminExportJobListDTO")
    assert_data_ref(openapi, "/api/admin/export-jobs/{job_id}", "get", "AdminExportJobDTO")
    assert_data_ref(openapi, "/api/admin/export-jobs/{job_id}/retry", "post", "AdminExportJobDTO")
    assert_data_ref(openapi, "/api/admin/export-job-alert-events", "get", "AdminExportJobAlertEventListDTO")
    assert_data_ref(
        openapi,
        "/api/admin/export-job-alert-events/summary",
        "get",
        "AdminExportJobAlertEventSummaryDTO",
    )
    assert_data_ref(
        openapi,
        "/api/admin/export-job-alert-events/{event_id}/acknowledge",
        "post",
        "AdminExportJobAlertEventDTO",
    )
    assert_data_ref(
        openapi,
        "/api/admin/export-job-alert-events/batch-acknowledge",
        "post",
        "AdminExportJobAlertEventBatchAcknowledgeDTO",
    )
    assert_data_ref(
        openapi,
        "/api/admin/export-job-alert-events/batch-delete",
        "post",
        "AdminExportJobAlertEventBatchDeleteDTO",
    )
    assert_data_ref(
        openapi,
        "/api/admin/export-job-alert-events/{event_id}/close",
        "post",
        "AdminExportJobAlertEventDTO",
    )
    assert_data_ref(
        openapi,
        "/api/admin/export-job-alert-events/batch-close",
        "post",
        "AdminExportJobAlertEventBatchCloseDTO",
    )
    assert_data_ref(
        openapi,
        "/api/admin/export-job-alert-events/{event_id}/reopen",
        "post",
        "AdminExportJobAlertEventDTO",
    )
    assert_data_ref(
        openapi,
        "/api/admin/export-job-alert-events/{event_id}",
        "delete",
        "AdminExportJobAlertEventDeleteDTO",
    )
    assert_data_ref(openapi, "/api/admin/orders", "get", "AdminOrderListDTO")
    assert_data_ref(openapi, "/api/admin/orders/{order_no}", "get", "AdminOrderDetailDTO")
    assert_data_list_ref(openapi, "/api/admin/orders/{order_no}/refund-logs", "get", "AdminRefundAuditLogDTO")
    assert_data_ref(openapi, "/api/admin/refund-logs", "get", "AdminRefundAuditLogListDTO")
    assert_data_ref(openapi, "/api/admin/check-ins", "post", "AdminCheckInDTO")
    assert_data_ref(openapi, "/api/admin/check-ins/batch", "post", "AdminBatchCheckInDTO")
    assert_data_ref(openapi, "/api/admin/check-ins/batch/undo", "post", "AdminBatchUndoCheckInDTO")
    assert_data_ref(openapi, "/api/admin/check-ins/{ticket_code}/undo", "post", "AdminUndoCheckInDTO")
    assert_data_list_ref(openapi, "/api/admin/check-ins/{ticket_code}/logs", "get", "AdminCheckInAuditLogDTO")
    assert_data_ref(openapi, "/api/admin/check-in-logs", "get", "AdminCheckInAuditLogListDTO")
    assert_data_ref(openapi, "/api/admin/check-in-failure-logs", "get", "AdminCheckInFailureAuditLogListDTO")
    assert_data_ref(openapi, "/api/admin/orders/{order_no}/refund", "post", "AdminRefundDTO")
    assert_data_ref(openapi, "/api/admin/orders/{order_no}/refund/items", "post", "AdminPartialRefundDTO")
    assert_data_ref(openapi, "/api/admin/reports/summary", "get", "AdminReportSummaryDTO")
    assert_data_ref(openapi, "/api/admin/reports/payment-reconciliation", "get", "AdminPaymentReconciliationDTO")
    assert_data_list_ref(openapi, "/api/admin/reports/product-breakdown", "get", "AdminProductBreakdownDTO")
    assert_data_list_ref(openapi, "/api/admin/reports/daily-trend", "get", "AdminDailyTrendDTO")
    assert_data_list_ref(openapi, "/api/admin/reports/hourly-trend", "get", "AdminHourlyTrendDTO")
    assert_data_list_ref(openapi, "/api/admin/reports/monthly-trend", "get", "AdminMonthlyTrendDTO")
    assert_data_ref(openapi, "/api/admin/settings", "get", "AdminSystemSettingsDTO")
    assert_data_ref(openapi, "/api/admin/settings", "patch", "AdminSystemSettingsDTO")
    assert_data_ref(openapi, "/api/payments/mock/callback", "post", "MockPaymentCallbackDTO")
    assert_data_list_ref(openapi, "/api/catalog/products", "get", "ProductPublicDTO")
    assert_data_list_ref(openapi, "/api/catalog/time-slots", "get", "TimeSlotPublicDTO")
    assert_data_ref(openapi, "/api/orders", "post", "OrderMeDTO")
    assert_data_list_ref(openapi, "/api/me/orders", "get", "OrderMeDTO")
    assert_data_ref(openapi, "/api/me/orders/{order_no}", "get", "OrderMeDTO")
    assert_data_ref(openapi, "/api/orders/{order_no}/pay", "post", "OrderMeDTO")
    assert_data_ref(openapi, "/api/orders/{order_no}/cancel", "post", "OrderMeDTO")


def test_openapi_documents_admin_export_alert_event_note_limits():
    openapi = create_app().openapi()
    schemas = openapi["components"]["schemas"]

    for request_schema_name in (
        "AdminExportJobAlertEventAcknowledgeRequest",
        "AdminExportJobAlertEventCloseRequest",
    ):
        request_schema = schemas[request_schema_name]
        assert request_schema["additionalProperties"] is False
        assert set(request_schema["properties"]) == {"note"}
        assert_optional_string(request_schema["properties"]["note"], max_length=200)

    batch_delete_request = schemas["AdminExportJobAlertEventBatchDeleteRequest"]
    assert batch_delete_request["additionalProperties"] is False
    assert batch_delete_request["required"] == ["eventIds"]
    assert set(batch_delete_request["properties"]) == {"eventIds"}
    event_ids_schema = batch_delete_request["properties"]["eventIds"]
    assert event_ids_schema["minItems"] == 1
    assert event_ids_schema["maxItems"] == 100
    assert event_ids_schema["uniqueItems"] is True
    assert event_ids_schema["items"]["minimum"] == 1

    batch_acknowledge_request = schemas["AdminExportJobAlertEventBatchAcknowledgeRequest"]
    assert batch_acknowledge_request["additionalProperties"] is False
    assert batch_acknowledge_request["required"] == ["eventIds"]
    assert set(batch_acknowledge_request["properties"]) == {"eventIds", "note"}
    event_ids_schema = batch_acknowledge_request["properties"]["eventIds"]
    assert event_ids_schema["minItems"] == 1
    assert event_ids_schema["maxItems"] == 100
    assert event_ids_schema["uniqueItems"] is True
    assert event_ids_schema["items"]["minimum"] == 1
    assert_optional_string(batch_acknowledge_request["properties"]["note"], max_length=200)

    batch_close_request = schemas["AdminExportJobAlertEventBatchCloseRequest"]
    assert batch_close_request["additionalProperties"] is False
    assert batch_close_request["required"] == ["eventIds"]
    assert set(batch_close_request["properties"]) == {"eventIds", "note"}
    event_ids_schema = batch_close_request["properties"]["eventIds"]
    assert event_ids_schema["minItems"] == 1
    assert event_ids_schema["maxItems"] == 100
    assert event_ids_schema["uniqueItems"] is True
    assert event_ids_schema["items"]["minimum"] == 1
    assert_optional_string(batch_close_request["properties"]["note"], max_length=200)


def test_openapi_documents_undo_check_in_reason_contract():
    openapi = create_app().openapi()
    schemas = openapi["components"]["schemas"]

    undo_request_body = openapi["paths"]["/api/admin/check-ins/{ticket_code}/undo"]["post"]["requestBody"]
    undo_body_schema = undo_request_body["content"]["application/json"]["schema"]
    undo_request = schemas["AdminUndoCheckInRequest"]
    batch_undo_request = schemas["AdminBatchUndoCheckInRequest"]
    audit_log_dto = schemas["AdminCheckInAuditLogDTO"]

    assert undo_request_body.get("required") is None
    assert {"$ref": "#/components/schemas/AdminUndoCheckInRequest"} in undo_body_schema["anyOf"]
    assert {"type": "null"} in undo_body_schema["anyOf"]

    assert undo_request["additionalProperties"] is False
    assert set(undo_request["properties"]) == {"reason"}
    assert_optional_string(undo_request["properties"]["reason"], min_length=1, max_length=100)

    assert batch_undo_request["additionalProperties"] is False
    assert batch_undo_request["required"] == ["ticketCodes"]
    assert set(batch_undo_request["properties"]) == {"ticketCodes", "reason"}
    assert_optional_string(batch_undo_request["properties"]["reason"], min_length=1, max_length=100)

    assert "reason" in audit_log_dto["properties"]
    assert_optional_string(audit_log_dto["properties"]["reason"])


def test_openapi_documents_time_slots_query_parameters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/catalog/time-slots"]["get"]["parameters"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in parameters
        if parameter["in"] == "query"
    }

    assert set(query_parameters) == {"visitDate", "ticketTypeId", "productId"}
    assert query_parameters["visitDate"]["required"] is False
    assert query_parameters["ticketTypeId"]["required"] is False
    assert query_parameters["productId"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["visitDate"]["schema"]["anyOf"]
    assert {"exclusiveMinimum": 0, "type": "integer"} in query_parameters["ticketTypeId"]["schema"]["anyOf"]
    assert {"exclusiveMinimum": 0, "type": "integer"} in query_parameters["productId"]["schema"]["anyOf"]


def test_openapi_documents_my_orders_status_filter_enum():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/me/orders"]["get"]["parameters"]
    status_parameter = next(
        parameter
        for parameter in parameters
        if parameter["in"] == "query" and parameter["name"] == "status"
    )
    candidate_schemas = status_parameter["schema"].get("anyOf", [status_parameter["schema"]])
    enum_values = [
        enum_value
        for candidate_schema in candidate_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]

    assert status_parameter["required"] is False
    assert enum_values == list(ORDER_STATUS_FILTER_OPTIONS)


def test_openapi_documents_admin_orders_filter_enums_and_pagination():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/orders"]["get"]["parameters"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in parameters
        if parameter["in"] == "query"
    }
    assert set(query_parameters) == {"status", "paymentStatus", "orderNo", "buyerPhone", "page", "pageSize"}

    status_schemas = query_parameters["status"]["schema"].get("anyOf", [query_parameters["status"]["schema"]])
    status_values = [
        enum_value
        for candidate_schema in status_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]
    payment_schemas = query_parameters["paymentStatus"]["schema"].get("anyOf", [query_parameters["paymentStatus"]["schema"]])
    payment_values = [
        enum_value
        for candidate_schema in payment_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]

    assert status_values == list(ADMIN_ORDER_STATUS_FILTER_OPTIONS)
    assert payment_values == list(ADMIN_PAYMENT_STATUS_FILTER_OPTIONS)
    assert query_parameters["page"]["schema"]["default"] == 1
    assert query_parameters["pageSize"]["schema"]["default"] == 20


def test_openapi_documents_admin_refund_log_search_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/refund-logs"]["get"]["parameters"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in parameters
        if parameter["in"] == "query"
    }
    assert set(query_parameters) == {
        "refundType",
        "orderNo",
        "operatorUsername",
        "dateFrom",
        "dateTo",
        "page",
        "pageSize",
    }

    refund_type_schemas = query_parameters["refundType"]["schema"].get(
        "anyOf",
        [query_parameters["refundType"]["schema"]],
    )
    refund_type_values = [
        enum_value
        for candidate_schema in refund_type_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]

    assert refund_type_values == list(ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS)
    assert query_parameters["page"]["schema"]["default"] == 1
    assert query_parameters["pageSize"]["schema"]["default"] == 20


def test_openapi_documents_admin_refund_log_csv_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/refund-logs.csv"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }
    response_content = operation["responses"]["200"]["content"]

    assert set(query_parameters) == {"refundType", "orderNo", "operatorUsername", "dateFrom", "dateTo"}
    refund_type_schemas = query_parameters["refundType"]["schema"].get(
        "anyOf",
        [query_parameters["refundType"]["schema"]],
    )
    refund_type_values = [
        enum_value
        for candidate_schema in refund_type_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]
    assert refund_type_values == list(ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS)
    assert query_parameters["dateFrom"]["required"] is False
    assert query_parameters["dateTo"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert response_content == {
        "text/csv": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }


def test_openapi_documents_admin_refund_log_xlsx_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/refund-logs.xlsx"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }
    response_content = operation["responses"]["200"]["content"]
    response_headers = operation["responses"]["200"]["headers"]

    assert set(query_parameters) == {"refundType", "orderNo", "operatorUsername", "dateFrom", "dateTo"}
    refund_type_schemas = query_parameters["refundType"]["schema"].get(
        "anyOf",
        [query_parameters["refundType"]["schema"]],
    )
    refund_type_values = [
        enum_value
        for candidate_schema in refund_type_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]
    assert refund_type_values == list(ADMIN_REFUND_AUDIT_LOG_TYPE_OPTIONS)
    assert query_parameters["dateFrom"]["required"] is False
    assert query_parameters["dateTo"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert response_content == {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert response_headers["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_check_in_log_search_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/check-in-logs"]["get"]["parameters"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in parameters
        if parameter["in"] == "query"
    }

    assert set(query_parameters) == {
        "ticketCode",
        "orderNo",
        "operatorUsername",
        "reason",
        "dateFrom",
        "dateTo",
        "page",
        "pageSize",
    }
    assert query_parameters["page"]["schema"]["default"] == 1
    assert query_parameters["pageSize"]["schema"]["default"] == 20
    assert query_parameters["ticketCode"]["required"] is False
    assert query_parameters["orderNo"]["required"] is False
    assert query_parameters["operatorUsername"]["required"] is False
    assert query_parameters["reason"]["required"] is False
    assert_optional_string(query_parameters["reason"]["schema"], max_length=100)
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]


def test_openapi_documents_admin_check_in_failure_log_search_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/check-in-failure-logs"]["get"]["parameters"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in parameters
        if parameter["in"] == "query"
    }

    assert set(query_parameters) == {
        "ticketCode",
        "failureCode",
        "operatorUsername",
        "dateFrom",
        "dateTo",
        "page",
        "pageSize",
    }
    failure_code_parameter = query_parameters["failureCode"]
    candidate_schemas = failure_code_parameter["schema"].get("anyOf", [failure_code_parameter["schema"]])
    failure_code_values = [
        enum_value
        for candidate_schema in candidate_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]
    assert failure_code_values == list(CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS)
    assert query_parameters["page"]["schema"]["default"] == 1
    assert query_parameters["pageSize"]["schema"]["default"] == 20
    assert query_parameters["ticketCode"]["required"] is False
    assert query_parameters["operatorUsername"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]


def test_openapi_documents_admin_export_job_filters():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/export-jobs"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }

    assert set(query_parameters) == {"exportType", "fileFormat", "status", "page", "pageSize"}
    export_type_schemas = query_parameters["exportType"]["schema"].get("anyOf", [query_parameters["exportType"]["schema"]])
    export_type_values = [
        enum_value
        for candidate_schema in export_type_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]
    status_schemas = query_parameters["status"]["schema"].get("anyOf", [query_parameters["status"]["schema"]])
    status_values = [
        enum_value
        for candidate_schema in status_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]
    file_format_schemas = query_parameters["fileFormat"]["schema"].get(
        "anyOf",
        [query_parameters["fileFormat"]["schema"]],
    )
    file_format_values = [
        enum_value
        for candidate_schema in file_format_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]

    assert export_type_values == list(ADMIN_EXPORT_JOB_TYPE_OPTIONS)
    assert file_format_values == list(ADMIN_EXPORT_JOB_FILE_FORMAT_OPTIONS)
    assert status_values == list(ADMIN_EXPORT_JOB_STATUS_OPTIONS)
    assert query_parameters["page"]["schema"]["default"] == 1
    assert query_parameters["pageSize"]["schema"]["default"] == 20


def test_openapi_documents_admin_export_job_download_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/export-jobs/{job_id}/download"]["get"]
    response = operation["responses"]["200"]

    assert response["content"] == {
        "text/csv; charset=utf-8": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        },
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        },
    }
    assert response["headers"]["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_check_in_log_csv_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/check-in-logs.csv"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }
    response_content = operation["responses"]["200"]["content"]

    assert set(query_parameters) == {"ticketCode", "orderNo", "operatorUsername", "reason", "dateFrom", "dateTo"}
    assert query_parameters["reason"]["required"] is False
    assert_optional_string(query_parameters["reason"]["schema"], max_length=100)
    assert query_parameters["dateFrom"]["required"] is False
    assert query_parameters["dateTo"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert response_content == {
        "text/csv": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }


def test_openapi_documents_admin_check_in_failure_log_csv_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/check-in-failure-logs.csv"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }
    failure_code_parameter = query_parameters["failureCode"]
    candidate_schemas = failure_code_parameter["schema"].get("anyOf", [failure_code_parameter["schema"]])
    failure_code_values = [
        enum_value
        for candidate_schema in candidate_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]
    response_content = operation["responses"]["200"]["content"]

    assert set(query_parameters) == {"ticketCode", "failureCode", "operatorUsername", "dateFrom", "dateTo"}
    assert failure_code_values == list(CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS)
    assert query_parameters["ticketCode"]["required"] is False
    assert query_parameters["operatorUsername"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert response_content == {
        "text/csv": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }


def test_openapi_documents_admin_check_in_failure_log_xlsx_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/check-in-failure-logs.xlsx"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }
    failure_code_parameter = query_parameters["failureCode"]
    candidate_schemas = failure_code_parameter["schema"].get("anyOf", [failure_code_parameter["schema"]])
    failure_code_values = [
        enum_value
        for candidate_schema in candidate_schemas
        for enum_value in candidate_schema.get("enum", [])
    ]
    response_content = operation["responses"]["200"]["content"]
    response_headers = operation["responses"]["200"]["headers"]

    assert set(query_parameters) == {"ticketCode", "failureCode", "operatorUsername", "dateFrom", "dateTo"}
    assert failure_code_values == list(CHECK_IN_FAILURE_AUDIT_LOG_CODE_OPTIONS)
    assert query_parameters["ticketCode"]["required"] is False
    assert query_parameters["operatorUsername"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert response_content == {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert response_headers["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_check_in_log_xlsx_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/check-in-logs.xlsx"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }
    response_content = operation["responses"]["200"]["content"]
    response_headers = operation["responses"]["200"]["headers"]

    assert set(query_parameters) == {"ticketCode", "orderNo", "operatorUsername", "reason", "dateFrom", "dateTo"}
    assert query_parameters["reason"]["required"] is False
    assert_optional_string(query_parameters["reason"]["schema"], max_length=100)
    assert query_parameters["dateFrom"]["required"] is False
    assert query_parameters["dateTo"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert response_content == {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert response_headers["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_report_summary_date_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/reports/summary"]["get"]["parameters"]
    assert_optional_date_range_parameters(parameters)


def test_openapi_documents_admin_payment_reconciliation_date_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/reports/payment-reconciliation"]["get"]["parameters"]
    assert_optional_date_range_parameters(parameters)


def test_openapi_documents_admin_payment_reconciliation_csv_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/reports/payment-reconciliation.csv"]["get"]
    assert_optional_date_range_parameters(operation["parameters"])
    assert operation["responses"]["200"]["content"] == {
        "text/csv": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert operation["responses"]["200"]["headers"]["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_payment_reconciliation_xlsx_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/reports/payment-reconciliation.xlsx"]["get"]
    assert_optional_date_range_parameters(operation["parameters"])
    assert operation["responses"]["200"]["content"] == {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert operation["responses"]["200"]["headers"]["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_product_breakdown_date_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/reports/product-breakdown"]["get"]["parameters"]
    assert_optional_date_range_parameters(parameters)


def test_openapi_documents_admin_product_breakdown_csv_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/reports/product-breakdown.csv"]["get"]
    assert_optional_date_range_parameters(operation["parameters"])
    assert operation["responses"]["200"]["content"] == {
        "text/csv": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert operation["responses"]["200"]["headers"]["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_product_breakdown_xlsx_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/reports/product-breakdown.xlsx"]["get"]
    assert_optional_date_range_parameters(operation["parameters"])
    assert operation["responses"]["200"]["content"] == {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert operation["responses"]["200"]["headers"]["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_daily_trend_date_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/reports/daily-trend"]["get"]["parameters"]
    assert_optional_trend_parameters(parameters)


def test_openapi_documents_admin_hourly_trend_date_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/reports/hourly-trend"]["get"]["parameters"]
    assert_optional_trend_parameters(parameters)


def test_openapi_documents_admin_monthly_trend_date_filters():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/admin/reports/monthly-trend"]["get"]["parameters"]
    assert_optional_trend_parameters(parameters)


def test_openapi_documents_admin_trend_csv_exports_as_file_responses():
    openapi = create_app().openapi()

    for path in (
        "/api/admin/reports/daily-trend.csv",
        "/api/admin/reports/hourly-trend.csv",
        "/api/admin/reports/monthly-trend.csv",
    ):
        operation = openapi["paths"][path]["get"]
        assert_optional_trend_parameters(operation["parameters"])
        assert operation["responses"]["200"]["content"] == {
            "text/csv": {
                "schema": {
                    "type": "string",
                    "format": "binary",
                }
            }
        }
        assert operation["responses"]["200"]["headers"]["Content-Disposition"]["schema"] == {"type": "string"}


def test_openapi_documents_admin_trend_xlsx_exports_as_file_responses():
    openapi = create_app().openapi()

    for path in (
        "/api/admin/reports/daily-trend.xlsx",
        "/api/admin/reports/hourly-trend.xlsx",
        "/api/admin/reports/monthly-trend.xlsx",
    ):
        operation = openapi["paths"][path]["get"]
        assert_optional_trend_parameters(operation["parameters"])
        assert operation["responses"]["200"]["content"] == {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
                "schema": {
                    "type": "string",
                    "format": "binary",
                }
            }
        }
        assert operation["responses"]["200"]["headers"]["Content-Disposition"]["schema"] == {"type": "string"}


def assert_optional_date_range_parameters(parameters: list[dict]) -> None:
    query_parameters = {
        parameter["name"]: parameter
        for parameter in parameters
        if parameter["in"] == "query"
    }

    assert set(query_parameters) == {"dateFrom", "dateTo"}
    assert query_parameters["dateFrom"]["required"] is False
    assert query_parameters["dateTo"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]


def assert_optional_trend_parameters(parameters: list[dict]) -> None:
    query_parameters = {
        parameter["name"]: parameter
        for parameter in parameters
        if parameter["in"] == "query"
    }

    assert set(query_parameters) == {"dateFrom", "dateTo", "includeEmpty"}
    assert query_parameters["dateFrom"]["required"] is False
    assert query_parameters["dateTo"]["required"] is False
    assert query_parameters["includeEmpty"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert query_parameters["includeEmpty"]["schema"] == {
        "type": "boolean",
        "default": False,
        "title": "Includeempty",
    }


def test_openapi_documents_admin_order_csv_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/reports/orders.csv"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }
    response_content = operation["responses"]["200"]["content"]

    assert set(query_parameters) == {"dateFrom", "dateTo"}
    assert query_parameters["dateFrom"]["required"] is False
    assert query_parameters["dateTo"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert response_content == {
        "text/csv": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }


def test_openapi_documents_admin_order_xlsx_export_as_file_response():
    openapi = create_app().openapi()

    operation = openapi["paths"]["/api/admin/reports/orders.xlsx"]["get"]
    query_parameters = {
        parameter["name"]: parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "query"
    }
    response_content = operation["responses"]["200"]["content"]
    response_headers = operation["responses"]["200"]["headers"]

    assert set(query_parameters) == {"dateFrom", "dateTo"}
    assert query_parameters["dateFrom"]["required"] is False
    assert query_parameters["dateTo"]["required"] is False
    assert {"format": "date", "type": "string"} in query_parameters["dateFrom"]["schema"]["anyOf"]
    assert {"format": "date", "type": "string"} in query_parameters["dateTo"]["schema"]["anyOf"]
    assert response_content == {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {
            "schema": {
                "type": "string",
                "format": "binary",
            }
        }
    }
    assert response_headers["Content-Disposition"]["schema"] == {"type": "string"}


def assert_failure_schema(openapi: dict, schema: dict) -> None:
    resolved_schema = resolve_ref(openapi, schema)
    properties = resolved_schema["properties"]

    assert resolved_schema["type"] == "object"
    assert resolved_schema["required"] == ["success", "code", "message", "request_id"]
    assert properties["success"]["const"] is False
    assert properties["code"]["type"] == "string"
    assert properties["message"]["type"] == "string"
    assert properties["request_id"]["type"] == "string"


def test_openapi_documents_frontend_error_contract_instead_of_fastapi_detail_shape():
    openapi = create_app().openapi()

    assert "ApiFailureDTO" in openapi["components"]["schemas"]
    assert "HTTPValidationError" not in openapi["components"]["schemas"]
    assert "ValidationError" not in openapi["components"]["schemas"]

    for path_item in openapi["paths"].values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue

            default_schema = operation["responses"]["default"]["content"]["application/json"]["schema"]
            assert default_schema == {"$ref": "#/components/schemas/ApiFailureDTO"}

            validation_response = operation["responses"].get("422")
            if validation_response:
                validation_schema = validation_response["content"]["application/json"]["schema"]
                assert validation_schema == {"$ref": "#/components/schemas/ApiFailureDTO"}

    assert_failure_schema(openapi, {"$ref": "#/components/schemas/ApiFailureDTO"})


def test_openapi_documents_request_id_response_header_for_all_operations():
    openapi = create_app().openapi()

    for path, path_item in openapi["paths"].items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            for status_code, response in operation["responses"].items():
                header = response.get("headers", {}).get("x-request-id")
                assert header, f"{method.upper()} {path} {status_code} must document x-request-id response header"
                assert header["schema"] == {"type": "string"}
                assert "request_id" in header["description"]


def test_openapi_documents_payment_idempotency_key_as_required_header():
    openapi = create_app().openapi()

    parameters = openapi["paths"]["/api/orders/{order_no}/pay"]["post"]["parameters"]
    idempotency_parameter = next(
        parameter
        for parameter in parameters
        if parameter["in"] == "header" and parameter["name"] == "Idempotency-Key"
    )

    assert idempotency_parameter["required"] is True


def test_openapi_documents_mock_payment_callback_signature_headers():
    openapi = create_app().openapi()
    csrf_header_name = get_settings().security.csrf_header_name

    timestamp_parameter = required_header_parameter(
        openapi,
        "/api/payments/mock/callback",
        "post",
        "X-Mockpay-Timestamp",
    )
    signature_parameter = required_header_parameter(
        openapi,
        "/api/payments/mock/callback",
        "post",
        "X-Mockpay-Signature",
    )
    callback_headers = {
        parameter["name"]
        for parameter in openapi["paths"]["/api/payments/mock/callback"]["post"].get("parameters", [])
        if parameter.get("in") == "header"
    }

    assert timestamp_parameter["required"] is True
    assert signature_parameter["required"] is True
    assert {"type": "string"} in timestamp_parameter["schema"].get("anyOf", [timestamp_parameter["schema"]])
    assert {"type": "string"} in signature_parameter["schema"].get("anyOf", [signature_parameter["schema"]])
    assert csrf_header_name not in callback_headers


def required_header_parameter(openapi: dict, path: str, method: str, header_name: str) -> dict:
    return next(
        parameter
        for parameter in openapi["paths"][path][method].get("parameters", [])
        if parameter.get("in") == "header" and parameter.get("name") == header_name
    )


def test_openapi_documents_csrf_header_as_required_for_state_changing_endpoints():
    openapi = create_app().openapi()
    csrf_header_name = get_settings().security.csrf_header_name

    for path in CSRF_PROTECTED_POST_PATHS:
        csrf_parameter = required_header_parameter(openapi, path, "post", csrf_header_name)
        assert csrf_parameter["required"] is True
        assert csrf_parameter["schema"]["type"] == "string"
    for path in CSRF_PROTECTED_PATCH_PATHS:
        csrf_parameter = required_header_parameter(openapi, path, "patch", csrf_header_name)
        assert csrf_parameter["required"] is True
        assert csrf_parameter["schema"]["type"] == "string"
    for path in CSRF_PROTECTED_DELETE_PATHS:
        csrf_parameter = required_header_parameter(openapi, path, "delete", csrf_header_name)
        assert csrf_parameter["required"] is True
        assert csrf_parameter["schema"]["type"] == "string"

    for path in [
        "/api/health",
        "/api/health/db",
        "/api/auth/csrf",
        "/api/auth/me",
        "/api/admin/auth/me",
        "/api/admin/export-job-alert-events",
        "/api/admin/export-job-alert-events/summary",
        "/api/admin/export-jobs",
        "/api/admin/export-jobs/{job_id}",
        "/api/admin/export-jobs/{job_id}/download",
        "/api/admin/orders",
        "/api/admin/orders/{order_no}",
        "/api/admin/orders/{order_no}/refund-logs",
        "/api/admin/check-ins/{ticket_code}/logs",
        "/api/admin/check-in-failure-logs",
        "/api/admin/check-in-failure-logs.csv",
        "/api/admin/check-in-failure-logs.xlsx",
        "/api/admin/check-in-logs",
        "/api/admin/check-in-logs.csv",
        "/api/admin/check-in-logs.xlsx",
        "/api/admin/refund-logs",
        "/api/admin/refund-logs.csv",
        "/api/admin/refund-logs.xlsx",
        "/api/admin/reports/summary",
        "/api/admin/reports/payment-reconciliation",
        "/api/admin/reports/payment-reconciliation.csv",
        "/api/admin/reports/payment-reconciliation.xlsx",
        "/api/admin/reports/product-breakdown",
        "/api/admin/reports/product-breakdown.csv",
        "/api/admin/reports/product-breakdown.xlsx",
        "/api/admin/reports/daily-trend",
        "/api/admin/reports/daily-trend.csv",
        "/api/admin/reports/daily-trend.xlsx",
        "/api/admin/reports/hourly-trend",
        "/api/admin/reports/hourly-trend.csv",
        "/api/admin/reports/hourly-trend.xlsx",
        "/api/admin/reports/monthly-trend",
        "/api/admin/reports/monthly-trend.csv",
        "/api/admin/reports/monthly-trend.xlsx",
        "/api/admin/reports/orders.csv",
        "/api/admin/reports/orders.xlsx",
        "/api/admin/settings",
        "/api/catalog/products",
        "/api/catalog/time-slots",
        "/api/me/orders",
        "/api/me/orders/{order_no}",
    ]:
        get_headers = {
            parameter["name"]
            for parameter in openapi["paths"][path]["get"].get("parameters", [])
            if parameter.get("in") == "header"
        }
        assert csrf_header_name not in get_headers


def test_openapi_uses_configured_csrf_header_name(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("CSRF_HEADER_NAME", "x-scenic-csrf")

    try:
        openapi = create_app().openapi()

        for path in CSRF_PROTECTED_POST_PATHS:
            header_names = {
                parameter["name"]
                for parameter in openapi["paths"][path]["post"].get("parameters", [])
                if parameter.get("in") == "header"
            }
            csrf_parameter = required_header_parameter(openapi, path, "post", "x-scenic-csrf")
            assert "x-scenic-csrf" in header_names
            assert "x-csrf-token" not in header_names
            assert csrf_parameter["required"] is True
        for path in CSRF_PROTECTED_PATCH_PATHS:
            header_names = {
                parameter["name"]
                for parameter in openapi["paths"][path]["patch"].get("parameters", [])
                if parameter.get("in") == "header"
            }
            csrf_parameter = required_header_parameter(openapi, path, "patch", "x-scenic-csrf")
            assert "x-scenic-csrf" in header_names
            assert "x-csrf-token" not in header_names
            assert csrf_parameter["required"] is True
        for path in CSRF_PROTECTED_DELETE_PATHS:
            header_names = {
                parameter["name"]
                for parameter in openapi["paths"][path]["delete"].get("parameters", [])
                if parameter.get("in") == "header"
            }
            csrf_parameter = required_header_parameter(openapi, path, "delete", "x-scenic-csrf")
            assert "x-scenic-csrf" in header_names
            assert "x-csrf-token" not in header_names
            assert csrf_parameter["required"] is True
    finally:
        get_settings.cache_clear()


def documented_api_contract_endpoints() -> set[tuple[str, str]]:
    contract = API_CONTRACT_PATH.read_text(encoding="utf-8")

    endpoints = {
        (match.group("method").lower(), match.group("path"))
        for match in re.finditer(
            r"^\s*(?P<method>GET|POST|PUT|PATCH|DELETE)\s+(?P<path>/api/[^\s`]+)\s*$",
            contract,
            flags=re.MULTILINE,
        )
    }

    assert endpoints, f"no API endpoints found in {API_CONTRACT_PATH}"
    return endpoints


def openapi_endpoints(openapi: dict) -> set[tuple[str, str]]:
    return {
        (method, path)
        for path, operations in openapi["paths"].items()
        for method in operations
        if method in {"get", "post", "put", "patch", "delete"}
    }


def test_api_contract_endpoint_inventory_matches_backend_openapi():
    documented_endpoints = documented_api_contract_endpoints()
    backend_endpoints = openapi_endpoints(create_app().openapi())

    assert documented_endpoints == backend_endpoints, (
        "docs/api-contract.md endpoint inventory must match backend OpenAPI: "
        f"missing_in_docs={sorted(backend_endpoints - documented_endpoints)}, "
        f"unknown_in_docs={sorted(documented_endpoints - backend_endpoints)}"
    )
