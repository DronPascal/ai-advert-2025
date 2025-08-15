# Active Context - AI Chat NextGen

## Current Focus
- Assistants API only; dual-agents orchestration (two assistants & threads) with automatic handoff
- Response format: thread-aware updates and resets on new thread
- Observability: system dividers for agent handoff and acceptance; stable message persistence
- UI polish: IME-aware chat and compact input; format indicator visibility after New Thread
- MCP web-search MVP: Agent 1 умеет вызывать локальный шлюз поиска (Docker) с инструментальным циклом ACTION/ARGS/OBSERVATION и обогащением контента

## Recent Changes
- Dual agents MVP implemented:
  - Added `AgentPrompts` with AGENT_1/2 system prompts and `HANDOFF_AGENT2` detector
  - Repository method `sendMessageDualAgents` orchestrates Agent1→(payload)→Agent2
  - System dividers: "Передача сообщения во 2-го агента" and "Сообщение принято агентом 2"
  - Badge "принято агентом 2" отображается до ответа агента 2
  - Persist user message immediately after sending to Agent 1 for stable UI
- Adopted gpt-4o-mini as the default model for Assistants (see ADR-0009) to reduce latency and cost.
- Centralized API authentication via OkHttp interceptor (no manual header wiring).
- System message dividers added for key events (format updates, new thread, history clear).
- System prompt revised to enforce clarification-first behavior; default instructions now allow multiple domain-specific questions in one turn when needed. Assistant runs pass temperature=0.2 for higher adherence and include concatenated default instructions + active format per thread.
- Keyboard/IME handling: use adjustResize + IME-aware paddings and autoscroll in chat. `LazyColumn` now uses `contentPadding` that accounts for IME height; added `LaunchedEffect` to keep last message visible when IME appears.
- Message input redesigned to be compact (reduced height, single-row default), preserved readability and accessibility.
- Detekt tuned for Android/Compose; static analysis and dead code pass clean.
- R8-based unused code pipeline: added `analyze` build type with `-printusage` (non-debuggable) and Gradle task `reportUnusedCode` producing `unused_code_report.md`.
- Architectural tests added with ArchUnit (no package cycles; layered dependencies) at `app/src/test/java/com/example/day1_ai_chat_nextgen/architecture/ArchitectureTest.kt`.
- Legacy analysis artifacts replaced by the new pipeline (removed `FINAL_UNUSED_CODE_ANALYSIS.md`, `REFACTORING_SUMMARY.md`, `scripts/find_unused_code.py`).

- MCP integration for Agent 1 (web search):
  - Локальный HTTP шлюз `day-6-mcp` (FastAPI, DDG/Wikipedia; опционально enrichment первой страницы)
  - В приложении: `McpBridgeApi`, DTO и DI; debug `BuildConfig.MCP_BRIDGE_URL = http://10.0.2.2:8765/`
  - Репозиторий: парсит `ACTION: web.search`, вызывает шлюз с `enrich=true`, публикует `OBSERVATION:` и перезапускает ран
  - `OBSERVATION:` содержит заголовки/URL и до 1000 символов контента

## Next Steps
- UI toggle for enabling/disabling dual-agents mode (MVP: always on)
- Separate reset actions for Agent 1 and Agent 2 threads
- Optional side-by-side display (payload vs Agent 2 rewritten)
- Fix format indicator visibility edge case after New Thread.
- Optionally set conservative token caps on Assistants runs (e.g., max_completion_tokens ~150) if required by ops policy.
- CI/CD: integrate detekt, unit tests, assembleRelease gates. Optional: add `assembleAnalyze` + `reportUnusedCode` to CI later (deferred).
- Optional: add unused dependency analysis (deferred).
- Security hardening follow-ups: certificate pinning, encrypted key storage for production.
 - Улучшить источники поиска (Brave/SerpAPI ключи), добавить ретраи/таймауты, стратегию выбора источников по типу запроса; сделать `enrich` управляемым из ARGS/настроек

## Open Decisions
- Model selection UI (single model vs multi-model): defer until backlog prioritization.
- Token limits for Assistants: enforce now vs observe and monitor first.

## Verification State
- Build: green on AGP 8.9.2, Kotlin 2.1.10, Gradle 8.11.1.
- Analyze/report: `./gradlew :app:assembleAnalyze` and `./gradlew :app:reportUnusedCode` succeed; `unused_code_report.md` generated.
- ArchUnit: architecture tests pass (no cycles, layered dependencies).
- Codegen: Hilt + KSP + Room generation verified with correct plugin declaration at root.
- Static analysis: detekt target zero weighted issues; OK.
 - UI: Manual verification
   - keyboard no longer pushes whole layout; messages area compresses and last item remains visible
   - dual-agents handoff works; acceptance badge shows before Agent 2 reply; user message persists immediately
   - web.search Divider + `OBSERVATION:` с заголовками/URL; при `enrich` добавляется фрагмент контента


