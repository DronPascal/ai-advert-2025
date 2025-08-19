package com.example.day1_ai_chat_nextgen.data.local.database

import androidx.room.Database
import androidx.room.RoomDatabase
import com.example.day1_ai_chat_nextgen.data.local.dao.ChatMessageDao
import com.example.day1_ai_chat_nextgen.data.local.dao.ChatThreadDao
import com.example.day1_ai_chat_nextgen.data.local.dao.ResponseFormatDao
import com.example.day1_ai_chat_nextgen.data.local.entity.ChatMessageEntity
import com.example.day1_ai_chat_nextgen.data.local.entity.ChatThreadEntity
import com.example.day1_ai_chat_nextgen.data.local.entity.ResponseFormatEntity

@Database(
    entities = [
        ChatMessageEntity::class,
        ChatThreadEntity::class,
        ResponseFormatEntity::class
    ],
    version = 2,
    exportSchema = false
)
abstract class ChatDatabase : RoomDatabase() {
    abstract fun chatMessageDao(): ChatMessageDao
    abstract fun chatThreadDao(): ChatThreadDao
    abstract fun responseFormatDao(): ResponseFormatDao

    companion object {
        const val DATABASE_NAME = "chat_database"
    }
}
