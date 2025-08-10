# Memory Bank - AI Chat NextGen

This memory bank contains project context, architectural decisions, and constraints for the AI Chat NextGen module.

## Structure

- `contexts/` - Project context and domain knowledge
- `decisions/` - Architectural Decision Records (ADRs)
- `constraints/` - Technical and business constraints
- `backlog.md` - Feature roadmap and technical debt tracking
- `glossary.md` - Project terminology and definitions
- `module_scope.md` - Module boundaries and responsibilities
- `operational.md` - Deployment, monitoring, and operational concerns

## Recent Updates

### Critical Resolution: Hilt + KSP + Kotlin 2.1+ Compatibility
- **Issue**: JavaPoet ClassName.canonicalName() error preventing Hilt code generation
- **Root Cause**: Incomplete plugin configuration in root build.gradle.kts
- **Solution**: All plugins must be declared in root build file (see ADR-0004)
- **Result**: 100% build success with working dependency injection

## Usage

This memory bank serves as the single source of truth for project knowledge and helps maintain consistency across development iterations.
