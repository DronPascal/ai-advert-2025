# Progress - AI Chat NextGen

## What Works
- Assistants flow end-to-end: create assistant/thread, send message, poll run, persist messages.
- Thread-aware format updates and system dividers in UI.
- Predefined and custom response formats with persistence in Room.
- Repository pattern with DI via Hilt; KSP codegen functional.
- Static analysis and dead code passes clean.
- R8-based unused code report via `analyze` build type and `reportUnusedCode` task.
- Architectural rules enforced by ArchUnit tests (no cycles; layered dependencies).
 - Keyboard/IME behavior: `adjustResize` + IME-aware `LazyColumn` padding and autoscroll keep last message visible above the keyboard.
 - Dual Agents MVP: two Assistants + two Threads with automatic handoff (Agent1→payload→Agent2)
 - System badges: "Передача сообщения во 2-го агента" and "Сообщение принято агентом 2" (до ответа А2)
 - Immediate local persistence of user message to prevent disappearance on refresh
 - MCP web-search MVP for Agent 1 via local gateway (Docker): ACTION/ARGS/OBSERVATION loop, results with titles/URLs; enrichment returns content excerpt
- Forced handoff: если Агент 1 не ставит HANDOFF, репозиторий передаёт SOURCES+PAYLOAD Агенту 2 автоматически
- Агент 2: сразу выдаёт краткую выжимку клоунским стилем (3–5 пунктов, ≤12 слов, с [n]-ссылками)

## What's Left
- Fix intermittent format indicator visibility after New Thread.
 - UI toggle for dual-agents mode; separate reset for Agent 1/2 threads; optional side-by-side payload vs rewritten
- Optional: cap tokens for Assistants runs if required (e.g., ~150 completion tokens).
- CI setup with quality gates (detekt/test/release assemble).
- Optional: unused dependencies analysis (deferred).
- Optional: CI job for `assembleAnalyze` + `reportUnusedCode` (deferred).
- Production security hardening (pinning, encrypted key storage).
 - Improve search sources (Brave/SerpAPI), retries/timeouts; configurable `enrich`

## Current Status
- Build and codegen: stable on AGP 8.9.2, Kotlin 2.1.10, KSP 2.1.10-1.0.30, Hilt 2.53.1.
- Model: gpt-4o-mini per ADR-0009.
- UX: Optimistic updates, instant dialog actions, system message dividers, compact input field, IME-safe chat.

## Known Issues
- Format indicator sometimes disappears after New Thread (expected when format is reset; ensure UX copy clarifies and visibility rules are consistent).

## Recent Verifications
- Hilt generation present under build/generated/ksp.
- Room DAOs compile and run.
- detekt: zero weighted issues.
- `:app:assembleAnalyze` minifies with R8 `-printusage`.
- `:app:reportUnusedCode` created `unused_code_report.md`.
 - Local gateway `day-6-mcp` responds: `/healthz`, `/tools`, `/search`; emulator access via `http://10.0.2.2:8765/`


