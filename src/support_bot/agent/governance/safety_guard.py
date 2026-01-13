from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyDecision:
    ok: bool
    error: str | None = None


class SafetyGuard:
    """Minimal safety/gov stub.

    In Module 1, this remains permissive. It exists to demonstrate where governance
    policies would live later.
    """

    def validate_input(self, text: str) -> SafetyDecision:
        return SafetyDecision(ok=True, error=None)

    def validate_output(self, text: str) -> SafetyDecision:
        return SafetyDecision(ok=True, error=None)
