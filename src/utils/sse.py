"""Server-Sent Events (SSE) formatting utilities for streaming RAG responses."""

import json
from datetime import datetime, timezone
from typing import Any, Dict


def utc_timestamp() -> str:
    """Return ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


def format_sse(event: str, data: Dict[str, Any]) -> str:
    """
    Format a single SSE message.

    Args:
        event: SSE event type name
        data: JSON-serializable payload

    Returns:
        SSE-formatted string ending with double newline
    """
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


def sse_error(stage: str, message: str) -> str:
    """Format an error SSE event."""
    return format_sse("error", {"stage": stage, "message": message, "timestamp": utc_timestamp()})
