package com.example.aiadvert2025.api

import retrofit2.Response
import retrofit2.http.*

// OpenAI API Models
data class OpenAIMessage(
    val role: String, // "system", "user", "assistant"
    val content: String
)

data class OpenAIChatRequest(
    val model: String = "gpt-3.5-turbo",
    val messages: List<OpenAIMessage>,
    val max_tokens: Int = 150,
    val temperature: Double = 0.7
)

data class OpenAIChoice(
    val message: OpenAIMessage,
    val finish_reason: String
)

data class OpenAIChatResponse(
    val id: String,
    val choices: List<OpenAIChoice>,
    val usage: Map<String, Int>
)

// JSONPlaceholder for fallback demo
data class Post(
    val userId: Int,
    val id: Int,
    val title: String,
    val body: String
)

interface OpenAIApi {
    @Headers("Content-Type: application/json")
    @POST("v1/chat/completions")
    suspend fun createChatCompletion(
        @Header("Authorization") authorization: String,
        @Body request: OpenAIChatRequest
    ): Response<OpenAIChatResponse>
}

interface ApiService {
    @GET("posts/{id}")
    suspend fun getPost(@Path("id") id: Int): Response<Post>
}
