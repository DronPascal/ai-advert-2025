package com.example.day1_ai_chat_nextgen.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "chat_threads")
data class ChatThreadEntity(
    @PrimaryKey
    val id: String,
    
    @ColumnInfo(name = "thread_id")
    val threadId: String,
    
    @ColumnInfo(name = "assistant_id")
    val assistantId: String,
    
    @ColumnInfo(name = "active_format_id")
    val activeFormatId: String?,
    
    @ColumnInfo(name = "title")
    val title: String,
    
    @ColumnInfo(name = "created_at")
    val createdAt: Long,
    
    @ColumnInfo(name = "last_message_at")
    val lastMessageAt: Long,
    
    @ColumnInfo(name = "message_count")
    val messageCount: Int,
    
    @ColumnInfo(name = "is_active")
    val isActive: Boolean
)
