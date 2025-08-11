package com.example.day1_ai_chat_nextgen.presentation.chat

import androidx.compose.runtime.Immutable
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.ChatThread
import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat

@Immutable
data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val messageInput: String = "",
    val isSendingMessage: Boolean = false,
    
    // New Assistants API fields
    val currentThread: ChatThread? = null,
    val activeFormat: ResponseFormat? = null,
    val availableFormats: List<ResponseFormat> = emptyList(),
    val allThreads: List<ChatThread> = emptyList(),
    
    // Format dialog state
    val showFormatDialog: Boolean = false,
    val formatInput: String = "",
    val isSettingFormat: Boolean = false,
    
    // Thread management state
    val showThreadDialog: Boolean = false,
    val isCreatingThread: Boolean = false,
    
    // Initialization state
    val isInitializing: Boolean = false,
    val needsFormatSelection: Boolean = false
) {
    val canSendMessage: Boolean
        get() = messageInput.isNotBlank() && !isSendingMessage && currentThread != null && !isInitializing
    
    val canTypeMessage: Boolean
        get() = currentThread != null && !isInitializing
}
