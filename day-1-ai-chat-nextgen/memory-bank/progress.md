# Progress - AI Chat NextGen

## What Works
- Assistants flow end-to-end: create assistant/thread, send message, poll run, persist messages.
- Thread-aware format updates and system dividers in UI.
- Predefined and custom response formats with persistence in Room.
- Repository pattern with DI via Hilt; KSP codegen functional.
- Static analysis and dead code passes clean.

## What's Left
- Fix intermittent format indicator visibility after New Thread.
- Optional: cap tokens for Assistants runs if required (e.g., ~150 completion tokens).
- CI setup with quality gates (detekt/test/release assemble).
- Production security hardening (pinning, encrypted key storage).

## Current Status
- Build and codegen: stable on AGP 8.9.2, Kotlin 2.1.10, KSP 2.1.10-1.0.30, Hilt 2.53.1.
- Model: gpt-4o-mini per ADR-0009.
- UX: Optimistic updates, instant dialog actions, system message dividers.

## Known Issues
- Format indicator sometimes disappears after New Thread (expected when format is reset; ensure UX copy clarifies and visibility rules are consistent).

## Recent Verifications
- Hilt generation present under build/generated/ksp.
- Room DAOs compile and run.
- detekt: zero weighted issues.


