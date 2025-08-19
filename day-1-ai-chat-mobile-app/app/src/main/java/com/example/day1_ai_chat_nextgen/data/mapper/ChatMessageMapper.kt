package com.example.day1_ai_chat_nextgen.data.mapper

import com.example.day1_ai_chat_nextgen.data.local.entity.ChatMessageEntity
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

// Removed legacy OpenAI Chat Completions mappings
