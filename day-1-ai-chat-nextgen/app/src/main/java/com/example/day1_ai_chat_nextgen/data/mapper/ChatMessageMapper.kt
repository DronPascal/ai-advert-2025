package com.example.day1_ai_chat_nextgen.data.mapper

import com.example.day1_ai_chat_nextgen.data.local.entity.ChatMessageEntity
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIMessageDto
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole

fun ChatMessage.toEntity(): ChatMessageEntity {
    return ChatMessageEntity(
        id = id,
        content = content,
        role = role.name,
        timestamp = timestamp,
        isLoading = isLoading,
        error = error
    )
}

fun ChatMessageEntity.toDomain(): ChatMessage {
    return ChatMessage(
        id = id,
        content = content,
        role = MessageRole.valueOf(role),
        timestamp = timestamp,
        isLoading = isLoading,
        error = error
    )
}

fun ChatMessage.toOpenAIDto(): OpenAIMessageDto {
    return OpenAIMessageDto(
        role = when (role) {
            MessageRole.USER -> "user"
            MessageRole.ASSISTANT -> "assistant"
            MessageRole.SYSTEM -> "system"
        },
        content = content
    )
}

fun OpenAIMessageDto.toDomain(id: String, timestamp: Long = System.currentTimeMillis()): ChatMessage {
    return ChatMessage(
        id = id,
        content = content,
        role = when (role) {
            "user" -> MessageRole.USER
            "assistant" -> MessageRole.ASSISTANT
            "system" -> MessageRole.SYSTEM
            else -> MessageRole.ASSISTANT // default fallback
        },
        timestamp = timestamp
    )
}
