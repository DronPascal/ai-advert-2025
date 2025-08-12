package com.example.day1_ai_chat_nextgen.data.mapper

import com.example.day1_ai_chat_nextgen.data.remote.dto.ThreadMessageDto
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole

fun ThreadMessageDto.toDomain(): ChatMessage {
    val messageContent = content.firstOrNull()?.text?.value ?: ""
    val messageRole = when (role) {
        "user" -> MessageRole.USER
        "assistant" -> MessageRole.ASSISTANT
        "system" -> MessageRole.SYSTEM
        else -> MessageRole.USER
    }

    return ChatMessage(
        id = id,
        content = messageContent,
        role = messageRole,
        timestamp = createdAt * 1000, // Convert to milliseconds
        isLoading = false,
        error = null
    )
}

fun List<ThreadMessageDto>.toDomainMessages(): List<ChatMessage> {
    return reversed() // OpenAI returns newest first, we want oldest first
        .map { it.toDomain() }
}
