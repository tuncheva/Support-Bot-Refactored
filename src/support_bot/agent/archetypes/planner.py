from __future__ import annotations

from dataclasses import dataclass

from support_bot.agent.core.models import AgentContext, PlanStep, ToolCall


@dataclass
class Planner:
    """Rule-based planner for Module 1.

    Produces a list of steps (tool calls and/or a final respond step).
    """

    def plan(self, context: AgentContext) -> list[PlanStep]:
        steps: list[PlanStep] = []

        # Multi-tool policy: if both are present, do both.
        if context.product_term:
            steps.append(
                PlanStep(
                    kind="tool",
                    tool_call=ToolCall(
                        name="file_search_products",
                        args={"keyword": context.product_term, "language": context.language},
                    ),
                    notes="search product catalog",
                )
            )

        if context.order_id:
            steps.append(
                PlanStep(
                    kind="tool",
                    tool_call=ToolCall(name="getOrderStatus", args={"order_id": context.order_id}),
                    notes="fetch order status",
                )
            )

        if not steps:
            steps.append(PlanStep(kind="respond", notes="no tool required"))

        return steps
