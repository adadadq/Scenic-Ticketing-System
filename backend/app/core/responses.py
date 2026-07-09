from typing import Any

from fastapi import Request


def success_response(request: Request, data: Any) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "request_id": request.state.request_id,
    }
