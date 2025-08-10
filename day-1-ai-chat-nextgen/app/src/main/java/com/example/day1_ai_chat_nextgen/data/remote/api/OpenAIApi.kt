package com.example.day1_ai_chat_nextgen.data.remote.api

import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIChatRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIChatResponseDto
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.Headers
import retrofit2.http.POST

interface OpenAIApi {
    
    @Headers("Content-Type: application/json")
    @POST("v1/chat/completions")
    suspend fun createChatCompletion(
        @Header("Authorization") authorization: String,
        @Body request: OpenAIChatRequestDto
    ): Response<OpenAIChatResponseDto>
}
