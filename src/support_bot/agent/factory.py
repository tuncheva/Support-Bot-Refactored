from __future__ import annotations

from support_bot.agent.archetypes.context_builder import ContextBuilder
from support_bot.agent.archetypes.critic import Critic
from support_bot.agent.archetypes.executor import Executor
from support_bot.agent.archetypes.planner import Planner
from support_bot.agent.archetypes.reporter import Reporter
from support_bot.agent.archetypes.run_manager import RunManager
from support_bot.agent.governance.memory_manager import MemoryManager
from support_bot.agent.governance.safety_guard import SafetyGuard


_DEFAULT_AGENT: RunManager | None = None


def build_default_agent() -> RunManager:
    """Build (and memoize) the default meta-agent used by the chat handler."""

    global _DEFAULT_AGENT
    if _DEFAULT_AGENT is not None:
        return _DEFAULT_AGENT

    safety = SafetyGuard()
    memory = MemoryManager()

    context_builder = ContextBuilder(memory=memory)
    planner = Planner()
    executor = Executor()
    reporter = Reporter()
    critic = Critic(safety=safety)

    _DEFAULT_AGENT = RunManager(
        safety=safety,
        context_builder=context_builder,
        planner=planner,
        executor=executor,
        critic=critic,
        reporter=reporter,
    )
    return _DEFAULT_AGENT
