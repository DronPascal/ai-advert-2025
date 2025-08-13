# ADR-0012: Dual Agents Handoff with Assistants API

## Status
Accepted

## Context
- Need to support agent-to-agent collaboration where Agent 2 validates/transforms output of Agent 1.
- App already uses OpenAI Assistants API v2 with threads and repository pattern.
- We require strong observability in UI to make orchestration understandable to users.

## Decision
- Implement two assistants and two threads (one per agent) with cached IDs.
- Define strict handoff signal: first line equals `HANDOFF_AGENT2`.
- Forward the remainder of Agent 1 final reply as-is to Agent 2 (payload).
- Add system dividers for handoff and acceptance in the chat stream.
- Persist user message locally immediately after sending to ensure stable UI.

## Implementation Details
- Domain: `AgentPrompts` provides `AGENT_1_SYSTEM_PROMPT`, `AGENT_2_SYSTEM_PROMPT`, and `extractPayloadForAgent2()`.
- Data: `AssistantsChatRepositoryImpl.sendMessageDualAgents()` orchestrates:
  1) Ensure Agent 1 assistant and thread; post user text; run; fetch A1 reply
  2) If A1 reply starts with `HANDOFF_AGENT2`, insert divider "Передача сообщения во 2-го агента"
  3) Ensure Agent 2 assistant and thread; post payload; insert divider "Сообщение принято агентом 2" (before reply)
  4) Run Agent 2; fetch reply; persist
- Presentation: ViewModel routes `SendMessage` to dual-agents method (MVP always-on).
- Observability: `SYSTEM` messages used by `MessageBubble` to render dividers with appropriate icons.

## Consequences
### Positive
- Clear, testable orchestration with explicit HANDOFF.
- Good UX transparency via system dividers and stable message persistence.
- Reuses existing Assistants/Threads architecture; minimal invasive changes.

### Negative
- Two parallel threads and stored assistants introduce additional state to manage.
- MVP hard-enables dual-agents; UI toggle deferred.

## Validation
- Build/tests pass; manual scenario validated: A1 clarifies; on HANDOFF header, payload sent to A2; acceptance badge appears before A2 reply.

## Future Work
- UI toggle; agent-specific resets; side-by-side view (payload vs rewritten); CI quality gates; token caps if needed.


