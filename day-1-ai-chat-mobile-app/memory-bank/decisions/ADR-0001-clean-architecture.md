# ADR-0001: Adopt Clean Architecture

## Status
Accepted

## Context
The original project had significant architectural issues:
- No separation of concerns
- ViewModel directly coupled to Retrofit API
- No testability due to hard dependencies
- Mixed business logic with UI logic
- Poor error handling

## Decision
Adopt Clean Architecture with three distinct layers:

1. **Domain Layer** - Pure business logic
   - Contains entities, use cases, and repository abstractions
   - No dependencies on Android framework or external libraries
   - Defines business rules and error types

2. **Data Layer** - Data access implementation
   - Implements repository interfaces from domain
   - Contains API clients, database DAOs, and data mappers
   - Handles data transformation and caching

3. **Presentation Layer** - UI and state management
   - Contains Activities, Composables, and ViewModels
   - Depends only on domain layer interfaces
   - Handles UI state and user interactions

## Consequences

### Positive
- **Testability**: Each layer can be tested in isolation
- **Maintainability**: Clear separation of concerns
- **Flexibility**: Easy to swap implementations (e.g., different APIs)
- **Scalability**: New features follow established patterns

### Negative
- **Initial Complexity**: More files and abstractions
- **Learning Curve**: Team needs to understand the architecture
- **Overhead**: More interfaces and mapping code

## Implementation Notes
- Use Hilt for dependency injection across layers
- Domain models are immutable and framework-agnostic
- Repository pattern abstracts data sources
- Use cases encapsulate business operations
