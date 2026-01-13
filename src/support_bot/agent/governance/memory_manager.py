from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryManager:
    """Minimal memory stub.

    Keeps a dict of session_id -> context dict. This is deliberately tiny for
    Module 1; it demonstrates where memory would be wired in.
    """

    store: dict[str, dict[str, Any]] = field(default_factory=dict)

    def get_context(self, session_id: str | None) -> dict[str, Any]:
        if not session_id:
            return {}
        return dict(self.store.get(session_id, {}))

    def store_turn(self, session_id: str | None, user_text: str, response_text: str) -> None:
        if not session_id:
            return
        # For now store only the last turn.
        self.store[session_id] = {"last_user_text": user_text, "last_response_text": response_text}
