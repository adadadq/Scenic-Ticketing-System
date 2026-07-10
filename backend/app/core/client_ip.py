from __future__ import annotations

from ipaddress import ip_address

from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    client_host = request.client.host if request.client else ""
    candidates = [client_host]
    if _is_loopback(client_host):
        forwarded_for = request.headers.get("x-forwarded-for", "")
        candidates = [forwarded_for.split(",", 1)[0], request.headers.get("x-real-ip", ""), client_host]
    for candidate in candidates:
        value = candidate.strip()
        if not value:
            continue
        try:
            return str(ip_address(value))
        except ValueError:
            continue
    return None


def _is_loopback(value: str) -> bool:
    try:
        return ip_address(value).is_loopback
    except ValueError:
        return False
