from starlette.requests import Request

from app.core.client_ip import get_client_ip


def make_request(client_host: str, headers: dict[str, str]) -> Request:
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
            "client": (client_host, 50000),
            "server": ("testserver", 80),
        }
    )


def test_client_ip_uses_forwarded_header_only_from_loopback_proxy():
    proxied = make_request(
        "127.0.0.1",
        {"x-forwarded-for": "198.51.100.23", "x-real-ip": "198.51.100.23"},
    )
    spoofed = make_request(
        "203.0.113.10",
        {"x-forwarded-for": "198.51.100.99", "x-real-ip": "198.51.100.99"},
    )

    assert get_client_ip(proxied) == "198.51.100.23"
    assert get_client_ip(spoofed) == "203.0.113.10"
