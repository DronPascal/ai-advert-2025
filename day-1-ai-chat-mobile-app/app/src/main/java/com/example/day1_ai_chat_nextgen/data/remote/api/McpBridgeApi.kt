package com.example.day1_ai_chat_nextgen.data.remote.api

import com.example.day1_ai_chat_nextgen.data.remote.dto.mcp.WebSearchRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.mcp.WebSearchResponseDto
import kotlinx.serialization.json.JsonElement
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface McpBridgeApi {
    @GET("healthz")
    suspend fun healthz(): Response<JsonElement>

    @GET("tools")
    suspend fun listTools(): Response<JsonElement>

    @POST("search")
    suspend fun search(
        @Body request: WebSearchRequestDto
    ): Response<WebSearchResponseDto>
}


