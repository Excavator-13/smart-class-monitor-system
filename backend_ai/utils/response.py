from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any
from uuid import uuid4

from flask import jsonify


TZ_SHANGHAI = timezone(timedelta(hours=8))


ERROR_MESSAGES = {
    0: "success",
    40001: "invalid parameter",
    40002: "no face detected",
    40003: "multiple faces detected",
    40401: "stream not found",
    50001: "ai model not loaded",
    50002: "video stream read failed",
    50003: "springboot alert persist failed",
    50004: "snapshot save failed",
}


def now_iso() -> str:
    return datetime.now(TZ_SHANGHAI).isoformat(timespec="seconds")


def new_trace_id() -> str:
    return f"req_{datetime.now(TZ_SHANGHAI).strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"


def envelope(
    data: Any = None,
    code: int = 0,
    message: str | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message if message is not None else ERROR_MESSAGES.get(code, "error"),
        "data": data,
        "timestamp": now_iso(),
        "trace_id": trace_id or new_trace_id(),
    }


def json_response(
    data: Any = None,
    code: int = 0,
    message: str | None = None,
    status: int = 200,
):
    return jsonify(envelope(data=data, code=code, message=message)), status


def error_response(code: int, message: str | None = None, status: int = 400):
    return json_response(data=None, code=code, message=message, status=status)

