# Active Context - AI Chat NextGen

## Current Focus
- Assistants API is the primary flow; legacy Chat Completions retained only for backward-compatibility.
- Response format management is thread-aware: update format within the current thread when possible; reset on new thread.
- UI polish: occasional visibility issues with the format indicator after New Thread.

## Recent Changes
- Adopted gpt-4o-mini as the default model for Assistants (see ADR-0009) to reduce latency and cost.
- Centralized API authentication via OkHttp interceptor (no manual header wiring).
- System message dividers added for key events (format updates, new thread, history clear).
- Detekt tuned for Android/Compose; static analysis and dead code pass clean.

## Next Steps
- Fix format indicator visibility edge case after New Thread.
- Optionally set conservative token caps on Assistants runs (e.g., max_completion_tokens ~150) if required by ops policy.
- CI/CD: integrate detekt, unit tests, assembleRelease gates.
- Security hardening follow-ups: certificate pinning, encrypted key storage for production.

## Open Decisions
- Model selection UI (single model vs multi-model): defer until backlog prioritization.
- Token limits for Assistants: enforce now vs observe and monitor first.

## Verification State
- Build: green on AGP 8.9.2, Kotlin 2.1.10, Gradle 8.11.1.
- Codegen: Hilt + KSP + Room generation verified with correct plugin declaration at root.
- Static analysis: detekt target zero weighted issues; OK.


