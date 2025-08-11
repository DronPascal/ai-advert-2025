package com.example.day1_ai_chat_nextgen.data.remote.api

import com.example.day1_ai_chat_nextgen.data.remote.dto.AssistantDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.CreateAssistantRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.CreateMessageRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.CreateRunRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.CreateThreadRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.MessagesResponseDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.RunDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.ThreadDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.ThreadMessageDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Headers
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface OpenAIAssistantsApi {
    
    @Headers("Content-Type: application/json", "OpenAI-Beta: assistants=v2")
    @POST("v1/assistants")
    suspend fun createAssistant(
        @Header("Authorization") authorization: String,
        @Body request: CreateAssistantRequestDto
    ): Response<AssistantDto>
    
    @Headers("Content-Type: application/json", "OpenAI-Beta: assistants=v2")
    @GET("v1/assistants/{assistant_id}")
    suspend fun getAssistant(
        @Header("Authorization") authorization: String,
        @Path("assistant_id") assistantId: String
    ): Response<AssistantDto>
    
    @Headers("Content-Type: application/json", "OpenAI-Beta: assistants=v2")
    @POST("v1/threads")
    suspend fun createThread(
        @Header("Authorization") authorization: String,
        @Body request: CreateThreadRequestDto = CreateThreadRequestDto()
    ): Response<ThreadDto>
    
    @Headers("Content-Type: application/json", "OpenAI-Beta: assistants=v2")
    @GET("v1/threads/{thread_id}")
    suspend fun getThread(
        @Header("Authorization") authorization: String,
        @Path("thread_id") threadId: String
    ): Response<ThreadDto>
    
    @Headers("Content-Type: application/json", "OpenAI-Beta: assistants=v2")
    @POST("v1/threads/{thread_id}/messages")
    suspend fun createMessage(
        @Header("Authorization") authorization: String,
        @Path("thread_id") threadId: String,
        @Body request: CreateMessageRequestDto
    ): Response<ThreadMessageDto>
    
    @Headers("Content-Type: application/json", "OpenAI-Beta: assistants=v2")
    @GET("v1/threads/{thread_id}/messages")
    suspend fun getMessages(
        @Header("Authorization") authorization: String,
        @Path("thread_id") threadId: String,
        @Query("limit") limit: Int? = null,
        @Query("order") order: String? = "desc",
        @Query("after") after: String? = null,
        @Query("before") before: String? = null
    ): Response<MessagesResponseDto>
    
    @Headers("Content-Type: application/json", "OpenAI-Beta: assistants=v2")
    @POST("v1/threads/{thread_id}/runs")
    suspend fun createRun(
        @Header("Authorization") authorization: String,
        @Path("thread_id") threadId: String,
        @Body request: CreateRunRequestDto
    ): Response<RunDto>
    
    @Headers("Content-Type: application/json", "OpenAI-Beta: assistants=v2")
    @GET("v1/threads/{thread_id}/runs/{run_id}")
    suspend fun getRun(
        @Header("Authorization") authorization: String,
        @Path("thread_id") threadId: String,
        @Path("run_id") runId: String
    ): Response<RunDto>
}
