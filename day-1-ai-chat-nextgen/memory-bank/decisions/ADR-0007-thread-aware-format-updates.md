# ADR-0007: Thread-Aware Format Updates

## Status
Accepted

## Context

The initial implementation of format selection always created new threads, which caused several UX problems:

1. **Context Loss**: Users lost conversation history when changing formats mid-conversation
2. **Inefficient Threading**: Unnecessary thread creation for simple format changes
3. **Poor User Experience**: Format experimentation required starting over
4. **Cognitive Load**: Users had to decide between losing context or keeping suboptimal format

This approach didn't match user mental models - they expect format changes to be like "changing the style" rather than "starting a new conversation."

## Decision

We will implement **thread-aware format updates** that distinguish between:
- **New conversations**: Create thread with initial format
- **Existing conversations**: Update format within current thread

### Smart Format Update Logic

```kotlin
if (currentState.currentThread != null) {
    // Update format in existing thread
    chatRepository.updateCurrentThreadFormat(format)
} else {
    // Create new thread with format
    chatRepository.setResponseFormat(format)
}
```

## Implementation Details

### Repository Enhancement

New method added to `ChatRepository`:
```kotlin
suspend fun updateCurrentThreadFormat(format: ResponseFormat): Result<Unit>
```

Implementation in `AssistantsChatRepositoryImpl`:
- Updates thread's `activeFormatId` in local database
- Applies format instructions to subsequent messages in the thread
- Preserves all existing messages and context
- No new thread creation required

### ViewModel Logic Update

Both `selectPredefinedFormat()` and `setCustomFormat()` now:

1. **Check thread state** - existing vs new
2. **Choose appropriate action** - update vs create
3. **Provide immediate feedback** - close dialog instantly
4. **Handle background operations** - format setting + thread management
5. **Update UI state** - reflect new format selection

### State Management

Enhanced `ChatUiState` to properly reflect format updates:
```kotlin
// On successful format update
_uiState.update { 
    it.copy(
        activeFormat = newFormat,
        isSettingFormat = false
    )
}
```

## Technical Specifications

### Database Operations

**For Existing Threads:**
- Update `ChatThreadEntity.activeFormatId`
- No message history changes
- Thread metadata preserved

**For New Threads:**
- Create new `ChatThreadEntity` with format
- Initialize with format in assistant instructions
- Standard thread creation flow

### API Integration

**Format Updates:**
- Use existing assistant with updated instructions
- Apply format to new runs within the thread
- No assistant recreation required

**Thread Continuity:**
- Maintain same OpenAI thread ID
- Preserve message history
- Update local metadata only

### Error Handling

**Update Failures:**
```kotlin
is Result.Error -> {
    _uiState.update { 
        it.copy(
            error = "Failed to update format: ${result.exception.message}",
            isSettingFormat = false
        )
    }
}
```

**Graceful Degradation:**
- Fall back to creating new thread if update fails
- Preserve user's format selection intent
- Clear error messaging about what happened

## Consequences

### Positive
✅ **Context Preservation**: Users keep conversation history when changing formats  
✅ **Natural UX**: Format changes feel like style adjustments, not conversation restarts  
✅ **Reduced Friction**: Encourages format experimentation without penalty  
✅ **Efficient Resource Use**: No unnecessary thread creation  
✅ **Better Mental Model**: Aligns with user expectations of format behavior

### Negative
⚠️ **Complexity**: Two different paths for format updates vs creation  
⚠️ **State Management**: More scenarios to handle in UI logic  
⚠️ **Testing**: Additional test cases for update vs create scenarios

### Neutral
ℹ️ **Backward Compatibility**: New threads still work exactly as before  
ℹ️ **Performance**: No performance impact, slightly more efficient in most cases

## Usage Patterns

### Scenario 1: First-Time User
1. Launch app → Format selection dialog
2. Choose format → New thread created with format
3. Standard new user onboarding flow

### Scenario 2: Format Experimentation  
1. In active conversation → Open format dialog
2. Try different format → Thread format updated instantly
3. Continue conversation → New format applied to AI responses
4. Try another format → Seamless format switching

### Scenario 3: Format Refinement
1. Using custom format → Realize it needs adjustment
2. Open format dialog → Edit custom format
3. Submit changes → Format updated in current thread
4. Continue conversation → Refined format applied

## Future Enhancements

### Immediate
- **Format History**: Track format changes within threads
- **Format Reversion**: Quick undo for format changes
- **Format Suggestions**: AI-suggested format improvements

### Medium Term
- **Format Branching**: Create new thread while keeping current
- **Format Templates**: Save successful format combinations
- **Format Validation**: Preview format effects before applying

### Long Term
- **Multi-Format Threads**: Different formats for different message types
- **Collaborative Formatting**: Shared format preferences in team chats
- **AI Format Learning**: Automatically suggest optimal formats based on usage

## Testing Strategy

### Unit Tests
- Thread state detection logic
- Format update vs creation decision making
- Error handling for both code paths
- State management consistency

### Integration Tests
- End-to-end format update flows
- Thread continuity verification
- Database state consistency
- API interaction patterns

### User Acceptance Tests
- Format switching in active conversations
- New user format selection flows
- Error recovery scenarios
- Performance under different conditions

## References

- [Assistants API Migration](./ADR-0005-assistants-api-migration.md)
- [UI Responsiveness Improvements](./ADR-0006-ui-responsiveness-improvements.md)
- [Clean Architecture Implementation](./ADR-0001-clean-architecture.md)
