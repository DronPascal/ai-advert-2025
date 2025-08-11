package com.example.day1_ai_chat_nextgen.data.repository

import android.content.SharedPreferences
import com.example.day1_ai_chat_nextgen.BuildConfig
import com.example.day1_ai_chat_nextgen.data.local.dao.ChatMessageDao
import com.example.day1_ai_chat_nextgen.data.local.dao.ChatThreadDao
import com.example.day1_ai_chat_nextgen.data.local.dao.ResponseFormatDao
import com.example.day1_ai_chat_nextgen.data.mapper.toDomain
import com.example.day1_ai_chat_nextgen.data.mapper.toDomainMessages
import com.example.day1_ai_chat_nextgen.data.mapper.toEntity
import com.example.day1_ai_chat_nextgen.data.remote.api.OpenAIAssistantsApi
import com.example.day1_ai_chat_nextgen.data.remote.dto.CreateAssistantRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.CreateMessageRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.CreateRunRequestDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.CreateThreadRequestDto
import com.example.day1_ai_chat_nextgen.domain.model.ChatError
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.ChatThread
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole
import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat
import com.example.day1_ai_chat_nextgen.domain.model.Result
import com.example.day1_ai_chat_nextgen.domain.repository.ChatRepository
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import retrofit2.HttpException
import java.io.IOException
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AssistantsChatRepositoryImpl @Inject constructor(
    private val assistantsApi: OpenAIAssistantsApi,
    private val chatMessageDao: ChatMessageDao,
    private val chatThreadDao: ChatThreadDao,
    private val responseFormatDao: ResponseFormatDao,
    private val sharedPreferences: SharedPreferences,
    private val json: Json
) : ChatRepository {

    companion object {
        private const val PREF_ASSISTANT_ID = "assistant_id"
        private const val PREF_CURRENT_THREAD_ID = "current_thread_id"
        private const val RUN_POLL_INTERVAL_MS = 1000L
        private const val RUN_TIMEOUT_MS = 30000L
    }

    // Legacy interface implementation (for compatibility)
    override fun getMessages(): Flow<List<ChatMessage>> {
        return chatMessageDao.getAllMessages().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun sendMessage(message: ChatMessage): Result<ChatMessage> {
        return sendMessage(message.content)
    }

    override suspend fun clearHistory(): Result<Unit> {
        return try {
            chatMessageDao.clearAllMessages()
            chatThreadDao.clearAllThreads()
            sharedPreferences.edit().remove(PREF_CURRENT_THREAD_ID).apply()
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

    // New Assistants API implementation
    override suspend fun sendMessage(content: String): Result<ChatMessage> {
        return try {
            // Validate API key
            if (BuildConfig.OPENAI_API_KEY.isBlank()) {
                return Result.Error(ChatError.ApiKeyMissing)
            }

            // Get or create assistant
            val assistantResult = getOrCreateAssistant()
            if (assistantResult is Result.Error) {
                return Result.Error(assistantResult.exception)
            }
            val assistantId = (assistantResult as Result.Success).data

            // Get current thread or create new one
            val threadResult = getCurrentThread()
            val currentThread = when (threadResult) {
                is Result.Success -> threadResult.data
                is Result.Error -> {
                    // Create new thread if none exists
                    val newThreadResult = createNewThread()
                    if (newThreadResult is Result.Error) {
                        return Result.Error(newThreadResult.exception)
                    }
                    (newThreadResult as Result.Success).data
                }
                is Result.Loading -> null // This shouldn't happen in this context
            }

            if (currentThread == null) {
                return Result.Error(ChatError.ThreadNotFound)
            }

            // Add user message to thread
            val messageResponse = assistantsApi.createMessage(
                threadId = currentThread.threadId,
                request = CreateMessageRequestDto(
                    role = "user",
                    content = content
                )
            )

            if (!messageResponse.isSuccessful) {
                return handleHttpError(messageResponse.code(), messageResponse.errorBody()?.string())
            }

            // Save user message locally
            val userMessage = ChatMessage(
                id = UUID.randomUUID().toString(),
                content = content,
                role = MessageRole.USER,
                timestamp = System.currentTimeMillis()
            )
            chatMessageDao.insertMessage(userMessage.toEntity())

            // Create and run assistant
            val runResult = createAndRunAssistant(currentThread, assistantId)
            if (runResult is Result.Error) {
                return Result.Error(runResult.exception)
            }

            // Get latest messages from thread
            val messagesResponse = assistantsApi.getMessages(

                threadId = currentThread.threadId,
                limit = 1,
                order = "desc"
            )

            if (!messagesResponse.isSuccessful) {
                return handleHttpError(messagesResponse.code(), messagesResponse.errorBody()?.string())
            }

            val latestMessages = messagesResponse.body()?.data?.toDomainMessages() ?: emptyList()
            val assistantMessage = latestMessages.firstOrNull { it.role == MessageRole.ASSISTANT }
                ?: return Result.Error(ChatError.UnknownError("No assistant response found"))

            // Save assistant message locally
            chatMessageDao.insertMessage(assistantMessage.toEntity())

            // Update thread activity
            chatThreadDao.updateThreadActivity(currentThread.id, System.currentTimeMillis())

            Result.Success(assistantMessage)

        } catch (e: IOException) {
            Result.Error(ChatError.NetworkError)
        } catch (e: HttpException) {
            handleHttpError(e.code(), e.message())
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Unknown error occurred"))
        }
    }

    override suspend fun getCurrentThread(): Result<ChatThread?> {
        return try {
            val currentThreadId = sharedPreferences.getString(PREF_CURRENT_THREAD_ID, null)
            val thread = if (currentThreadId != null) {
                chatThreadDao.getThread(currentThreadId)?.toDomain()
            } else {
                chatThreadDao.getCurrentActiveThread()?.toDomain()
            }
            Result.Success(thread)
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to get current thread"))
        }
    }

    override suspend fun createNewThread(formatId: String?): Result<ChatThread> {
        return try {
            val assistantResult = getOrCreateAssistant()
            if (assistantResult is Result.Error) {
                return Result.Error(assistantResult.exception)
            }
            val assistantId = (assistantResult as Result.Success).data

            // Create OpenAI thread
            val threadResponse = assistantsApi.createThread(

                request = CreateThreadRequestDto()
            )

            if (!threadResponse.isSuccessful) {
                return handleHttpError(threadResponse.code(), threadResponse.errorBody()?.string())
            }

            val openAiThread = threadResponse.body()
                ?: return Result.Error(ChatError.UnknownError("Empty thread response"))

            // Create local thread
            val chatThread = ChatThread.create(
                threadId = openAiThread.id,
                assistantId = assistantId,
                formatId = formatId
            )

            // Deactivate all other threads
            chatThreadDao.deactivateAllThreads()

            // Save new thread
            chatThreadDao.insertThread(chatThread.toEntity())

            // Set as current thread
            sharedPreferences.edit()
                .putString(PREF_CURRENT_THREAD_ID, chatThread.id)
                .apply()

            // If format is specified, send format instructions
            formatId?.let { id ->
                val format = responseFormatDao.getFormat(id)
                if (format != null) {
                    setActiveFormat(format.toDomain())
                }
            }

            Result.Success(chatThread)

        } catch (e: IOException) {
            Result.Error(ChatError.NetworkError)
        } catch (e: HttpException) {
            handleHttpError(e.code(), e.message())
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to create thread"))
        }
    }

    override suspend fun switchToThread(threadId: String): Result<ChatThread> {
        return try {
            val thread = chatThreadDao.getThread(threadId)?.toDomain()
                ?: return Result.Error(ChatError.ThreadNotFound)

            // Deactivate all threads
            chatThreadDao.deactivateAllThreads()
            
            // Activate selected thread
            chatThreadDao.setThreadActive(threadId)

            // Set as current thread
            sharedPreferences.edit()
                .putString(PREF_CURRENT_THREAD_ID, threadId)
                .apply()

            Result.Success(thread)

        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to switch thread"))
        }
    }

    override fun getAllThreads(): Flow<List<ChatThread>> {
        return chatThreadDao.getAllThreads().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun setResponseFormat(formatInstructions: String): Result<ResponseFormat> {
        val customFormat = ResponseFormat.createCustomFormat(formatInstructions)
        return setResponseFormat(customFormat)
    }

    override suspend fun setResponseFormat(format: ResponseFormat): Result<ResponseFormat> {
        return try {
            // Deactivate all formats
            responseFormatDao.deactivateAllFormats()

            // Save and activate new format
            val activeFormat = format.copy(isActive = true)
            responseFormatDao.insertFormat(activeFormat.toEntity())

            // Update current thread's format
            val currentThread = getCurrentThread()
            if (currentThread is Result.Success && currentThread.data != null) {
                chatThreadDao.updateThreadFormat(currentThread.data.id, format.id)
                setActiveFormat(activeFormat)
            }

            Result.Success(activeFormat)

        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to set format"))
        }
    }

    override suspend fun getActiveFormat(): Result<ResponseFormat?> {
        return try {
            val format = responseFormatDao.getActiveFormat()?.toDomain()
            Result.Success(format)
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to get active format"))
        }
    }

    override suspend fun getPredefinedFormats(): Result<List<ResponseFormat>> {
        return try {
            val formats = responseFormatDao.getPredefinedFormats().map { it.toDomain() }
            Result.Success(formats)
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to get predefined formats"))
        }
    }

    override fun getAllFormats(): Flow<List<ResponseFormat>> {
        return responseFormatDao.getAllFormats().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun getOrCreateAssistant(): Result<String> {
        return try {
            val savedAssistantId = sharedPreferences.getString(PREF_ASSISTANT_ID, null)
            
            // Try to use saved assistant ID
            if (savedAssistantId != null) {
                val assistantResponse = assistantsApi.getAssistant(
    
                    assistantId = savedAssistantId
                )
                
                if (assistantResponse.isSuccessful) {
                    return Result.Success(savedAssistantId)
                }
            }

            // Create new assistant
            val createResponse = assistantsApi.createAssistant(

                request = CreateAssistantRequestDto(
                    instructions = ResponseFormat.getDefaultSystemInstructions()
                )
            )

            if (!createResponse.isSuccessful) {
                return handleHttpError(createResponse.code(), createResponse.errorBody()?.string())
            }

            val assistant = createResponse.body()
                ?: return Result.Error(ChatError.UnknownError("Empty assistant response"))

            // Save assistant ID
            sharedPreferences.edit()
                .putString(PREF_ASSISTANT_ID, assistant.id)
                .apply()

            Result.Success(assistant.id)

        } catch (e: IOException) {
            Result.Error(ChatError.NetworkError)
        } catch (e: HttpException) {
            handleHttpError(e.code(), e.message())
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to get or create assistant"))
        }
    }

    override suspend fun initializePredefinedFormats(): Result<Unit> {
        return try {
            val existingFormats = responseFormatDao.getPredefinedFormats()
            if (existingFormats.isEmpty()) {
                val predefinedFormats = ResponseFormat.PREDEFINED_FORMATS.map { it.toEntity() }
                responseFormatDao.insertFormats(predefinedFormats)
            }
            Result.Success(Unit)
        } catch (e: Exception) {
            Result.Error(ChatError.UnknownError(e.message ?: "Failed to initialize formats"))
        }
    }

    private suspend fun createAndRunAssistant(thread: ChatThread, assistantId: String): Result<Unit> {
        return try {
            // Get format instructions for the run
            val activeFormat = if (thread.activeFormatId != null) {
                responseFormatDao.getFormat(thread.activeFormatId)?.toDomain()
            } else null

            val additionalInstructions = activeFormat?.instructions

            // Create run
            val runResponse = assistantsApi.createRun(

                threadId = thread.threadId,
                request = CreateRunRequestDto(
                    assistantId = assistantId,
                    additionalInstructions = additionalInstructions
                )
            )

            if (!runResponse.isSuccessful) {
                return handleHttpError(runResponse.code(), runResponse.errorBody()?.string())
            }

            val run = runResponse.body()
                ?: return Result.Error(ChatError.UnknownError("Empty run response"))

            // Poll run status
            return pollRunStatus(thread.threadId, run.id)

        } catch (e: Exception) {
            Result.Error(ChatError.RunFailed)
        }
    }

    private suspend fun pollRunStatus(threadId: String, runId: String): Result<Unit> {
        val startTime = System.currentTimeMillis()
        
        while (System.currentTimeMillis() - startTime < RUN_TIMEOUT_MS) {
            try {
                val runResponse = assistantsApi.getRun(
    
                    threadId = threadId,
                    runId = runId
                )

                if (!runResponse.isSuccessful) {
                    return handleHttpError(runResponse.code(), runResponse.errorBody()?.string())
                }

                val run = runResponse.body()
                    ?: return Result.Error(ChatError.UnknownError("Empty run response"))

                when (run.status) {
                    "completed" -> return Result.Success(Unit)
                    "failed", "cancelled", "expired" -> {
                        val errorMessage = run.lastError?.message ?: "Run ${run.status}"
                        return Result.Error(ChatError.RunFailed)
                    }
                    "requires_action" -> {
                        return Result.Error(ChatError.RunRequiresAction(
                            run.requiredAction ?: "Unknown action required"
                        ))
                    }
                    "in_progress", "queued" -> {
                        delay(RUN_POLL_INTERVAL_MS)
                        continue
                    }
                }
            } catch (e: Exception) {
                return Result.Error(ChatError.NetworkError)
            }
        }
        
        return Result.Error(ChatError.RunTimeout)
    }

    private suspend fun setActiveFormat(format: ResponseFormat) {
        // This would send format instructions to the current thread
        // Implementation depends on how we want to handle format updates
        // Could send a system message with the format instructions
        // For now, we store the format in the database and apply it in runs
        responseFormatDao.setFormatActive(format.id)
    }

    private fun <T> handleHttpError(code: Int, errorBody: String?): Result<T> {
        return when (code) {
            401 -> Result.Error(ChatError.ApiKeyInvalid)
            429 -> Result.Error(ChatError.RateLimitExceeded)
            402 -> Result.Error(ChatError.InsufficientCredits)
            404 -> Result.Error(ChatError.AssistantNotFound)
            else -> {
                val details = try {
                    errorBody?.let { 
                        // Parse OpenAI error response if needed
                        it
                    } ?: "HTTP $code"
                } catch (e: Exception) {
                    "HTTP $code"
                }
                Result.Error(ChatError.ApiError(code, details))
            }
        }
    }
}
