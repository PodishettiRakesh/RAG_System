import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SessionResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier for conversation history")


class SessionMessage(BaseModel):
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    message_id: str = Field(..., description="Unique message identifier")


class SessionHistoryResponse(BaseModel):
    session_id: str = Field(..., description="Session identifier for conversation history")
    history: List[SessionMessage] = Field(..., description="Ordered conversation history")


# In-memory session store for version 1
session_store: Dict[str, List[Dict[str, str]]] = {}
MAX_HISTORY_TURNS = 10


def create_session() -> str:
    session_id = str(uuid.uuid4())
    session_store.setdefault(session_id, [])
    return session_id


def clear_session_history(session_id: str) -> None:
    session_store.pop(session_id, None)


def get_session_history(session_id: str) -> List[Dict[str, str]]:
    return session_store.get(session_id, [])


def get_recent_history(session_id: str, max_turns: int = MAX_HISTORY_TURNS) -> List[Dict[str, str]]:
    return get_session_history(session_id)[-max_turns:]


def save_session_message(session_id: str, role: str, content: str) -> Dict[str, str]:
    if not session_id:
        return {}
    message = {
        "role": role,
        "content": content,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "message_id": str(uuid.uuid4()),
    }
    session_store.setdefault(session_id, []).append(message)
    return message
