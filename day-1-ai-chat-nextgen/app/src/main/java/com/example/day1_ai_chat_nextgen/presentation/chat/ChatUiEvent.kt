package com.example.day1_ai_chat_nextgen.presentation.chat

sealed class ChatUiEvent {
    data class MessageInputChanged(val message: String) : ChatUiEvent()
    data object SendMessage : ChatUiEvent()
    data object ClearMessages : ChatUiEvent()
    data class DeleteMessage(val messageId: String) : ChatUiEvent()
    data object DismissError : ChatUiEvent()
}
