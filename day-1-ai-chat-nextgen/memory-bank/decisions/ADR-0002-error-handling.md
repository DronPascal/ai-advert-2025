# ADR-0002: Typed Error Handling with Result Pattern

## Status
Accepted

## Context
The original project had poor error handling:
- Generic try-catch blocks without specific error types
- No distinction between different error categories
- Poor user experience with generic error messages
- No proper error propagation through layers

## Decision
Implement typed error handling using:

1. **Result<T> Sealed Class**
   ```kotlin
   sealed class Result<out T> {
       data class Success<T>(val data: T) : Result<T>()
       data class Error(val exception: Throwable) : Result<Nothing>()
       data object Loading : Result<Nothing>()
   }
   ```

2. **ChatError Sealed Class Hierarchy**
   ```kotlin
   sealed class ChatError : Exception() {
       data object NetworkError : ChatError()
       data object ApiKeyMissing : ChatError()
       data object ApiKeyInvalid : ChatError()
       data object RateLimitExceeded : ChatError()
       // ... more specific errors
   }
   ```

3. **Repository Layer Error Mapping**
   - Map HTTP status codes to specific ChatError types
   - Handle network exceptions appropriately
   - Provide meaningful error messages for users

## Consequences

### Positive
- **Type Safety**: Compile-time error handling verification
- **User Experience**: Specific error messages for different scenarios
- **Debugging**: Clear error categorization for logging
- **Testing**: Easier to test error scenarios

### Negative
- **Verbosity**: More code to handle different error types
- **Maintenance**: Need to keep error types up to date

## Implementation Notes
- All repository methods return Result<T>
- Use cases propagate errors without modification
- ViewModels handle Result types and update UI state
- UI displays user-friendly error messages based on error type
