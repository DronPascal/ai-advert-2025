package com.example.day1_ai_chat_nextgen.domain.model

sealed class ChatError : Exception() {
    data object NetworkError : ChatError()
    data object ApiKeyMissing : ChatError()
    data object ApiKeyInvalid : ChatError()
    data object RateLimitExceeded : ChatError()
    data object InsufficientCredits : ChatError()
    data object ModelNotAvailable : ChatError()
    data object ContentFiltered : ChatError()

    // Assistants API specific errors
    data object AssistantNotFound : ChatError()
    data object ThreadNotFound : ChatError()
    data object RunFailed : ChatError()
    data object RunTimeout : ChatError()
    data object RunCancelled : ChatError()
    data class RunRequiresAction(val requiredAction: String) : ChatError()
    data object FormatNotSet : ChatError()

    data class ApiError(val code: Int, val details: String) : ChatError()
    data class UnknownError(val details: String) : ChatError()

    override val message: String
        get() = when (this) {
            NetworkError -> "Network connection error. Please check your internet connection."
            ApiKeyMissing -> "OpenAI API key is not configured."
            ApiKeyInvalid -> "OpenAI API key is invalid."
            RateLimitExceeded -> "Rate limit exceeded. Please try again later."
            InsufficientCredits -> "Insufficient API credits."
            ModelNotAvailable -> "The requested AI model is not available."
            ContentFiltered -> "Content was filtered by OpenAI's safety systems."
            AssistantNotFound -> "Assistant not found. Creating new assistant..."
            ThreadNotFound -> "Thread not found. Creating new thread..."
            RunFailed -> "Failed to process message. Please try again."
            RunTimeout -> "Message processing timed out. Please try again."
            RunCancelled -> "Message processing was cancelled."
            is RunRequiresAction -> "Action required: $requiredAction"
            FormatNotSet -> "Please set a response format first."
            is ApiError -> "API Error ($code): $details"
            is UnknownError -> "Unknown error: $details"
        }
}
