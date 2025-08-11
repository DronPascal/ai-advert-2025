package com.example.day1_ai_chat_nextgen.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.day1_ai_chat_nextgen.data.local.entity.ChatThreadEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ChatThreadDao {
    
    @Query("SELECT * FROM chat_threads ORDER BY last_message_at DESC")
    fun getAllThreads(): Flow<List<ChatThreadEntity>>
    
    @Query("SELECT * FROM chat_threads WHERE id = :threadId LIMIT 1")
    suspend fun getThread(threadId: String): ChatThreadEntity?
    
    @Query("SELECT * FROM chat_threads WHERE thread_id = :openAiThreadId LIMIT 1")
    suspend fun getThreadByOpenAiId(openAiThreadId: String): ChatThreadEntity?
    
    @Query("SELECT * FROM chat_threads WHERE is_active = 1 ORDER BY last_message_at DESC LIMIT 1")
    suspend fun getCurrentActiveThread(): ChatThreadEntity?
    
    @Query("UPDATE chat_threads SET is_active = 0 WHERE is_active = 1")
    suspend fun deactivateAllThreads()
    
    @Query("UPDATE chat_threads SET is_active = 1 WHERE id = :threadId")
    suspend fun setThreadActive(threadId: String)
    
    @Query("UPDATE chat_threads SET active_format_id = :formatId WHERE id = :threadId")
    suspend fun updateThreadFormat(threadId: String, formatId: String?)
    
    @Query("UPDATE chat_threads SET last_message_at = :timestamp, message_count = message_count + 1 WHERE id = :threadId")
    suspend fun updateThreadActivity(threadId: String, timestamp: Long)
    
    @Query("UPDATE chat_threads SET title = :title WHERE id = :threadId")
    suspend fun updateThreadTitle(threadId: String, title: String)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertThread(thread: ChatThreadEntity)
    
    @Update
    suspend fun updateThread(thread: ChatThreadEntity)
    
    @Query("DELETE FROM chat_threads WHERE id = :threadId")
    suspend fun deleteThread(threadId: String)
    
    @Query("DELETE FROM chat_threads")
    suspend fun clearAllThreads()
}
