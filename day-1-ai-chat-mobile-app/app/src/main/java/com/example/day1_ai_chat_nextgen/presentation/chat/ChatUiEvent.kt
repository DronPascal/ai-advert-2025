package com.example.day1_ai_chat_nextgen.presentation.chat

import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat

sealed class ChatUiEvent {
    // Message events
    data class MessageInputChanged(val message: String) : ChatUiEvent()
    data object SendMessage : ChatUiEvent()
    data object ClearMessages : ChatUiEvent()
    data class DeleteMessage(val messageId: String) : ChatUiEvent()
    data object DismissError : ChatUiEvent()

    // Format management events
    data object ShowFormatDialog : ChatUiEvent()
    data object HideFormatDialog : ChatUiEvent()
    data class FormatInputChanged(val format: String) : ChatUiEvent()
    data class SetCustomFormat(val instructions: String) : ChatUiEvent()
    data class SelectPredefinedFormat(val format: ResponseFormat) : ChatUiEvent()

    // Thread management events
    data object ShowThreadDialog : ChatUiEvent()
    data object HideThreadDialog : ChatUiEvent()
    data object CreateNewThread : ChatUiEvent()
    data class SwitchToThread(val threadId: String) : ChatUiEvent()

    // Initialization events
    data object InitializeApp : ChatUiEvent()
    data object SkipFormatSelection : ChatUiEvent()
}
