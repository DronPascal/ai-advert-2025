# Architecture Context - AI Chat NextGen

## Clean Architecture Implementation

### Layer Structure
```
presentation/     # UI Layer - Compose, ViewModels, States
├── main/        # MainActivity and navigation
├── chat/        # Chat screen and related UI (Assistants)
├── components/  # Reusable UI components (format dialogs, indicators)
└── theme/       # Material 3 theming

domain/          # Business Logic Layer
├── model/       # Domain entities (ChatMessage, ChatThread, ResponseFormat, Result, Errors)
├── repository/  # Repository abstractions (enhanced ChatRepository)
└── usecase/     # Business use cases

data/            # Data Access Layer
├── local/       # Room database (messages, threads, formats)
│   ├── dao/     # Data Access Objects (enhanced with threads/formats)
│   ├── entity/  # Database entities (ChatThread, ResponseFormat)
│   └── database/ # Room database configuration (v2 schema)
├── remote/      # OpenAI API implementation (Assistants only)
│   ├── api/     # API interfaces (OpenAIAssistantsApi)
│   └── dto/     # Data transfer objects (Assistants DTOs)
├── mapper/      # Data transformation (enhanced with threads/formats)
└── repository/  # Repository implementations (Assistants only)
```

### Key Architectural Patterns

#### 1. Repository Pattern
- **Abstract Interface**: `ChatRepository` in domain layer
- **Implementation**: `AssistantsChatRepositoryImpl` with OpenAI Assistants API
- **Enhanced Features**: Thread-aware format updates, centralized authentication, format deactivation
- **Format Management**: `deactivateAllFormats()`, `updateCurrentThreadFormat()`, format persistence
- **System Messages**: Elegant dividers for format changes, thread creation, history clearing
- **Benefits**: Testability, separation of concerns, data source abstraction, migration flexibility

#### 2. Use Case Pattern
- Removed with legacy flow; Assistants ViewModel orchestrates repository directly.

#### 3. MVI (Model-View-Intent) Pattern
- **Immutable State**: `ChatUiState` with `@Immutable` annotation
- **Event-Driven**: `ChatUiEvent` sealed class for user actions
- **Unidirectional Data Flow**: Events → ViewModel → State → UI
- **Optimistic Updates**: Immediate UI feedback with background processing

#### 4. Result Pattern
- **Type-Safe Errors**: `Result<T>` sealed class with Success/Error/Loading
- **Error Hierarchy**: `ChatError` sealed class with specific error types
- **Production Error Handling**: `catch (expected: Exception)` pattern for explicit intent
- **Benefits**: Explicit error handling, no exceptions in happy path, Detekt compliant

#### 5. Dual Agents Orchestration
- Two Assistants (Agent 1: Planner & Clarifier; Agent 2: Clown Rewriter)
- Two Threads, one per Agent, both cached across sessions (SharedPreferences keys per agent)
- Handoff protocol: Agent 1 emits final message whose first line is `HANDOFF_AGENT2`; payload is the rest sent as-is to Agent 2
- Observability: system `SYSTEM` messages used as dividers
  - "Передача сообщения во 2-го агента" — when handoff detected
  - "Сообщение принято агентом 2" — immediately after Agent 2 receives payload (before reply)
- Repository method `sendMessageDualAgents()` orchestrates A1→A2; VM routes `SendMessage` to this method in MVP

### Dependency Flow
```
Presentation → Domain ← Data
     ↓           ↓        ↓
   Compose   Use Cases  Repository
   ViewModel   Models   API/Database
```

### State Management Strategy
- **ViewModel**: Holds UI state and handles business logic delegation
- **StateFlow**: Reactive state updates with lifecycle awareness
- **Remember**: Local component state for UI-only concerns
- **Immutability**: All state objects are immutable for predictable updates

### Testing Strategy
- **Unit Tests**: Domain layer (use cases, models)
- **Integration Tests**: Repository implementations
- **UI Tests**: ViewModel state management
- **Test Doubles**: Mocks for external dependencies

### Security Architecture
- **API Key Protection**: Build-time configuration, ProGuard obfuscation
- **Network Security**: HTTPS only, certificate pinning ready
- **Data Protection**: Room database encryption ready
- **Logging**: Sensitive data filtering in production builds

### Code Quality Architecture
- **Static Analysis**: 100% Detekt compliance with zero warnings
- **Dead Code Elimination**: Comprehensive unused code detection and removal
- **Error Pattern Consistency**: Standardized `expected: Exception` handling
- **Architectural Suppressions**: Strategic @Suppress usage for design patterns
- **Build Quality**: Conflict-free configuration, successful release builds
 - **Architectural Tests**: Enforced with ArchUnit
   - No package cycles across `com.example.day1_ai_chat_nextgen.(**)`
   - Layered dependencies respected:
     - Domain must not depend on Presentation or Data
     - Presentation must not depend on Data
     - Data must not depend on Presentation
   - See: `app/src/test/java/com/example/day1_ai_chat_nextgen/architecture/ArchitectureTest.kt`
