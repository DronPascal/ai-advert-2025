package com.example.day1_ai_chat_nextgen.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Assistant DTOs
@Serializable
data class CreateAssistantRequestDto(
    @SerialName("model") val model: String = "gpt-4o-mini",
    @SerialName("name") val name: String = "Free-Format Chat",
    @SerialName("instructions") val instructions: String,
    @SerialName("tools") val tools: List<AssistantToolDto> = emptyList(),
    @SerialName("metadata") val metadata: Map<String, String> = emptyMap()
)

@Serializable
data class AssistantDto(
    @SerialName("id") val id: String,
    @SerialName("object") val `object`: String,
    @SerialName("created_at") val createdAt: Long,
    @SerialName("name") val name: String?,
    @SerialName("description") val description: String?,
    @SerialName("model") val model: String,
    @SerialName("instructions") val instructions: String?,
    @SerialName("tools") val tools: List<AssistantToolDto>,
    @SerialName("metadata") val metadata: Map<String, String>
)

@Serializable
data class AssistantToolDto(
    @SerialName("type") val type: String
)

// Thread DTOs
@Serializable
data class CreateThreadRequestDto(
    @SerialName("messages") val messages: List<ThreadMessageDto> = emptyList(),
    @SerialName("metadata") val metadata: Map<String, String> = emptyMap()
)

@Serializable
data class ThreadDto(
    @SerialName("id") val id: String,
    @SerialName("object") val `object`: String,
    @SerialName("created_at") val createdAt: Long,
    @SerialName("metadata") val metadata: Map<String, String>
)

// Message DTOs
@Serializable
data class CreateMessageRequestDto(
    @SerialName("role") val role: String,
    @SerialName("content") val content: String,
    @SerialName("metadata") val metadata: Map<String, String> = emptyMap()
)

@Serializable
data class ThreadMessageDto(
    @SerialName("id") val id: String,
    @SerialName("object") val `object`: String,
    @SerialName("created_at") val createdAt: Long,
    @SerialName("thread_id") val threadId: String,
    @SerialName("role") val role: String,
    @SerialName("content") val content: List<MessageContentDto>,
    @SerialName("metadata") val metadata: Map<String, String>
)

@Serializable
data class MessageContentDto(
    @SerialName("type") val type: String,
    @SerialName("text") val text: MessageTextDto?
)

@Serializable
data class MessageTextDto(
    @SerialName("value") val value: String,
    @SerialName("annotations") val annotations: List<String> = emptyList()
)

@Serializable
data class MessagesResponseDto(
    @SerialName("object") val `object`: String,
    @SerialName("data") val data: List<ThreadMessageDto>,
    @SerialName("first_id") val firstId: String?,
    @SerialName("last_id") val lastId: String?,
    @SerialName("has_more") val hasMore: Boolean
)

// Run DTOs
@Serializable
data class CreateRunRequestDto(
    @SerialName("assistant_id") val assistantId: String,
    @SerialName("model") val model: String? = null,
    @SerialName("instructions") val instructions: String? = null,
    @SerialName("additional_instructions") val additionalInstructions: String? = null,
    @SerialName("tools") val tools: List<AssistantToolDto>? = null,
    @SerialName("metadata") val metadata: Map<String, String> = emptyMap(),
    @SerialName("temperature") val temperature: Double? = null,
    @SerialName("max_prompt_tokens") val maxPromptTokens: Int? = null,
    @SerialName("max_completion_tokens") val maxCompletionTokens: Int? = null
)

@Serializable
data class RunDto(
    @SerialName("id") val id: String,
    @SerialName("object") val `object`: String,
    @SerialName("created_at") val createdAt: Long,
    @SerialName("assistant_id") val assistantId: String,
    @SerialName("thread_id") val threadId: String,
    @SerialName("status") val status: String,
    @SerialName("required_action") val requiredAction: String? = null,
    @SerialName("last_error") val lastError: RunErrorDto? = null,
    @SerialName("model") val model: String,
    @SerialName("instructions") val instructions: String,
    @SerialName("tools") val tools: List<AssistantToolDto>,
    @SerialName("metadata") val metadata: Map<String, String>,
    @SerialName("usage") val usage: RunUsageDto? = null
)

@Serializable
data class RunErrorDto(
    @SerialName("code") val code: String,
    @SerialName("message") val message: String
)

@Serializable
data class RunUsageDto(
    @SerialName("prompt_tokens") val promptTokens: Int,
    @SerialName("completion_tokens") val completionTokens: Int,
    @SerialName("total_tokens") val totalTokens: Int
)
