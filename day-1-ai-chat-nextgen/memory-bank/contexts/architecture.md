# Architecture Context - AI Chat NextGen

## Clean Architecture Implementation

### Layer Structure
```
presentation/     # UI Layer - Compose, ViewModels, States
├── main/        # MainActivity and navigation
├── chat/        # Chat screen and related UI (legacy + assistants)
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
├── remote/      # OpenAI API implementation (dual: completions + assistants)
│   ├── api/     # API interfaces (OpenAIApi, OpenAIAssistantsApi)
│   └── dto/     # Data transfer objects (chat + assistants DTOs)
├── mapper/      # Data transformation (enhanced with threads/formats)
└── repository/  # Repository implementations (legacy + assistants)
```

### Key Architectural Patterns

#### 1. Repository Pattern
- **Abstract Interface**: `ChatRepository` in domain layer
- **Primary Implementation**: `AssistantsChatRepositoryImpl` with OpenAI Assistants API
- **Legacy Implementation**: `LegacyChatRepositoryImpl` with Chat Completions API
- **Enhanced Features**: Thread-aware format updates, centralized authentication
- **Benefits**: Testability, separation of concerns, data source abstraction, migration flexibility

#### 2. Use Case Pattern
- **Single Responsibility**: Each use case handles one business operation
- **Examples**: `SendMessageUseCase`, `GetMessagesUseCase`
- **Benefits**: Reusable business logic, easier testing

#### 3. MVI (Model-View-Intent) Pattern
- **Immutable State**: `ChatUiState` with `@Immutable` annotation
- **Event-Driven**: `ChatUiEvent` sealed class for user actions
- **Unidirectional Data Flow**: Events → ViewModel → State → UI
- **Optimistic Updates**: Immediate UI feedback with background processing

#### 4. Result Pattern
- **Type-Safe Errors**: `Result<T>` sealed class with Success/Error/Loading
- **Error Hierarchy**: `ChatError` sealed class with specific error types
- **Benefits**: Explicit error handling, no exceptions in happy path

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
