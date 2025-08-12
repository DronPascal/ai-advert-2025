# Active Context - AI Chat NextGen

## Current Focus
- Assistants API is the only flow; legacy Chat Completions removed.
- Response format management is thread-aware: update format within the current thread when possible; reset on new thread.
- UI polish: IME/keyboard behavior and compact input field; occasional visibility issues with the format indicator after New Thread.

## Recent Changes
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

## Next Steps
- Fix format indicator visibility edge case after New Thread.
- Optionally set conservative token caps on Assistants runs (e.g., max_completion_tokens ~150) if required by ops policy.
- CI/CD: integrate detekt, unit tests, assembleRelease gates. Optional: add `assembleAnalyze` + `reportUnusedCode` to CI later (deferred).
- Optional: add unused dependency analysis (deferred).
- Security hardening follow-ups: certificate pinning, encrypted key storage for production.

## Open Decisions
- Model selection UI (single model vs multi-model): defer until backlog prioritization.
- Token limits for Assistants: enforce now vs observe and monitor first.

## Verification State
- Build: green on AGP 8.9.2, Kotlin 2.1.10, Gradle 8.11.1.
- Analyze/report: `./gradlew :app:assembleAnalyze` and `./gradlew :app:reportUnusedCode` succeed; `unused_code_report.md` generated.
- ArchUnit: architecture tests pass (no cycles, layered dependencies).
- Codegen: Hilt + KSP + Room generation verified with correct plugin declaration at root.
- Static analysis: detekt target zero weighted issues; OK.
 - UI: Manual verification on device — keyboard no longer pushes whole layout; messages area compresses and last item remains visible.


