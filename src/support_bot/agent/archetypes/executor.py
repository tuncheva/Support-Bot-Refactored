from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from support_bot.agent.core.models import AgentContext, PlanStep, ToolResult
from support_bot.services.order_status import getOrderStatus
from support_bot.services.product_catalog import file_search_products


@dataclass
class ExecutionState:
    products_found: list[dict[str, Any]]
    order_info: dict[str, Any] | None


@dataclass
class Executor:
    """Executes tool calls described by PlanSteps."""

    def execute(self, steps: list[PlanStep], context: AgentContext) -> tuple[list[ToolResult], ExecutionState]:
        tool_results: list[ToolResult] = []
        products_found: list[dict[str, Any]] = []
        order_info: dict[str, Any] | None = None

        for step in steps:
            if step.kind != "tool" or not step.tool_call:
                continue

            name = step.tool_call.name
            try:
                if name == "getOrderStatus":
                    order_id = str(step.tool_call.args.get("order_id") or "").strip()
                    if not any(ch.isdigit() for ch in order_id):
                        raise ValueError("order_id is missing or invalid")
                    order_info = getOrderStatus(order_id)
                    tool_results.append(ToolResult(name=name, ok=True, data=order_info))

                elif name == "file_search_products":
                    keyword = str(step.tool_call.args.get("keyword") or "").strip()
                    language = str(step.tool_call.args.get("language") or context.language)
                    if not keyword:
                        raise ValueError("keyword is missing")

                    products_found = file_search_products(keyword, language=language)

                    # Multiword fallback: try last word first, then the rest.
                    if not products_found and " " in keyword:
                        words = keyword.split()
                        for search_word in [words[-1]] + words[:-1]:
                            products_found = file_search_products(search_word, language=language)
                            if products_found:
                                break

                    tool_results.append(ToolResult(name=name, ok=True, data=products_found))

                else:
                    raise ValueError(f"unknown tool: {name}")

            except Exception as e:
                tool_results.append(ToolResult(name=name, ok=False, data=None, error=str(e)))

        return tool_results, ExecutionState(products_found=products_found, order_info=order_info)
