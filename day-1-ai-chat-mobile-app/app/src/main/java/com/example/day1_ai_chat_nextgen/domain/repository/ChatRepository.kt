package com.example.day1_ai_chat_nextgen.domain.repository

import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.ChatThread
import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat
import com.example.day1_ai_chat_nextgen.domain.model.Result
import kotlinx.coroutines.flow.Flow

interface ChatRepository {
    // Legacy message functions (for compatibility)
    fun getMessages(): Flow<List<ChatMessage>>
    suspend fun sendMessage(message: ChatMessage): Result<ChatMessage>
    suspend fun clearHistory(): Result<Unit>
    suspend fun deleteMessage(messageId: String): Result<Unit>

    // New Assistants API functions
    suspend fun sendMessage(content: String): Result<ChatMessage>
    suspend fun sendMessageDualAgents(content: String): Result<Unit>
    suspend fun getCurrentThread(): Result<ChatThread?>
    suspend fun createNewThread(formatId: String? = null): Result<ChatThread>
    suspend fun switchToThread(threadId: String): Result<ChatThread>
    fun getAllThreads(): Flow<List<ChatThread>>

    // Format management
    suspend fun setResponseFormat(formatInstructions: String): Result<ResponseFormat>
    suspend fun setResponseFormat(format: ResponseFormat): Result<ResponseFormat>
    suspend fun updateCurrentThreadFormat(format: ResponseFormat): Result<Unit>
    suspend fun deactivateAllFormats(): Result<Unit>
    suspend fun getActiveFormat(): Result<ResponseFormat?>
    suspend fun getPredefinedFormats(): Result<List<ResponseFormat>>
    fun getAllFormats(): Flow<List<ResponseFormat>>

    // Assistant management
    suspend fun getOrCreateAssistant(): Result<String>
    suspend fun initializePredefinedFormats(): Result<Unit>
}
