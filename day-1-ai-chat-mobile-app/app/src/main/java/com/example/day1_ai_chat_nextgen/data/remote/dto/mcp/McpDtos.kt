package com.example.day1_ai_chat_nextgen.data.remote.dto.mcp

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class WebSearchRequestDto(
    @SerialName("query") val query: String,
    @SerialName("top_k") val topK: Int = 5,
    @SerialName("enrich") val enrich: Boolean = false
)

@Serializable
data class WebSearchResponseDto(
    @SerialName("results") val results: List<WebSearchResultDto> = emptyList()
)

@Serializable
data class WebSearchResultDto(
    @SerialName("title") val title: String = "",
    @SerialName("url") val url: String = "",
    @SerialName("snippet") val snippet: String = "",
    @SerialName("content") val content: String? = null
)


