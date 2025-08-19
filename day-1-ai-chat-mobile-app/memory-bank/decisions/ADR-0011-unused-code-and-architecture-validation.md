## ADR-0011 — Unused Code Detection and Architecture Validation

- Status: Accepted
- Date: 2025-08-12

### Context
Legacy approaches to unused code detection (custom scripts, static heuristics) proved noisy and brittle. We need a reliable, bytecode-level signal and enforceable architectural rules to keep the codebase clean and maintainable.

### Decision
1) Unused code detection
- Introduce an `analyze` build type with R8 `-printusage` (non-debuggable to enable full optimization) and a dedicated ProGuard file `proguard-usage.pro` to write usage to `app/build/reports/unused/printusage-analyze.txt`.
- Add Gradle task `reportUnusedCode` to parse and filter the R8 output into `unused_code_report.md`, excluding generated artifacts (Hilt, Room, Kotlin synthetic, Compose singletons).

2) Architecture validation
- Add ArchUnit tests to assert:
  - No package cycles in `com.example.day1_ai_chat_nextgen.(**)`.
  - Layered dependencies: Domain must not depend on Presentation/Data; Presentation must not depend on Data; Data must not depend on Presentation.
- Test location: `app/src/test/java/com/example/day1_ai_chat_nextgen/architecture/ArchitectureTest.kt`.

### Consequences
- New build variant (`analyze`) and Gradle reporting task form part of the quality gate locally; CI job is deferred for now.
- Developers can quickly inspect `unused_code_report.md` and remove true dead code with confidence.
- Architectural regressions will fail fast via unit tests.

### Alternatives Considered
- Detekt custom rules: good for style and patterns, weak for true reachability.
- Android Lint: useful but not focused on bytecode reachability.
- Hand-written scripts: high maintenance, many false positives.

### How to Run
```
./gradlew :app:assembleAnalyze
./gradlew :app:reportUnusedCode
# Output: day-1-ai-chat-nextgen/unused_code_report.md
```

