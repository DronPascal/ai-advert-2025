# Memory Bank for day-1-ai-chat

Purpose: A compact, human-maintainable knowledge base to keep decisions, scope, constraints, and working context for the `day-1-ai-chat` module. All content is plain Markdown and safe for source control. No secrets are stored here.

## Conventions
- English only.
- Keep entries concise and actionable.
- Reference code by paths like `app/src/main/java/...` when helpful.
- Do not add secrets, tokens, API keys, or PII. Use `local.properties` for keys.

## Structure
- `constraints.md` — project and security constraints.
- `module_scope.md` — what’s in-scope vs out-of-scope.
- `backlog.md` — prioritized, living list of improvements.
- `decisions/` — Architectural Decision Records (ADRs).
- `contexts/` — persistent context snapshots (architecture, data flow, etc.).
- `glossary.md` — domain and technical terms used in this module.
- `operational.md` — build/run instructions and safe operational notes.

## How to use
1. Update `backlog.md` when priorities change.
2. Add a new ADR under `decisions/` when making significant architectural choices.
3. Keep `constraints.md` aligned with team policies.
4. Expand `contexts/` as the system evolves.


