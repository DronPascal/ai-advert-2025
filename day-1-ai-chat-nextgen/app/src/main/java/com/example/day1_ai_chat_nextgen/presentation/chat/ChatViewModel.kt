package com.example.day1_ai_chat_nextgen.presentation.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.day1_ai_chat_nextgen.domain.model.Result
import com.example.day1_ai_chat_nextgen.domain.repository.ChatRepository
import com.example.day1_ai_chat_nextgen.domain.usecase.GetMessagesUseCase
import com.example.day1_ai_chat_nextgen.domain.usecase.SendMessageUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val getMessagesUseCase: GetMessagesUseCase,
    private val sendMessageUseCase: SendMessageUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    init {
        observeMessages()
    }

    private fun observeMessages() {
        getMessagesUseCase()
            .catch { exception ->
                _uiState.update { currentState ->
                    currentState.copy(
                        error = exception.message ?: "Unknown error occurred",
                        isLoading = false
                    )
                }
            }
            .onEach { messages ->
                _uiState.update { currentState ->
                    currentState.copy(
                        messages = messages,
                        isLoading = false
                    )
                }
            }
            .launchIn(viewModelScope)
    }

    fun onEvent(event: ChatUiEvent) {
        when (event) {
            is ChatUiEvent.MessageInputChanged -> {
                _uiState.update { it.copy(messageInput = event.message) }
            }
            
            ChatUiEvent.SendMessage -> {
                sendMessage()
            }
            
            ChatUiEvent.ClearMessages -> {
                clearMessages()
            }
            
            is ChatUiEvent.DeleteMessage -> {
                deleteMessage(event.messageId)
            }
            
            ChatUiEvent.DismissError -> {
                _uiState.update { it.copy(error = null) }
            }
            
            // Stub implementations for new events (legacy compatibility)
            ChatUiEvent.ShowFormatDialog -> { /* Not implemented */ }
            ChatUiEvent.HideFormatDialog -> { /* Not implemented */ }
            is ChatUiEvent.FormatInputChanged -> { /* Not implemented */ }
            is ChatUiEvent.SetCustomFormat -> { /* Not implemented */ }
            is ChatUiEvent.SelectPredefinedFormat -> { /* Not implemented */ }
            ChatUiEvent.ShowThreadDialog -> { /* Not implemented */ }
            ChatUiEvent.HideThreadDialog -> { /* Not implemented */ }
            ChatUiEvent.CreateNewThread -> { /* Not implemented */ }
            is ChatUiEvent.SwitchToThread -> { /* Not implemented */ }
            ChatUiEvent.InitializeApp -> { /* Not implemented */ }
            ChatUiEvent.SkipFormatSelection -> { /* Not implemented */ }
        }
    }

    private fun sendMessage() {
        val currentState = _uiState.value
        if (!currentState.canSendMessage) return

        val messageToSend = currentState.messageInput.trim()
        
        // Clear input immediately for better UX
        _uiState.update { 
            it.copy(
                messageInput = "",
                isSendingMessage = true,
                error = null
            )
        }

        viewModelScope.launch {
            sendMessageUseCase(messageToSend)
                .catch { exception ->
                    _uiState.update { currentState ->
                        currentState.copy(
                            error = exception.message ?: "Failed to send message",
                            isSendingMessage = false
                        )
                    }
                }
                .collect { result ->
                    when (result) {
                        is Result.Loading -> {
                            _uiState.update { it.copy(isSendingMessage = true) }
                        }
                        
                        is Result.Success -> {
                            _uiState.update { 
                                it.copy(
                                    isSendingMessage = false,
                                    error = null
                                )
                            }
                        }
                        
                        is Result.Error -> {
                            _uiState.update { currentState ->
                                currentState.copy(
                                    error = result.exception.message ?: "Failed to send message",
                                    isSendingMessage = false
                                )
                            }
                        }
                    }
                }
        }
    }

    private fun clearMessages() {
        viewModelScope.launch {
            // Implementation would call repository to clear messages
            // For now, just update UI state
            _uiState.update { it.copy(error = null) }
        }
    }

    private fun deleteMessage(messageId: String) {
        viewModelScope.launch {
            // Implementation would call repository to delete specific message
            // For now, just update UI state
            _uiState.update { it.copy(error = null) }
        }
    }
}
