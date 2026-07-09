import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import SecuritySettings
from app.main import create_app


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_APP_ROOT = PROJECT_ROOT / "backend" / "app"
FRONTEND_SRC_ROOT = PROJECT_ROOT / "frontend" / "src"
FRONTEND_API_FILES = (
    PROJECT_ROOT / "frontend" / "src" / "shared" / "api" / "client.ts",
    PROJECT_ROOT / "frontend" / "src" / "shared" / "api" / "endpoints.ts",
)
FRONTEND_OPTIONAL_API_FILES = (
    PROJECT_ROOT / "frontend" / "src" / "shared" / "api" / "errors.ts",
    PROJECT_ROOT / "frontend" / "src" / "shared" / "api" / "response.ts",
    PROJECT_ROOT / "frontend" / "src" / "shared" / "api" / "searchBuilders.ts",
)
FRONTEND_LOCAL_ERROR_CODES = {"CSRF_TOKEN_MISSING", "INVALID_RESPONSE"}


@dataclass(frozen=True)
class FrontendApiRequest:
    method: str
    path: str
    response_type: str
    query_keys: frozenset[str]
    source: str
    call_text: str


def frontend_api_sources() -> dict[Path, str]:
    missing_files = [str(path) for path in FRONTEND_API_FILES if not path.exists()]
    assert not missing_files, f"frontend API files not found: {missing_files}"
    readable_files = FRONTEND_API_FILES + tuple(path for path in FRONTEND_OPTIONAL_API_FILES if path.exists())
    return {path: path.read_text(encoding="utf-8") for path in readable_files}


def frontend_api_file_source(file_name: str) -> str:
    for path, source in frontend_api_sources().items():
        if path.name == file_name:
            return source
    raise AssertionError(f"frontend API file {file_name} is not configured")


def optional_frontend_api_file_source(file_name: str, fallback_file_name: str) -> str:
    sources = frontend_api_sources()
    for path, source in sources.items():
        if path.name == file_name:
            return source
    for path, source in sources.items():
        if path.name == fallback_file_name:
            return source
    raise AssertionError(f"frontend API fallback file {fallback_file_name} is not configured")


def frontend_source_files() -> list[Path]:
    return sorted(path for path in FRONTEND_SRC_ROOT.rglob("*.ts*") if path.is_file())


def line_number(source: str, index: int) -> int:
    return source.count("\n", 0, index) + 1


def first_argument(call_text: str) -> str:
    match = re.match(r"apiRequest(?:<[^>]+>)?\(\s*(?P<path>'[^']+'|\"[^\"]+\"|`[^`]+`)", call_text, flags=re.DOTALL)
    assert match, f"apiRequest path must be an inline string or template literal: {call_text}"
    return match.group("path")


def response_type_argument(call_text: str) -> str:
    match = re.match(r"apiRequest<(?P<type>[^>]+)>\(", call_text, flags=re.DOTALL)
    assert match, f"apiRequest must declare its frontend response type: {call_text}"
    return re.sub(r"\s+", "", match.group("type"))


def query_keys_from_url_search_params(source_fragment: str) -> set[str]:
    keys: set[str] = set()
    for match in re.finditer(r"new\s+URLSearchParams\(\s*\{(?P<body>.*?)\}\s*\)", source_fragment, flags=re.DOTALL):
        keys.update(
            key_match.group("key")
            for key_match in re.finditer(r"\b(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*(?::|,|$)", match.group("body"))
        )
    keys.update(
        match.group("key")
        for match in re.finditer(r"\.set\(\s*['\"](?P<key>[A-Za-z_][A-Za-z0-9_]*)['\"]", source_fragment)
    )
    return keys


def query_keys_from_function(source: str, function_name: str) -> set[str]:
    body = None
    try:
        body, _body_start = function_body(source, function_name)
    except AssertionError:
        for helper_source in frontend_api_sources().values():
            try:
                body, _body_start = function_body(helper_source, function_name)
                break
            except AssertionError:
                continue
    assert body is not None, f"function {function_name} not found"
    keys = query_keys_from_url_search_params(body)
    assert keys, f"query helper function {function_name} does not expose static URLSearchParams keys"
    return keys


def query_keys_from_variable(source: str, call_start: int, variable_name: str) -> set[str]:
    assignment_pattern = re.compile(
        rf"\bconst\s+{re.escape(variable_name)}\s*=\s*(?P<body>.*?)(?=\n\s*(?:return\s+)?apiRequest|\n\s*const\s+\w+\s*=|\Z)",
        flags=re.DOTALL,
    )
    matches = [match for match in assignment_pattern.finditer(source, 0, call_start)]
    assert matches, f"query variable {variable_name} is not declared before apiRequest"

    keys = query_keys_from_url_search_params(matches[-1].group("body"))
    assert keys, f"query variable {variable_name} does not expose static URLSearchParams keys"
    return keys


def normalize_frontend_path(path_expression: str, source: str, call_start: int) -> tuple[str, frozenset[str]]:
    path = path_expression.strip()[1:-1]
    query_keys: set[str] = set()

    if "?" in path:
        path, query = path.split("?", 1)
        query_keys.update(query_keys_from_url_search_params(query))
        for variable_match in re.finditer(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\.toString\(\))?\}", query):
            query_keys.update(query_keys_from_variable(source, call_start, variable_match.group("name")))

    path = path.replace("${encodeURIComponent(orderNo)}", "{order_no}")
    path = path.replace("${orderNo}", "{order_no}")
    path = path.replace("${encodeURIComponent(jobId)}", "{job_id}")
    path = path.replace("${jobId}", "{job_id}")
    path = path.replace("${encodeURIComponent(ticketId)}", "{ticket_id}")
    path = path.replace("${ticketId}", "{ticket_id}")
    path = path.replace("${encodeURIComponent(templateId)}", "{template_id}")
    path = path.replace("${templateId}", "{template_id}")
    for function_match in re.finditer(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\([^)]*\)\}$", path):
        query_keys.update(query_keys_from_function(source, function_match.group("name")))
        path = path[: function_match.start()]
    for variable_match in re.finditer(r"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}$", path):
        query_keys.update(query_keys_from_variable(source, call_start, variable_match.group("name")))
        path = path[: variable_match.start()]

    assert "${" not in path, f"unsupported dynamic frontend API path: {path_expression}"
    return path, frozenset(query_keys)


def api_request_call_spans(source: str) -> list[tuple[int, int]]:
    starts = [
        match.start()
        for match in re.finditer(r"\bapiRequest(?:<[^>]+>)?\(", source)
        if not source[: match.start()].rstrip().endswith("function")
    ]
    spans: list[tuple[int, int]] = []
    for start in starts:
        index = source.find("(", start)
        depth = 0
        quote: str | None = None
        escaped = False
        while index < len(source):
            char = source[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in {"'", '"', "`"}:
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    spans.append((start, index + 1))
                    break
            index += 1
        assert len(spans) and spans[-1][0] == start, f"unterminated apiRequest call near offset {start}"
    return spans


def function_body(source: str, function_name: str) -> tuple[str, int]:
    match = re.search(rf"\bfunction\s+{re.escape(function_name)}\b|export\s+async\s+function\s+{re.escape(function_name)}\b", source)
    assert match, f"function {function_name} not found"

    signature_start = source.find("(", match.end())
    assert signature_start != -1, f"function {function_name} has no signature"

    _signature, signature_call_start = call_expression(source, re.escape(source[match.start() : signature_start]), match.start())
    brace_index = source.find("{", signature_call_start + len(_signature))
    assert brace_index != -1, f"function {function_name} has no body"

    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(brace_index, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace_index : index + 1], brace_index

    raise AssertionError(f"function {function_name} body is unterminated")


def method_body(source: str, method_name: str) -> tuple[str, int]:
    match = re.search(rf"\b{re.escape(method_name)}\s*\(", source)
    assert match, f"method {method_name} not found"

    signature_start = source.find("(", match.start())
    assert signature_start != -1, f"method {method_name} has no signature"

    _signature, signature_call_start = call_expression(source, re.escape(source[match.start() : signature_start]), match.start())
    brace_index = source.find("{", signature_call_start + len(_signature))
    assert brace_index != -1, f"method {method_name} has no body"

    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(brace_index, len(source)):
        char = source[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[brace_index : index + 1], brace_index

    raise AssertionError(f"method {method_name} body is unterminated")


def call_expression(source: str, callee_pattern: str, start_index: int = 0) -> tuple[str, int]:
    match = re.search(callee_pattern, source[start_index:])
    assert match, f"call expression {callee_pattern} not found"

    start = start_index + match.start()
    index = source.find("(", start)
    assert index != -1, f"call expression {callee_pattern} has no arguments"

    depth = 0
    quote: str | None = None
    escaped = False
    for cursor in range(index, len(source)):
        char = source[cursor]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[start : cursor + 1], start

    raise AssertionError(f"call expression {callee_pattern} is unterminated")


def api_request_method(call_text: str) -> str:
    method_match = re.search(r"method:\s*['\"](?P<method>[A-Z]+)['\"]", call_text)
    if method_match:
        return method_match.group("method").lower()
    assert "method:" not in call_text, f"apiRequest method must be an inline HTTP method literal: {call_text}"
    return "get"


def frontend_api_requests() -> set[FrontendApiRequest]:
    requests: set[FrontendApiRequest] = set()
    for path, source in frontend_api_sources().items():
        for start, end in api_request_call_spans(source):
            call_text = source[start:end]
            source_location = f"{path}:{line_number(source, start)}"
            try:
                path_expression = first_argument(call_text)
                response_type = response_type_argument(call_text)
                method = api_request_method(call_text)
                normalized_path, query_keys = normalize_frontend_path(path_expression, source, start)
            except AssertionError as exc:
                raise AssertionError(f"{source_location}: {exc}") from exc
            requests.add(
                FrontendApiRequest(
                    method=method,
                    path=normalized_path,
                    response_type=response_type,
                    query_keys=query_keys,
                    source=source_location,
                    call_text=call_text,
                )
            )

    assert requests, "no frontend apiRequest calls were parsed from shared API files"
    return requests


def test_frontend_shared_api_requests_exist_in_backend_openapi():
    openapi = create_app().openapi()
    backend_requests = {
        (method, path)
        for path, operations in openapi["paths"].items()
        for method in operations
        if method in {"get", "post", "put", "patch", "delete"}
    }

    frontend_requests = frontend_api_requests()
    frontend_method_paths = {(request.method, request.path) for request in frontend_requests}

    assert frontend_method_paths <= backend_requests, (
        "frontend shared API calls missing from backend OpenAPI: "
        f"{sorted(frontend_method_paths - backend_requests)}; "
        f"sources={sorted(request.source for request in frontend_requests)}"
    )


def test_frontend_shared_api_query_keys_exist_in_backend_openapi_parameters():
    openapi = create_app().openapi()
    backend_query_keys = {
        (method, path): {
            parameter["name"]
            for parameter in operation.get("parameters", [])
            if parameter.get("in") == "query"
        }
        for path, operations in openapi["paths"].items()
        for method, operation in operations.items()
        if method in {"get", "post", "put", "patch", "delete"}
    }

    missing_query_keys = {
        request.source: sorted(request.query_keys - backend_query_keys.get((request.method, request.path), set()))
        for request in frontend_api_requests()
        if request.query_keys - backend_query_keys.get((request.method, request.path), set())
    }

    assert not missing_query_keys, f"frontend query keys missing from backend OpenAPI parameters: {missing_query_keys}"


def test_frontend_shared_api_sends_backend_required_query_keys():
    openapi = create_app().openapi()
    backend_required_query_keys = {
        (method, path): {
            parameter["name"]
            for parameter in operation.get("parameters", [])
            if parameter.get("in") == "query" and parameter.get("required") is True
        }
        for path, operations in openapi["paths"].items()
        for method, operation in operations.items()
        if method in {"get", "post", "put", "patch", "delete"}
    }

    missing_required_query_keys = {
        request.source: sorted(backend_required_query_keys.get((request.method, request.path), set()) - request.query_keys)
        for request in frontend_api_requests()
        if backend_required_query_keys.get((request.method, request.path), set()) - request.query_keys
    }

    assert not missing_required_query_keys, (
        "frontend shared API calls do not send backend required query keys: "
        f"{missing_required_query_keys}"
    )


def openapi_success_data_schema(openapi: dict, method: str, path: str) -> dict:
    response_schema = openapi["paths"][path][method]["responses"]["200"]["content"]["application/json"]["schema"]
    wrapper_ref = response_schema["$ref"].removeprefix("#/components/schemas/")
    wrapper_schema = openapi["components"]["schemas"][wrapper_ref]

    assert wrapper_schema["properties"]["success"]["const"] is True
    return wrapper_schema["properties"]["data"]


def contract_schema(schema: dict) -> dict:
    return {
        key: contract_schema(value) if isinstance(value, dict) else value
        for key, value in schema.items()
        if key != "title"
    }


FRONTEND_RESPONSE_TYPE_SCHEMAS = {
    "AdminMe": {"$ref": "#/components/schemas/AdminMeDTO"},
    "AdminBatchCheckIn": {"$ref": "#/components/schemas/AdminBatchCheckInDTO"},
    "AdminBatchUndoCheckIn": {"$ref": "#/components/schemas/AdminBatchUndoCheckInDTO"},
    "AdminCheckIn": {"$ref": "#/components/schemas/AdminCheckInDTO"},
    "AdminCheckInFailureAuditLogList": {
        "$ref": "#/components/schemas/AdminCheckInFailureAuditLogListDTO"
    },
    "AdminExportJob": {"$ref": "#/components/schemas/AdminExportJobDTO"},
    "AdminExportJobList": {"$ref": "#/components/schemas/AdminExportJobListDTO"},
    "AdminDailyTrend[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/AdminDailyTrendDTO"},
    },
    "AdminHourlyTrend[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/AdminHourlyTrendDTO"},
    },
    "AdminMonthlyTrend[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/AdminMonthlyTrendDTO"},
    },
    "AdminOrderDetail": {"$ref": "#/components/schemas/AdminOrderDetailDTO"},
    "AdminOrderList": {"$ref": "#/components/schemas/AdminOrderListDTO"},
    "AdminPaymentReconciliation": {"$ref": "#/components/schemas/AdminPaymentReconciliationDTO"},
    "AdminProductBreakdown[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/AdminProductBreakdownDTO"},
    },
    "AdminReportSummary": {"$ref": "#/components/schemas/AdminReportSummaryDTO"},
    "AdminSystemSettings": {"$ref": "#/components/schemas/AdminSystemSettingsDTO"},
    "AdminTicket": {"$ref": "#/components/schemas/AdminTicketDTO"},
    "AdminTicket[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/AdminTicketDTO"},
    },
    "Announcement": {"$ref": "#/components/schemas/AnnouncementDTO"},
    "AdminRefundAuditLog[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/AdminRefundAuditLogDTO"},
    },
    "AdminRefundAuditLogList": {"$ref": "#/components/schemas/AdminRefundAuditLogListDTO"},
    "AdminRefund": {"$ref": "#/components/schemas/AdminRefundDTO"},
    "AdminPartialRefund": {"$ref": "#/components/schemas/AdminPartialRefundDTO"},
    "CsrfPayload": {"$ref": "#/components/schemas/CsrfPayloadDTO"},
    "DatabaseHealthPayload": {"$ref": "#/components/schemas/DatabaseHealthDTO"},
    "HealthPayload": {"$ref": "#/components/schemas/HealthDTO"},
    "LogoutPayload": {"$ref": "#/components/schemas/LogoutPayloadDTO"},
    "MyOrderDetail": {"$ref": "#/components/schemas/OrderMeDTO"},
    "OrderSummary": {"$ref": "#/components/schemas/OrderMeDTO"},
    "OrderSummary[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/OrderMeDTO"},
    },
    "ProductPublic[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/ProductPublicDTO"},
    },
    "PassengerTemplate": {"$ref": "#/components/schemas/PassengerTemplateDTO"},
    "PassengerTemplate[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/PassengerTemplateDTO"},
    },
    "TimeSlotPublic[]": {
        "type": "array",
        "items": {"$ref": "#/components/schemas/TimeSlotPublicDTO"},
    },
    "VisitorMe": {"$ref": "#/components/schemas/VisitorMeDTO"},
    "{deleted:boolean}": {"additionalProperties": True, "type": "object"},
}


def test_frontend_shared_api_response_types_match_backend_openapi_data_schema():
    openapi = create_app().openapi()

    mismatches = {
        request.source: {
            "request": f"{request.method.upper()} {request.path}",
            "frontend_response_type": request.response_type,
            "expected_schema": FRONTEND_RESPONSE_TYPE_SCHEMAS.get(request.response_type),
            "backend_data_schema": contract_schema(openapi_success_data_schema(openapi, request.method, request.path)),
        }
        for request in frontend_api_requests()
        if FRONTEND_RESPONSE_TYPE_SCHEMAS.get(request.response_type)
        != contract_schema(openapi_success_data_schema(openapi, request.method, request.path))
    }
    unknown_response_types = {
        request.source: request.response_type
        for request in frontend_api_requests()
        if request.response_type not in FRONTEND_RESPONSE_TYPE_SCHEMAS
    }

    assert not unknown_response_types, (
        "frontend apiRequest response types must be mapped to backend OpenAPI schemas: "
        f"{unknown_response_types}"
    )
    assert not mismatches, f"frontend response types do not match backend OpenAPI data schemas: {mismatches}"


def test_frontend_shared_api_client_sends_browser_credentials_for_session_cookie():
    client_source = frontend_api_file_source("client.ts")
    api_request_body, _body_start = function_body(client_source, "apiRequest")
    fetch_call, fetch_start = call_expression(api_request_body, r"\bfetch\b")
    fetch_location = f"{FRONTEND_API_FILES[0]}:{line_number(client_source, client_source.find(fetch_call))}"

    assert re.search(r"credentials:\s*['\"]include['\"]", fetch_call), (
        f"{fetch_location}: frontend apiRequest fetch options must send credentials: 'include' "
        "so the backend HTTP-only session cookie is included"
    )


def test_frontend_shared_api_client_can_read_documented_request_id_header():
    response_source = optional_frontend_api_file_source("response.ts", "client.ts")
    errors_source = optional_frontend_api_file_source("errors.ts", "client.ts")
    invalid_response_body, _body_start = function_body(response_source, "invalidResponse")
    api_error_constructor, _constructor_start = method_body(errors_source, "constructor")
    format_api_error_body, _format_start = function_body(errors_source, "formatApiError")
    openapi = create_app().openapi()

    if "REQUEST_ID_HEADER" in response_source:
        assert re.search(
            r"REQUEST_ID_HEADER\s*=\s*['\"]X-Request-Id['\"]",
            response_source,
        ), "response parser must keep the documented request id header name"
    assert re.search(
        r"request_id\s*:\s*response\.headers\.get\(\s*(?:REQUEST_ID_HEADER|['\"]X-Request-Id['\"])\s*\)\s*\?\?\s*['\"]['\"]",
        invalid_response_body,
    ), "invalidResponse must preserve the documented response header in ApiFailure.request_id"
    assert re.search(
        r"this\.requestId\s*=\s*error\.request_id",
        api_error_constructor,
    ), "ApiError must expose backend request_id as requestId"
    assert re.search(
        r"error\.requestId\s*\?.*?请求编号",
        format_api_error_body,
        flags=re.DOTALL,
    ), "formatApiError must include requestId in the displayed fallback message"
    for path, path_item in openapi["paths"].items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            for status_code, response in operation["responses"].items():
                header = response.get("headers", {}).get("x-request-id")
                assert header, f"{method.upper()} {path} {status_code} must document x-request-id"
                assert header["schema"] == {"type": "string"}


def test_frontend_shared_api_client_fetches_and_injects_csrf_for_mutations():
    client_source = frontend_api_file_source("client.ts")

    assert re.search(
        r"apiRequest(?:<[^>]+>)?\(\s*['\"]\/api\/auth\/csrf['\"].*?method:\s*['\"]GET['\"].*?skipCsrf:\s*true",
        client_source,
        flags=re.DOTALL,
    ), "getCsrfToken must fetch /api/auth/csrf with GET and skip CSRF bootstrap recursion"
    assert re.search(
        r"if\s*\(\s*isMutatingMethod\(method\)\s*&&\s*!options\.skipCsrf\s*\).*?await\s+getCsrfToken\(\).*?headers\.set\(csrfHeaderName,\s*token\)",
        client_source,
        flags=re.DOTALL,
    ), "frontend apiRequest must inject the backend-provided CSRF header for mutating methods"

    csrf_bypasses = {
        request.source: request.call_text
        for request in frontend_api_requests()
        if request.method != "get" and re.search(r"skipCsrf\s*:\s*true", request.call_text)
    }
    assert not csrf_bypasses, f"mutating frontend API calls must not skip CSRF: {csrf_bypasses}"


def test_frontend_shared_api_client_default_csrf_cookie_name_matches_backend_default():
    client_source = frontend_api_file_source("client.ts")
    cookie_name_match = re.search(
        r"const\s+CSRF_COOKIE_NAME\s*=\s*import\.meta\.env\.VITE_CSRF_COOKIE_NAME\s*\?\?\s*['\"](?P<name>[^'\"]+)['\"]",
        client_source,
    )

    assert cookie_name_match, (
        "frontend apiRequest must define CSRF_COOKIE_NAME from VITE_CSRF_COOKIE_NAME "
        "with a literal fallback matching backend SecuritySettings.csrf_cookie_name"
    )
    assert cookie_name_match.group("name") == SecuritySettings.csrf_cookie_name


def test_frontend_payment_call_sends_backend_idempotency_header_option():
    client_source = frontend_api_file_source("client.ts")
    openapi = create_app().openapi()
    pay_parameters = openapi["paths"]["/api/orders/{order_no}/pay"]["post"].get("parameters", [])

    idempotency_parameters = [
        parameter
        for parameter in pay_parameters
        if parameter.get("in") == "header" and parameter.get("name") == "Idempotency-Key"
    ]

    assert idempotency_parameters, "backend OpenAPI must document the payment Idempotency-Key header"
    assert idempotency_parameters[0].get("required") is True, (
        "backend OpenAPI must mark payment Idempotency-Key as required because runtime rejects missing keys"
    )
    assert "const IDEMPOTENCY_HEADER = 'Idempotency-Key'" in client_source
    assert re.search(
        r"if\s*\(\s*options\.idempotencyKey\s*\).*?headers\.set\(IDEMPOTENCY_HEADER,\s*options\.idempotencyKey\)",
        client_source,
        flags=re.DOTALL,
    ), "frontend apiRequest must forward options.idempotencyKey as the Idempotency-Key header"

    pay_requests = [
        request
        for request in frontend_api_requests()
        if request.method == "post" and request.path == "/api/orders/{order_no}/pay"
    ]

    assert len(pay_requests) == 1
    assert re.search(r"\bidempotencyKey\b", pay_requests[0].call_text), (
        "frontend ordersApi.pay must pass its idempotencyKey argument into apiRequest options"
    )


def test_frontend_api_error_code_branches_are_backed_by_backend_error_codes():
    frontend_compared_codes: dict[str, set[str]] = {}
    for path in frontend_source_files():
        source = path.read_text(encoding="utf-8")
        codes = {
            match.group("code")
            for match in re.finditer(r"\.code\s*={2,3}\s*['\"](?P<code>[A-Z0-9_]+)['\"]", source)
        }
        if codes:
            frontend_compared_codes[str(path.relative_to(PROJECT_ROOT))] = codes

    backend_error_codes: set[str] = set()
    for path in sorted(BACKEND_APP_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        backend_error_codes.update(
            match.group("code")
            for match in re.finditer(r"AppError\(\s*[^,\n]+,\s*['\"](?P<code>[A-Z0-9_]+)['\"]", source)
        )
        backend_error_codes.update(
            match.group("code")
            for match in re.finditer(
                r"error_response\([^,\n]+,\s*[^,\n]+,\s*['\"](?P<code>[A-Z0-9_]+)['\"]",
                source,
            )
        )

    unknown_codes = {
        source: sorted(codes - backend_error_codes - FRONTEND_LOCAL_ERROR_CODES)
        for source, codes in frontend_compared_codes.items()
        if codes - backend_error_codes - FRONTEND_LOCAL_ERROR_CODES
    }

    assert frontend_compared_codes, "frontend should have explicit ApiError.code branches for auth/order flows"
    assert "AUTH_REQUIRED" in backend_error_codes
    assert "HTTP_ERROR" in backend_error_codes
    assert not unknown_codes, (
        "frontend ApiError.code branches must match backend-produced error codes "
        f"or documented frontend-local codes {sorted(FRONTEND_LOCAL_ERROR_CODES)}: {unknown_codes}"
    )
