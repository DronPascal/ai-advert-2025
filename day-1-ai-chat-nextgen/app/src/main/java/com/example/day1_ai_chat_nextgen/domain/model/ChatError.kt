package com.example.day1_ai_chat_nextgen.domain.model

sealed class ChatError : Exception() {
    data object NetworkError : ChatError()
    data object ApiKeyMissing : ChatError()
    data object ApiKeyInvalid : ChatError()
    data object RateLimitExceeded : ChatError()
    data object InsufficientCredits : ChatError()
    data object ModelNotAvailable : ChatError()
    data object ContentFiltered : ChatError()
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
            is ApiError -> "API Error ($code): $details"
            is UnknownError -> "Unknown error: $details"
        }
}
