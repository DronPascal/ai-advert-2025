# ADR-0003: Compose State Management with MVI Pattern

## Status
Accepted

## Context
The original project had state management issues:
- Exposed MutableStateFlow instead of StateFlow
- No proper state hoisting in Compose
- Inefficient recomposition due to mutable state
- Side effects mixed with UI logic

## Decision
Implement MVI (Model-View-Intent) pattern with proper Compose state management:

1. **Immutable UI State**
   ```kotlin
   @Immutable
   data class ChatUiState(
       val messages: List<ChatMessage> = emptyList(),
       val isLoading: Boolean = false,
       val error: String? = null
   )
   ```

2. **Event-Driven Architecture**
   ```kotlin
   sealed class ChatUiEvent {
       data class MessageInputChanged(val message: String) : ChatUiEvent()
       data object SendMessage : ChatUiEvent()
   }
   ```

3. **State Hoisting Pattern**
   - ViewModels hold and manage state
   - Composables receive state and emit events
   - No local state in UI components for business data

4. **Performance Optimizations**
   - Use `@Stable` and `@Immutable` annotations
   - Proper keys in LazyColumn for efficient recomposition
   - StateFlow with `collectAsStateWithLifecycle()`

## Consequences

### Positive
- **Predictable State**: Unidirectional data flow
- **Performance**: Reduced unnecessary recompositions
- **Testability**: State changes are easily testable
- **Debugging**: Clear state transitions

### Negative
- **Verbosity**: More code for event handling
- **Learning Curve**: MVI pattern requires understanding

## Implementation Notes
- ViewModel exposes StateFlow, not MutableStateFlow
- UI components are stateless and event-driven
- Use `collectAsStateWithLifecycle()` for automatic lifecycle handling
- Apply `@Immutable` to all UI state classes
