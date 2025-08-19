package com.example.day1_ai_chat_nextgen.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "chat_messages")
data class ChatMessageEntity(
    @PrimaryKey val id: String,
    val content: String,
    val role: String, // USER, ASSISTANT, SYSTEM
    val timestamp: Long,
    val isLoading: Boolean = false,
    val error: String? = null
)
