package com.example.day1_ai_chat_nextgen.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class OpenAIMessageDto(
    @SerialName("role") val role: String,
    @SerialName("content") val content: String,
    @SerialName("refusal") val refusal: String? = null
)

@Serializable
data class OpenAIChatRequestDto(
    @SerialName("model") val model: String = "gpt-3.5-turbo",
    @SerialName("messages") val messages: List<OpenAIMessageDto>,
    @SerialName("max_tokens") val maxTokens: Int = 150,
    @SerialName("temperature") val temperature: Double = 0.7,
    @SerialName("stream") val stream: Boolean = false
)

@Serializable
data class OpenAIChoiceDto(
    @SerialName("index") val index: Int,
    @SerialName("message") val message: OpenAIMessageDto,
    @SerialName("finish_reason") val finishReason: String
)

@Serializable
data class OpenAIUsageDto(
    @SerialName("prompt_tokens") val promptTokens: Int,
    @SerialName("completion_tokens") val completionTokens: Int,
    @SerialName("total_tokens") val totalTokens: Int
)

@Serializable
data class OpenAIChatResponseDto(
    @SerialName("id") val id: String,
    @SerialName("object") val `object`: String,
    @SerialName("created") val created: Long,
    @SerialName("model") val model: String,
    @SerialName("choices") val choices: List<OpenAIChoiceDto>,
    @SerialName("usage") val usage: OpenAIUsageDto,
    @SerialName("system_fingerprint") val systemFingerprint: String? = null
)

@Serializable
data class OpenAIErrorDto(
    @SerialName("message") val message: String,
    @SerialName("type") val type: String,
    @SerialName("param") val param: String? = null,
    @SerialName("code") val code: String? = null
)

@Serializable
data class OpenAIErrorResponseDto(
    @SerialName("error") val error: OpenAIErrorDto
)
