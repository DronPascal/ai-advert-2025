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

### 11 August 2025 Major Enhancements

#### Format Context & System UI Improvements (Day 2)
- **System Message Dividers**: Elegant system event separators with icons (🔄 format, ✨ new thread, 🗑️ clear)
- **Format Context Preservation**: Fixed format loss on repeated changes within sessions
- **Thread-Aware Format Updates**: Format changes update existing threads instead of creating new ones
- **Format Reset Logic**: "New Thread" button properly resets formats to clean state
- **Performance Optimization**: Switched to GPT-4o-mini for faster, cost-effective responses
- **Format Notification Consistency**: Unified format change notifications across all flows

#### Technical Achievements
- **Thread Continuity**: Context preservation during format changes
- **Optimistic UI Updates**: Immediate feedback for all user interactions
- **Clean Architecture**: Separation between format inheritance and reset flows
- **Comprehensive Error Handling**: Graceful degradation for all scenarios

### Critical Resolution: Hilt + KSP + Kotlin 2.1+ Compatibility
- **Issue**: JavaPoet ClassName.canonicalName() error preventing Hilt code generation
- **Root Cause**: Incomplete plugin configuration in root build.gradle.kts
- **Solution**: All plugins must be declared in root build file (see ADR-0004)
- **Result**: 100% build success with working dependency injection

## Usage

This memory bank serves as the single source of truth for project knowledge and helps maintain consistency across development iterations.
