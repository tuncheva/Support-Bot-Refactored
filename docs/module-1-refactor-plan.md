# Module 1 Refactor Plan — Modular Meta‑Agent Architecture

## Goal
Refactor the support bot to use a modular “meta‑agent” architecture under [`src/support_bot/agent/`](src/support_bot/agent:1) while keeping the public API stable:

- Keep [`handle_user_query()`](src/support_bot/chat/handler.py:12) signature and behavior (including `debug=True` returning `(response, debug_dict)`)
- Keep Flask endpoint [`api_chat()`](src/support_bot/web/app.py:77) working by delegating to the meta‑agent
- Preserve meaning and key fields in responses; keep debug output stable (tools called + trace)
- Continue using existing services:
  - [`getOrderStatus()`](src/support_bot/services/order_status.py:10)
  - [`file_search_products()`](src/support_bot/services/product_catalog.py:130)

## Constraints / Acceptance
- Terminal (CLI) and Flask app must run.
- Existing tests must pass; add new unit tests for:
  - routing (order vs product vs general)
  - product search behavior
  - order status behavior
  - bilingual handling
- Reasonable lint/type hints; no breaking API changes.

## High‑Level Approach
Introduce a default “meta‑agent” that orchestrates:

1. **Planner**: decides which tools (services) to use and in what order.
2. **ContextBuilder**: prepares structured context from user input and (stub) memory.
3. **Executor**: executes planned tool calls and builds a draft response.
4. **Critic**: validates output consistency and safety; minimal governance.
5. **Reporter**: formats final response + stable debug payload.
6. **RunManager**: owns run lifecycle, trace collection, and debug consolidation.

Keep **SafetyGuard** and **MemoryManager** as lightweight stubs initially, but include interfaces so later modules can expand governance/memory without changing the public API.

## Target Package Structure
Create the following tree under [`src/support_bot/agent/`](src/support_bot/agent:1):

- `core/` (data models)
  - `AgentInput`, `AgentOutput`
  - `PlanStep`, `ToolCall`, `ToolResult`
  - `RunTraceEvent`, `AgentRun`
- `archetypes/`
  - [`planner.py`](src/support_bot/agent/archetypes/planner.py:1)
  - [`context_builder.py`](src/support_bot/agent/archetypes/context_builder.py:1)
  - [`executor.py`](src/support_bot/agent/archetypes/executor.py:1)
  - [`critic.py`](src/support_bot/agent/archetypes/critic.py:1)
  - [`reporter.py`](src/support_bot/agent/archetypes/reporter.py:1)
  - [`run_manager.py`](src/support_bot/agent/archetypes/run_manager.py:1)
- `governance/`
  - [`safety_guard.py`](src/support_bot/agent/governance/safety_guard.py:1)
  - [`memory_manager.py`](src/support_bot/agent/governance/memory_manager.py:1)
- Wiring
  - [`factory.py`](src/support_bot/agent/factory.py:1) — constructs default agent used by chat handler

## Data Model Design (Core)
Use dataclasses (or pydantic only if already present; keep dependencies minimal). Include type hints.

### AgentInput
- `user_text: str`
- `debug: bool`
- Optional: `locale_hint: str | None` (if bilingual detection exists)
- Optional: `session_id: str | None` (for future memory)

### AgentOutput
- `response_text: str`
- `tools_called: list[str]` (stable; matches prior debug expectations)
- `trace: list[RunTraceEvent]` (new timeline)
- Optional: `debug: dict` (for backward compatibility; includes `tools_called` and `trace` at least)

### PlanStep / ToolCall / ToolResult
- `PlanStep`: `kind: Literal["tool", "respond"]`, `tool_call: ToolCall | None`, `notes: str | None`
- `ToolCall`: `name: str`, `args: dict[str, Any]`
- `ToolResult`: `name: str`, `ok: bool`, `data: Any`, `error: str | None`

### RunTraceEvent / AgentRun
- `RunTraceEvent`: `ts: float`, `stage: str`, `message: str`, `data: dict[str, Any] | None`
- `AgentRun`: `input: AgentInput`, `plan: list[PlanStep]`, `tool_results: list[ToolResult]`, `output: AgentOutput | None`

## Archetype Responsibilities

### Planner
- Input: `AgentInput` + context
- Output: `list[PlanStep]`
- Routing logic replaces old inline regex logic in [`handle_user_query()`](src/support_bot/chat/handler.py:12):
  - If text indicates order status → plan tool call `getOrderStatus`
  - If text indicates product search → plan tool call `file_search_products`
  - Else → plan direct response step

### ContextBuilder
- Builds normalized query, extracted entities (order id, product terms), and language hints.
- Calls `MemoryManager.get_context()` (stub) and returns merged context.

### Executor
- Executes tool steps:
  - `getOrderStatus(order_id=...)`
  - `file_search_products(query=..., limit=...)`
- Collects `ToolResult`s and synthesizes a draft response consistent with existing response meaning.

### Critic
- Minimal checks:
  - Ensure response is nonempty
  - Ensure tool results errors are surfaced politely
  - SafetyGuard validation (stub) to allow/block

### Reporter
- Produces final string response.
- Produces stable debug payload when `debug=True`:
  - `tools_called: list[str]`
  - `trace: list[dict]` (timeline events)
  - Any prior debug keys preserved if they exist today (to be verified)

### RunManager
- Owns an `AgentRun` lifecycle:
  - emit trace events for each stage (planner/context/executor/critic/reporter)
  - consolidate `tools_called`
  - return `AgentOutput`

## Governance Stubs

### SafetyGuard (minimal)
- `validate_input(text) -> ok/error`
- `validate_output(text) -> ok/error`
- Initially permissive, but provides hooks for later safety policies.

### MemoryManager (minimal)
- In‑memory no‑op stub or simple dict keyed by `session_id`.
- `get_context(session_id) -> dict`
- `store_turn(session_id, user_text, response_text)`

## Wiring / Factory
Implement [`build_default_agent()`](src/support_bot/agent/factory.py:1) returning a configured `RunManager` (or a thin `MetaAgent` facade) with default archetypes and governance objects.

The chat handler imports the factory to obtain a singleton default agent.

## Integration Steps
1. Add new package tree under [`src/support_bot/agent/`](src/support_bot/agent:1) with datamodels + archetypes + governance + factory.
2. Update [`handle_user_query()`](src/support_bot/chat/handler.py:12) to delegate:
   - `agent_output = default_agent.run(user_text, debug=debug, session_id=...)`
   - Return `agent_output.response_text` or `(response_text, debug_dict)`.
3. Ensure [`api_chat()`](src/support_bot/web/app.py:77) continues calling handler unchanged.
4. Keep debug stability:
   - Maintain `tools_called` list (names in call order)
   - Add `trace` timeline (stage + message + optional data)
5. Tests:
   - Add new unit tests for:
     - Order routing triggers `getOrderStatus`
     - Product routing triggers `file_search_products`
     - Non‑tool query returns general response
     - Bilingual queries (EN/BG) route correctly if previously supported
   - Preserve existing tests.
6. Update [`README.md`](README.md:1) with:
   - Architecture diagram/overview
   - Where to add new tools
   - How to run tests and server
   - “Lab guidance” for extending Planner/Critic/SafetyGuard

## Definition of Done Checklist
- Handler and Flask endpoint function signatures unchanged.
- All tests pass; new tests included.
- Running the web server works with the same request/response shape.
- `debug=True` includes `tools_called` and a `trace` timeline while keeping previous debug keys stable.
