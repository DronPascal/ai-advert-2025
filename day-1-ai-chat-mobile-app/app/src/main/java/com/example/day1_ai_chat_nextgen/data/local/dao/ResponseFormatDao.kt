package com.example.day1_ai_chat_nextgen.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.day1_ai_chat_nextgen.data.local.entity.ResponseFormatEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface ResponseFormatDao {

    @Query("SELECT * FROM response_formats ORDER BY timestamp DESC")
    fun getAllFormats(): Flow<List<ResponseFormatEntity>>

    @Query("SELECT * FROM response_formats WHERE id = :formatId LIMIT 1")
    suspend fun getFormat(formatId: String): ResponseFormatEntity?

    @Query("SELECT * FROM response_formats WHERE is_active = 1 LIMIT 1")
    suspend fun getActiveFormat(): ResponseFormatEntity?

    @Query("SELECT * FROM response_formats WHERE is_custom = 0 ORDER BY timestamp ASC")
    suspend fun getPredefinedFormats(): List<ResponseFormatEntity>

    @Query("SELECT * FROM response_formats WHERE is_custom = 1 ORDER BY timestamp DESC")
    suspend fun getCustomFormats(): List<ResponseFormatEntity>

    @Query("UPDATE response_formats SET is_active = 0 WHERE is_active = 1")
    suspend fun deactivateAllFormats()

    @Query("UPDATE response_formats SET is_active = 1 WHERE id = :formatId")
    suspend fun setFormatActive(formatId: String)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFormat(format: ResponseFormatEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFormats(formats: List<ResponseFormatEntity>)

    @Update
    suspend fun updateFormat(format: ResponseFormatEntity)

    @Query("DELETE FROM response_formats WHERE id = :formatId")
    suspend fun deleteFormat(formatId: String)

    @Query("DELETE FROM response_formats WHERE is_custom = 1")
    suspend fun deleteCustomFormats()

    @Query("DELETE FROM response_formats")
    suspend fun clearAllFormats()
}
