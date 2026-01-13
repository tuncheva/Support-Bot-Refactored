from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from support_bot.agent.archetypes.context_builder import ContextBuilder
from support_bot.agent.archetypes.critic import Critic
from support_bot.agent.archetypes.executor import Executor, ExecutionState
from support_bot.agent.archetypes.planner import Planner
from support_bot.agent.archetypes.reporter import Reporter
from support_bot.agent.core.models import AgentInput, AgentOutput, PlanStep, ToolResult
from support_bot.agent.governance.safety_guard import SafetyGuard


@dataclass
class RunManager:
    safety: SafetyGuard
    context_builder: ContextBuilder
    planner: Planner
    executor: Executor
    critic: Critic
    reporter: Reporter

    def run(self, agent_input: AgentInput) -> AgentOutput:
        trace: list[dict[str, Any]] = []
        tools_called: list[dict[str, Any]] = []

        def emit(stage: str, message: str, data: dict[str, Any] | None = None) -> None:
            trace.append({"ts": time.time(), "stage": stage, "message": message, "data": data})

        emit("input", "received input", {"chars": len(agent_input.user_text or "")})

        decision = self.safety.validate_input(agent_input.user_text)
        if not decision.ok:
            emit("safety", "input blocked", {"error": decision.error})
            response_text = decision.error or "Input blocked by safety policy."
            return AgentOutput(
                response_text=response_text,
                tools_called=[],
                trace=trace,
                debug={"tools_called": [], "trace": trace},
            )

        context = self.context_builder.build(agent_input)
        emit(
            "context",
            "built context",
            {"language": context.language, "has_order": bool(context.order_id), "has_product": bool(context.product_term)},
        )

        plan: list[PlanStep] = self.planner.plan(context)
        emit("plan", "created plan", {"steps": [s.kind + (":" + (s.tool_call.name if s.tool_call else "")) for s in plan]})

        for step in plan:
            if step.kind == "tool" and step.tool_call:
                tools_called.append({"name": step.tool_call.name, "args": dict(step.tool_call.args)})

        tool_results: list[ToolResult]
        state: ExecutionState
        tool_results, state = self.executor.execute(plan, context)
        emit("tool", "executed tools", {"results": [{"name": r.name, "ok": r.ok} for r in tool_results]})

        response_text = self.reporter.format(context=context, state=state)
        emit("report", "formatted response", {"chars": len(response_text)})

        response_text = self.critic.review(response_text=response_text, tool_results=tool_results)
        emit("critic", "reviewed response", {"chars": len(response_text)})

        debug: dict[str, Any] = {"tools_called": tools_called, "trace": trace}

        # Web-only multi-turn UX hook: if we found multiple products, expose them in debug
        # so the Flask layer can stash them in the session.
        if len(state.products_found) > 1:
            debug["pending_product_matches"] = state.products_found[1:]

        emit("output", "returning output", {"debug": bool(agent_input.debug)})

        return AgentOutput(response_text=response_text, tools_called=tools_called, trace=trace, debug=debug)
