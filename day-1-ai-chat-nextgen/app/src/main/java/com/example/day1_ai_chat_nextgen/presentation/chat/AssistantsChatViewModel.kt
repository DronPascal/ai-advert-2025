package com.example.day1_ai_chat_nextgen.presentation.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.day1_ai_chat_nextgen.domain.model.Result
import com.example.day1_ai_chat_nextgen.domain.repository.ChatRepository
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
class AssistantsChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    init {
        initializeApp()
    }

    private fun initializeApp() {
        _uiState.update { it.copy(isInitializing = true) }
        
        viewModelScope.launch {
            // Initialize predefined formats
            chatRepository.initializePredefinedFormats()
            
            // Get or create assistant
            when (val assistantResult = chatRepository.getOrCreateAssistant()) {
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(
                            error = assistantResult.exception.message,
                            isInitializing = false
                        )
                    }
                    return@launch
                }
                is Result.Success -> {
                    // Continue with initialization
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
            
            // Try to get current thread
            when (val threadResult = chatRepository.getCurrentThread()) {
                is Result.Success -> {
                    if (threadResult.data != null) {
                        // We have an existing thread, continue with it
                        _uiState.update { 
                            it.copy(
                                currentThread = threadResult.data,
                                isInitializing = false
                            )
                        }
                        observeData()
                    } else {
                        // No current thread, need format selection
                        _uiState.update { 
                            it.copy(
                                needsFormatSelection = true,
                                isInitializing = false
                            )
                        }
                        loadFormats()
                    }
                }
                is Result.Error -> {
                    // Need format selection
                    _uiState.update { 
                        it.copy(
                            needsFormatSelection = true,
                            isInitializing = false
                        )
                    }
                    loadFormats()
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }

    private fun observeData() {
        // Observe messages
        chatRepository.getMessages()
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

        // Observe threads
        chatRepository.getAllThreads()
            .onEach { threads ->
                _uiState.update { it.copy(allThreads = threads) }
            }
            .launchIn(viewModelScope)

        // Observe formats
        chatRepository.getAllFormats()
            .onEach { formats ->
                _uiState.update { it.copy(availableFormats = formats) }
            }
            .launchIn(viewModelScope)

        // Observe active format
        viewModelScope.launch {
            when (val formatResult = chatRepository.getActiveFormat()) {
                is Result.Success -> {
                    _uiState.update { it.copy(activeFormat = formatResult.data) }
                }
                is Result.Error -> {
                    // No active format, which is okay
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }

    private fun loadFormats() {
        viewModelScope.launch {
            when (val formatsResult = chatRepository.getPredefinedFormats()) {
                is Result.Success -> {
                    _uiState.update { 
                        it.copy(availableFormats = formatsResult.data)
                    }
                }
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(error = "Failed to load formats: ${formatsResult.exception.message}")
                    }
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
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
            
            // Format management events
            ChatUiEvent.ShowFormatDialog -> {
                _uiState.update { it.copy(showFormatDialog = true) }
            }
            
            ChatUiEvent.HideFormatDialog -> {
                _uiState.update { 
                    it.copy(
                        showFormatDialog = false,
                        formatInput = ""
                    )
                }
            }
            
            is ChatUiEvent.FormatInputChanged -> {
                _uiState.update { it.copy(formatInput = event.format) }
            }
            
            is ChatUiEvent.SetCustomFormat -> {
                setCustomFormat(event.instructions)
            }
            
            is ChatUiEvent.SelectPredefinedFormat -> {
                selectPredefinedFormat(event.format)
            }
            
            // Thread management events
            ChatUiEvent.ShowThreadDialog -> {
                _uiState.update { it.copy(showThreadDialog = true) }
            }
            
            ChatUiEvent.HideThreadDialog -> {
                _uiState.update { it.copy(showThreadDialog = false) }
            }
            
            ChatUiEvent.CreateNewThread -> {
                createNewThread()
            }
            
            is ChatUiEvent.SwitchToThread -> {
                switchToThread(event.threadId)
            }
            
            // Initialization events
            ChatUiEvent.InitializeApp -> {
                initializeApp()
            }
            
            ChatUiEvent.SkipFormatSelection -> {
                skipFormatSelection()
            }
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
            when (val result = chatRepository.sendMessage(messageToSend)) {
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

    private fun clearMessages() {
        viewModelScope.launch {
            when (val result = chatRepository.clearHistory()) {
                is Result.Success -> {
                    _uiState.update { 
                        it.copy(
                            currentThread = null,
                            needsFormatSelection = true,
                            error = null
                        )
                    }
                    loadFormats()
                }
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(error = "Failed to clear messages: ${result.exception.message}")
                    }
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }

    private fun deleteMessage(messageId: String) {
        viewModelScope.launch {
            when (val result = chatRepository.deleteMessage(messageId)) {
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(error = "Failed to delete message: ${result.exception.message}")
                    }
                }
                else -> {
                    // Success or loading handled by observeMessages
                }
            }
        }
    }

    private fun setCustomFormat(instructions: String) {
        if (instructions.isBlank()) return
        
        _uiState.update { it.copy(isSettingFormat = true) }
        
        viewModelScope.launch {
            when (val result = chatRepository.setResponseFormat(instructions)) {
                is Result.Success -> {
                    // Create new thread with this format
                    createNewThreadWithFormat(result.data.id)
                }
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(
                            error = "Failed to set format: ${result.exception.message}",
                            isSettingFormat = false
                        )
                    }
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }

    private fun selectPredefinedFormat(format: com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat) {
        _uiState.update { it.copy(isSettingFormat = true) }
        
        viewModelScope.launch {
            when (val result = chatRepository.setResponseFormat(format)) {
                is Result.Success -> {
                    // Create new thread with this format
                    createNewThreadWithFormat(result.data.id)
                }
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(
                            error = "Failed to set format: ${result.exception.message}",
                            isSettingFormat = false
                        )
                    }
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }

    private fun createNewThread() {
        _uiState.update { it.copy(isCreatingThread = true) }
        
        viewModelScope.launch {
            val activeFormat = _uiState.value.activeFormat
            when (val result = chatRepository.createNewThread(activeFormat?.id)) {
                is Result.Success -> {
                    _uiState.update { 
                        it.copy(
                            currentThread = result.data,
                            isCreatingThread = false,
                            showThreadDialog = false,
                            needsFormatSelection = false
                        )
                    }
                    observeData()
                }
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(
                            error = "Failed to create thread: ${result.exception.message}",
                            isCreatingThread = false
                        )
                    }
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }

    private fun createNewThreadWithFormat(formatId: String) {
        viewModelScope.launch {
            when (val result = chatRepository.createNewThread(formatId)) {
                is Result.Success -> {
                    _uiState.update { 
                        it.copy(
                            currentThread = result.data,
                            isSettingFormat = false,
                            showFormatDialog = false,
                            needsFormatSelection = false
                        )
                    }
                    observeData()
                }
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(
                            error = "Failed to create thread: ${result.exception.message}",
                            isSettingFormat = false
                        )
                    }
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }

    private fun switchToThread(threadId: String) {
        viewModelScope.launch {
            when (val result = chatRepository.switchToThread(threadId)) {
                is Result.Success -> {
                    _uiState.update { 
                        it.copy(
                            currentThread = result.data,
                            showThreadDialog = false
                        )
                    }
                }
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(error = "Failed to switch thread: ${result.exception.message}")
                    }
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }

    private fun skipFormatSelection() {
        // Create a thread without format
        _uiState.update { it.copy(isCreatingThread = true) }
        
        viewModelScope.launch {
            when (val result = chatRepository.createNewThread()) {
                is Result.Success -> {
                    _uiState.update { 
                        it.copy(
                            currentThread = result.data,
                            needsFormatSelection = false,
                            isCreatingThread = false
                        )
                    }
                    observeData()
                }
                is Result.Error -> {
                    _uiState.update { 
                        it.copy(
                            error = "Failed to create thread: ${result.exception.message}",
                            isCreatingThread = false
                        )
                    }
                }
                is Result.Loading -> {
                    // Continue waiting
                }
            }
        }
    }
}
