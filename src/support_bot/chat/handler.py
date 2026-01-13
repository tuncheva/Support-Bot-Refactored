"""Chat handler: parse a user message and delegate to the meta-agent."""

from __future__ import annotations

from support_bot.agent.core.models import AgentInput
from support_bot.agent.factory import build_default_agent


def handle_user_query(user_input: str, debug: bool = False):
    """Handle a user query using the refactored meta-agent.

    Public API compatibility:
    - If `debug` is False: returns `str`.
    - If `debug` is True: returns `(str, dict)`.

    Debug payload is now standardized to include at least:
    - `tools_called`
    - `trace`
    """

    agent = build_default_agent()
    agent_output = agent.run(AgentInput(user_text=user_input or "", debug=debug))

    if debug:
        return agent_output.response_text, agent_output.debug
    return agent_output.response_text


def create_thread_and_ask(question: str):
    """Simulate creating a thread and asking the assistant; returns response and debug info."""

    return handle_user_query(question, debug=True)
