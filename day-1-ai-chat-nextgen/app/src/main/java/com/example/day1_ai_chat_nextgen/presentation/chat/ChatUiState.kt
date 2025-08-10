package com.example.day1_ai_chat_nextgen.presentation.chat

import androidx.compose.runtime.Immutable
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage

@Immutable
data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
    val messageInput: String = "",
    val isSendingMessage: Boolean = false
) {
    val canSendMessage: Boolean
        get() = messageInput.isNotBlank() && !isSendingMessage
}
