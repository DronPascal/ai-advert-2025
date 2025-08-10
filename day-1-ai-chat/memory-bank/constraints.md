# Constraints

- Security by default.
- Never store or commit secrets (API keys, tokens, passwords) or PII.
- All network requests use HTTPS with certificate validation and reasonable timeouts.
- Android permissions: request only what’s necessary, use runtime permissions, explain clearly to users.
- Kotlin/Android guidelines:
  - Clean architecture where beneficial, avoid unnecessary layers.
  - MVVM with `ViewModel` and Kotlin `Flow`/`StateFlow`.
  - Jetpack Compose + Material 3 for UI.
  - Coroutines for async and lifecycle-safe usage.
  - Repository pattern for persistence when added.
  - MVI-style state handling in `ViewModel` when state grows.
- Code quality:
  - Explicit types for functions and public APIs.
  - Small, purposeful functions; early returns; avoid deep nesting.
  - Prefer immutability for data models.
  - Unit tests per public function; acceptance tests per module when applicable.


