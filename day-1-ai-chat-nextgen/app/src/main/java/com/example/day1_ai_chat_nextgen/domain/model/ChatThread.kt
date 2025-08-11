package com.example.day1_ai_chat_nextgen.domain.model

import androidx.compose.runtime.Immutable
import kotlinx.serialization.Serializable
import java.util.UUID

@Immutable
@Serializable
data class ChatThread(
    val id: String = UUID.randomUUID().toString(),
    val threadId: String, // OpenAI thread ID
    val assistantId: String,
    val activeFormatId: String?,
    val title: String = "New Chat",
    val createdAt: Long = System.currentTimeMillis(),
    val lastMessageAt: Long = System.currentTimeMillis(),
    val messageCount: Int = 0,
    val isActive: Boolean = true
) {
    companion object {
        fun create(
            threadId: String,
            assistantId: String,
            formatId: String? = null,
            title: String = "New Chat"
        ): ChatThread {
            return ChatThread(
                threadId = threadId,
                assistantId = assistantId,
                activeFormatId = formatId,
                title = title
            )
        }
    }
    
    fun withUpdatedActivity(): ChatThread {
        return copy(
            lastMessageAt = System.currentTimeMillis(),
            messageCount = messageCount + 1
        )
    }
    
    fun withFormat(formatId: String?): ChatThread {
        return copy(activeFormatId = formatId)
    }
    
    fun withTitle(newTitle: String): ChatThread {
        return copy(title = newTitle)
    }
}
