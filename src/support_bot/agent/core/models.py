from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class AgentInput:
    user_text: str
    debug: bool = False
    session_id: str | None = None


@dataclass(frozen=True)
class AgentContext:
    language: Literal["en", "bg"]
    normalized_text: str
    order_id: str | None = None
    product_term: str | None = None
    memory: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class PlanStep:
    kind: Literal["tool", "respond"]
    tool_call: ToolCall | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ToolResult:
    name: str
    ok: bool
    data: Any = None
    error: str | None = None


@dataclass(frozen=True)
class TraceEvent:
    ts: float
    stage: str
    message: str
    data: dict[str, Any] | None = None


@dataclass
class AgentOutput:
    response_text: str
    tools_called: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    debug: dict[str, Any] = field(default_factory=dict)
