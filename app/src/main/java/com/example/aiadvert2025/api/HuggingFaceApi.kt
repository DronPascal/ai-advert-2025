package com.example.aiadvert2025.api

import retrofit2.Response
import retrofit2.http.*

// OpenAI API Models
data class OpenAIMessage(
    val role: String, // "system", "user", "assistant"
    val content: String,
    val refusal: String? = null
)

data class OpenAIChatRequest(
    val model: String = "gpt-3.5-turbo",
    val messages: List<OpenAIMessage>,
    val max_tokens: Int = 150,
    val temperature: Double = 0.7
)

data class OpenAIChoice(
    val index: Int,
    val message: OpenAIMessage,
    val finish_reason: String,
    val logprobs: Any? = null
)

data class OpenAIUsage(
    val prompt_tokens: Int,
    val completion_tokens: Int,
    val total_tokens: Int,
    val prompt_tokens_details: Map<String, Int>? = null,
    val completion_tokens_details: Map<String, Int>? = null
)

data class OpenAIChatResponse(
    val id: String,
    val `object`: String,
    val created: Long,
    val model: String,
    val choices: List<OpenAIChoice>,
    val usage: OpenAIUsage,
    val service_tier: String? = null,
    val system_fingerprint: String? = null
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
