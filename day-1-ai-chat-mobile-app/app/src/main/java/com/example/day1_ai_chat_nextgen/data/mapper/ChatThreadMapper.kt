package com.example.day1_ai_chat_nextgen.data.mapper

import com.example.day1_ai_chat_nextgen.data.local.entity.ChatThreadEntity
import com.example.day1_ai_chat_nextgen.domain.model.ChatThread

fun ChatThread.toEntity(): ChatThreadEntity {
    return ChatThreadEntity(
        id = id,
        threadId = threadId,
        assistantId = assistantId,
        activeFormatId = activeFormatId,
        title = title,
        createdAt = createdAt,
        lastMessageAt = lastMessageAt,
        messageCount = messageCount,
        isActive = isActive
    )
}

fun ChatThreadEntity.toDomain(): ChatThread {
    return ChatThread(
        id = id,
        threadId = threadId,
        assistantId = assistantId,
        activeFormatId = activeFormatId,
        title = title,
        createdAt = createdAt,
        lastMessageAt = lastMessageAt,
        messageCount = messageCount,
        isActive = isActive
    )
}
