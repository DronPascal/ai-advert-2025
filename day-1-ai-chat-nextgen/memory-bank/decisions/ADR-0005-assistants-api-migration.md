# ADR-0005: OpenAI Assistants API Migration

## Status
Accepted

## Context

The application was initially built using OpenAI's Chat Completions API (`/v1/chat/completions`), which required manual conversation history management and provided no built-in format persistence capabilities. The requirement to implement custom response formats with persistent memory across sessions led to the decision to migrate to OpenAI's Assistants API.

## Decision

We will migrate from the Chat Completions API to the OpenAI Assistants API to enable:

1. **Thread-based conversation management** with server-side memory
2. **Custom response format persistence** through assistant instructions
3. **Session restoration** across app restarts
4. **Format flexibility** without rigid JSON schema validation

### Architecture Changes

#### API Layer
- **API Interface**: `OpenAIAssistantsApi` with comprehensive endpoint coverage
- **DTOs**: Complete set of data transfer objects for all Assistants API entities
- **Cleanup**: Legacy `OpenAIApi` and Chat Completions fallback removed

#### Domain Layer
- **New Models**: `ChatThread`, `ResponseFormat` with rich behavior
- **Enhanced Errors**: Assistants-specific error types (`RunFailed`, `ThreadNotFound`, etc.)
- **Extended Repository**: Additional methods for thread and format management

#### Data Layer
- **Database Schema Update**: New entities for threads and formats (v1→v2 migration)
- **Enhanced Persistence**: Thread ID storage in SharedPreferences
- **New Repository**: `AssistantsChatRepositoryImpl` with full Assistants API integration

#### Presentation Layer
- **Format Management UI**: Intuitive selection dialog with predefined and custom options
- **Thread Management**: Session restoration and multi-thread support
- **Enhanced State**: Rich UI state with initialization and format selection flows

## Implementation Details

### Assistant Management
```kotlin
// One-time assistant creation with format instructions
val assistant = createAssistant(
    model = "gpt-4o-2024-08-06",
    instructions = getDefaultSystemInstructions()
)
```

### Thread-based Conversations
```kotlin
// Thread creation with format context
val thread = createThread()
val message = addMessage(thread.id, userMessage)
val run = createRun(thread.id, assistant.id, formatInstructions)
val response = pollRunCompletion(run.id)
```

### Format Persistence
- **Storage**: Format instructions stored in assistant configuration
- **Application**: Applied to each run as `additional_instructions`
- **Persistence**: Thread-based memory maintains format across sessions

### Session Management
- **Thread ID**: Stored in SharedPreferences for session restoration
- **Local Cache**: Threads and formats cached in Room database
- **Synchronization**: Regular sync between local and remote state

## Consequences

### Positive
✅ **Persistent Format Memory**: Formats maintained across app restarts  
✅ **Simplified State Management**: Server-side conversation memory  
✅ **Enhanced User Experience**: Seamless session restoration  
✅ **Format Flexibility**: Any structural format without rigid validation  
✅ **Scalable Architecture**: Clean separation of concerns maintained  

### Negative
⚠️ **API Complexity**: More complex API calls (create thread → add message → run → poll)  
⚠️ **Latency Increase**: Additional API roundtrips for run management  
⚠️ **Cost Implications**: Potentially higher token usage from persistent context  
⚠️ **Error Handling**: More failure modes (runs can fail, timeout, require actions)  

### Risks Accepted for MVP
- **Client-side API Key**: Security risk accepted for MVP simplicity
- **No Format Validation**: Model compliance relied upon without strict enforcement
- **Limited Error Recovery**: Basic retry mechanisms, not comprehensive
- **Cost Management**: No usage tracking or budgeting implemented

## Migration Strategy

### Phase 1: Parallel Implementation ✅
- New Assistants repository alongside legacy implementation
- Feature flag capability for switching between implementations
- Comprehensive test coverage for new implementation

### Phase 2: Default Switch ✅
- Update dependency injection to use Assistants implementation
 - No legacy fallback retained
- User acceptance testing with new flow

### Phase 3: Cleanup ✅
- Remove legacy Chat Completions implementation
- Clean up unused dependencies and code
- Optimize for Assistants API patterns

## Technical Specifications

### API Endpoints Used
- `POST /v1/assistants` - Assistant creation/management
- `POST /v1/threads` - Thread creation
- `POST /v1/threads/{thread_id}/messages` - Message management
- `POST /v1/threads/{thread_id}/runs` - Run execution
- `GET /v1/threads/{thread_id}/runs/{run_id}` - Run status polling
- `GET /v1/threads/{thread_id}/messages` - Message retrieval

### Data Models
```kotlin
// Thread management
data class ChatThread(
    val threadId: String,      // OpenAI thread ID
    val assistantId: String,   // OpenAI assistant ID
    val activeFormatId: String?, // Current format
    val title: String,         // User-friendly title
    // ... activity tracking
)

// Format management  
data class ResponseFormat(
    val instructions: String,  // Format instructions
    val isCustom: Boolean,    // User-defined vs predefined
    val isActive: Boolean,    // Currently selected
    // ... metadata
)
```

### Error Handling Strategy
- **Run Failures**: Graceful degradation with user notification
- **Network Issues**: Retry with exponential backoff
- **Assistant Missing**: Automatic recreation with format preservation
- **Thread Missing**: New thread creation with context restoration

## Testing Strategy

### Unit Tests ✅
- `AssistantsChatRepositoryImplTest`: Comprehensive API integration testing
- `AssistantsChatViewModelTest`: UI state management and event handling
- `ResponseFormatTest`: Domain model behavior validation
- `ChatThreadTest`: Thread lifecycle and operations

### Integration Tests (Future)
- End-to-end format persistence verification
- Session restoration across app restarts
- Error recovery scenarios
- Performance benchmarking

## Monitoring and Metrics

### Success Metrics
- **Format Persistence Rate**: % of sessions where format is maintained
- **Session Restoration Success**: % of successful app restart continuations
- **User Format Adoption**: Usage of predefined vs custom formats
- **Error Recovery Rate**: % of successful error recoveries

### Performance Metrics
- **API Response Times**: Thread operations vs legacy chat completions
- **Token Usage**: Comparison with previous implementation
- **App Launch Time**: Impact of initialization flow
- **Battery Usage**: Background session management impact

## Future Enhancements

### Immediate (Post-MVP)
- JSON mode integration for structured responses
- Enhanced error recovery with intelligent retry
- Thread management UI improvements
- Format validation and preview

### Medium Term
- Structured Outputs with JSON Schema
- Backend proxy for API key security
- Advanced thread features (branching, merging)
- Format marketplace and sharing

### Long Term
- Multi-model support (different AI providers)
- Collaborative thread features
- Advanced analytics and insights
- Plugin architecture for extensibility

## References

- [OpenAI Assistants API Documentation](https://platform.openai.com/docs/assistants)
- [Clean Architecture Implementation Guide](./ADR-0001-clean-architecture.md)
- [Error Handling Strategy](./ADR-0002-error-handling.md)
- [State Management Patterns](./ADR-0003-compose-state-management.md)
