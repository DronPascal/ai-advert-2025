package com.example.day1_ai_chat_nextgen.domain.usecase

import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole
import com.example.day1_ai_chat_nextgen.domain.model.Result
import com.example.day1_ai_chat_nextgen.domain.repository.ChatRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.util.UUID
import javax.inject.Inject

class SendMessageUseCase @Inject constructor(
    private val chatRepository: ChatRepository
) {
    suspend operator fun invoke(messageContent: String): Flow<Result<ChatMessage>> = flow {
        if (messageContent.isBlank()) {
            emit(Result.Error(IllegalArgumentException("Message cannot be empty")))
            return@flow
        }
        
        emit(Result.Loading)
        
        val userMessage = ChatMessage(
            id = UUID.randomUUID().toString(),
            content = messageContent.trim(),
            role = MessageRole.USER
        )
        
        val result = chatRepository.sendMessage(userMessage)
        emit(result)
    }
}
