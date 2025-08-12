# Glossary - AI Chat NextGen

## Architecture Terms

**Clean Architecture**
: Software architecture pattern with clear separation of concerns across layers (Domain, Data, Presentation)

**Domain Layer**
: The innermost layer containing business logic, entities, and use cases. Framework-independent.

**Data Layer**
: Layer responsible for data access, including APIs, databases, and repository implementations.

**Presentation Layer**
: UI layer containing Activities, Composables, ViewModels, and UI state management.

**Repository Pattern**
: Design pattern that abstracts data access logic behind a clean interface.

**Use Case**
: A class that encapsulates a single business operation or workflow.

## State Management Terms

**MVI (Model-View-Intent)**
: Architectural pattern with unidirectional data flow: Intent → Model → View

**State Hoisting**
: Compose pattern where state is moved up to the closest common ancestor component.

**Immutable State**
: State objects that cannot be modified after creation, ensuring predictable updates.

**StateFlow**
: Kotlin coroutine type that represents a hot stream of state updates.

## Error Handling Terms

**Result Pattern**
: Pattern using sealed classes to represent success, error, or loading states explicitly.

**Typed Errors**
: Specific error types that provide context about what went wrong (vs generic exceptions).

**Error Mapping**
: Converting low-level errors (HTTP codes) to domain-specific error types.

## Testing Terms

**BDD (Behavior-Driven Development)**
: Testing approach using Given-When-Then syntax to describe behavior.

**Test Double**
: Generic term for mocks, stubs, fakes, and spies used in testing.

**Unit Test**
: Test that verifies a single unit of code in isolation.

**Integration Test**
: Test that verifies interaction between multiple components.

## Technology Terms

**Hilt**
: Android dependency injection library built on top of Dagger.

**KSP (Kotlin Symbol Processing)**
: Kotlin-first annotation processing tool, replacement for KAPT.

**Room**
: Android persistence library providing abstraction over SQLite.

**Retrofit**
: Type-safe HTTP client for Android and Kotlin.

**Jetpack Compose**
: Android's modern declarative UI toolkit.

**Coroutines**
: Kotlin feature for asynchronous programming using suspend functions.

**R8 (printusage)**
: Android code shrinker. The `-printusage` option writes a list of classes/members removed by minification, which we parse to detect unused code.

**ArchUnit**
: Java/Kotlin testing library for asserting architectural rules (e.g., no package cycles, layered dependencies) in unit tests.

## Business Terms

**OpenAI API**
: External service providing access to GPT language models.

**Chat Message**
: Core domain entity representing a single message in conversation.

**Token**
: Unit of text processing used by OpenAI for billing and rate limiting.

**Rate Limiting**
: Restriction on number of API requests allowed per time period.

**Context Window**
: Maximum amount of conversation history sent to AI model for context.
