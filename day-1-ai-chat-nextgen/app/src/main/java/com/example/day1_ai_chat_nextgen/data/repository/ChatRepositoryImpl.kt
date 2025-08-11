package com.example.day1_ai_chat_nextgen.data.repository

import com.example.day1_ai_chat_nextgen.BuildConfig
import com.example.day1_ai_chat_nextgen.data.local.dao.ChatMessageDao
import com.example.day1_ai_chat_nextgen.data.mapper.toDomain
import com.example.day1_ai_chat_nextgen.data.mapper.toEntity
import com.example.day1_ai_chat_nextgen.data.mapper.toOpenAIDto
import com.example.day1_ai_chat_nextgen.data.remote.api.OpenAIApi
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIChatRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIErrorResponseDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIMessageDto
import com.example.day1_ai_chat_nextgen.domain.model.ChatError
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.ChatThread
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole
import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat
import com.example.day1_ai_chat_nextgen.domain.model.Result
import com.example.day1_ai_chat_nextgen.domain.repository.ChatRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import retrofit2.HttpException
import java.io.IOException
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LegacyChatRepositoryImpl @Inject constructor(
    private val openAIApi: OpenAIApi,
    private val chatMessageDao: ChatMessageDao,
    private val json: Json
) : ChatRepository {

    override fun getMessages(): Flow<List<ChatMessage>> {
        return chatMessageDao.getAllMessages().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun sendMessage(message: ChatMessage): Result<ChatMessage> {
        return try {
            // Save user message locally
            chatMessageDao.insertMessage(message.toEntity())

            // Validate API key
            if (BuildConfig.OPENAI_API_KEY.isBlank()) {
                return Result.Error(ChatError.ApiKeyMissing)
            }

            // Get conversation history for context
            val conversationHistory = buildConversationHistory()
            val messages = conversationHistory + message.toOpenAIDto()

            val request = OpenAIChatRequestDto(
                model = "gpt-3.5-turbo",
                messages = messages,
                maxTokens = 150,
                temperature = 0.7
            )

            val response = openAIApi.createChatCompletion(

                request = request
            )

            if (response.isSuccessful) {
                val responseBody = response.body()
                    ?: return Result.Error(ChatError.UnknownError("Empty response body"))

                if (responseBody.choices.isEmpty()) {
                    return Result.Error(ChatError.UnknownError("No choices in response"))
                }

                val aiMessage = responseBody.choices.first().message
                
                // Check for content refusal
                if (aiMessage.refusal != null) {
                    return Result.Error(ChatError.ContentFiltered)
                }

                val assistantMessage = ChatMessage(
                    id = UUID.randomUUID().toString(),
                    content = aiMessage.content.takeIf { it.isNotBlank() }
                        ?: return Result.Error(ChatError.UnknownError("Empty content in response")),
                    role = MessageRole.ASSISTANT,
                    timestamp = System.currentTimeMillis()
                )

                // Save assistant message locally
                chatMessageDao.insertMessage(assistantMessage.toEntity())

                Result.Success(assistantMessage)
            } else {
                handleHttpError(response.code(), response.errorBody()?.string())
            }
        } catch (e: IOException) {
            Result.Error(ChatError.NetworkError)
        } catch (e: HttpException) {
            handleHttpError(e.code(), e.message())
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Unknown error occurred"))
        }
    }

    override suspend fun clearHistory(): Result<Unit> {
        return try {
            chatMessageDao.clearAllMessages()
            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to clear history"))
        }
    }

    override suspend fun deleteMessage(messageId: String): Result<Unit> {
        return try {
            chatMessageDao.deleteMessage(messageId)
            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to delete message"))
        }
    }

    private suspend fun buildConversationHistory(): List<OpenAIMessageDto> {
        val messages = mutableListOf<OpenAIMessageDto>()
        
        // Add system message
        messages.add(
            OpenAIMessageDto(
                role = "system",
                content = "You are a helpful AI assistant. Respond concisely and helpfully in Russian."
            )
        )

        // Get recent conversation history (last 10 messages for context)
        val recentMessages = chatMessageDao.getAllMessages()
        // Note: This is simplified - in real implementation you'd want to limit the query
        
        return messages
    }

    private fun handleHttpError(code: Int, errorBody: String?): Result<ChatMessage> {
        return when (code) {
            401 -> Result.Error(ChatError.ApiKeyInvalid)
            429 -> Result.Error(ChatError.RateLimitExceeded)
            402 -> Result.Error(ChatError.InsufficientCredits)
            404 -> Result.Error(ChatError.ModelNotAvailable)
            else -> {
                val errorMessage = try {
                    errorBody?.let { 
                        json.decodeFromString<OpenAIErrorResponseDto>(it).error.message 
                    } ?: "HTTP $code"
                } catch (e: Exception) {
                    "HTTP $code"
                }
                Result.Error(ChatError.ApiError(code, errorMessage))
            }
        }
    }

    // Stub implementations for new interface methods (will be replaced by AssistantsChatRepositoryImpl)
    override suspend fun sendMessage(content: String): Result<ChatMessage> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override suspend fun getCurrentThread(): Result<ChatThread?> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override suspend fun createNewThread(formatId: String?): Result<ChatThread> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override suspend fun switchToThread(threadId: String): Result<ChatThread> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override fun getAllThreads(): Flow<List<ChatThread>> {
        return flowOf(emptyList())
    }

    override suspend fun setResponseFormat(formatInstructions: String): Result<ResponseFormat> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override suspend fun setResponseFormat(format: ResponseFormat): Result<ResponseFormat> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override suspend fun getActiveFormat(): Result<ResponseFormat?> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override suspend fun getPredefinedFormats(): Result<List<ResponseFormat>> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override fun getAllFormats(): Flow<List<ResponseFormat>> {
        return flowOf(emptyList())
    }

    override suspend fun getOrCreateAssistant(): Result<String> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }

    override suspend fun initializePredefinedFormats(): Result<Unit> {
        return Result.Error(ChatError.UnknownError("Use AssistantsChatRepositoryImpl instead"))
    }
}
