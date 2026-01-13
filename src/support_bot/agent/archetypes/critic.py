from __future__ import annotations

from dataclasses import dataclass

from support_bot.agent.core.models import ToolResult
from support_bot.agent.governance.safety_guard import SafetyGuard


@dataclass
class Critic:
    safety: SafetyGuard

    def review(self, *, response_text: str, tool_results: list[ToolResult]) -> str:
        text = (response_text or "").strip()
        if not text:
            text = "Sorry — I couldn't produce a response."

        decision = self.safety.validate_output(text)
        if not decision.ok:
            return decision.error or "Sorry — output blocked by safety policy."

        # Surface tool errors politely (minimal pass).
        errors = [tr for tr in tool_results if not tr.ok and tr.error]
        if errors:
            # Keep it compact; do not dump stack traces.
            text = text + " (Some tools failed: " + ", ".join(f"{e.name}" for e in errors) + ")"

        return text
