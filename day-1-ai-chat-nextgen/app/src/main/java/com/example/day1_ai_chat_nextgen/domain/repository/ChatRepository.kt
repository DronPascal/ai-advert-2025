package com.example.day1_ai_chat_nextgen.domain.repository

import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.Result
import kotlinx.coroutines.flow.Flow

interface ChatRepository {
    fun getMessages(): Flow<List<ChatMessage>>
    suspend fun sendMessage(message: ChatMessage): Result<ChatMessage>
    suspend fun clearHistory(): Result<Unit>
    suspend fun deleteMessage(messageId: String): Result<Unit>
}
