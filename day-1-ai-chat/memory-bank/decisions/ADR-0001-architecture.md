# ADR-0001: App Architecture for day-1-ai-chat

Date: 2025-08-10

## Status
Accepted

## Context
The module is a simple AI chat Android application. It currently uses Jetpack Compose for UI, a `ViewModel` for state, Retrofit for networking, and integrates with OpenAI. The README outlines MVVM and repository patterns and mentions possible future features (persistence, theme settings).

## Decision
- Use MVVM with a single `ChatViewModel` to manage chat state and side effects.
- Use Jetpack Compose (Material 3) for UI; avoid fragments.
- Use Retrofit + OkHttp for HTTP; enforce HTTPS and timeouts; no logging of PII.
- Keep a thin network layer: `OpenAIApi` + `RetrofitClient`.
- Defer repository/data persistence to a later ADR when local history is introduced.
- Keep the codebase simple (KISS, YAGNI). Avoid layers unless justified by change pressure or duplication.

## Consequences
- Faster iteration for day-1 scope.
- Clear path to introduce a repository and storage when chat history persistence is implemented.
- Reduced complexity and maintenance cost.


