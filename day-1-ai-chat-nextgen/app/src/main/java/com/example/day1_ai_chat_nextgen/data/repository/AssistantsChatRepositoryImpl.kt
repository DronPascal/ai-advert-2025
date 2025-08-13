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
    private val sharedPreferences: SharedPreferences
) : ChatRepository {

    companion object {
        private const val PREF_ASSISTANT_ID = "assistant_id"
        private const val PREF_CURRENT_THREAD_ID = "current_thread_id"
        private const val PREF_ASSISTANT1_ID = "assistant1_id"
        private const val PREF_ASSISTANT2_ID = "assistant2_id"
        private const val PREF_AGENT1_THREAD_ID = "agent1_thread_id"
        private const val PREF_AGENT2_THREAD_ID = "agent2_thread_id"
        private const val RUN_POLL_INTERVAL_MS = 1000L
        private const val RUN_TIMEOUT_MS = 30000L
        private const val HTTP_UNAUTHORIZED = 401
        private const val HTTP_PAYMENT_REQUIRED = 402
        private const val HTTP_NOT_FOUND = 404
        private const val HTTP_TOO_MANY_REQUESTS = 429
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

            // Add system message for history clear
            val clearMessage = ChatMessage(
                id = UUID.randomUUID().toString(),
                content = "История беседы очищена",
                role = MessageRole.SYSTEM,
                timestamp = System.currentTimeMillis()
            )
            chatMessageDao.insertMessage(clearMessage.toEntity())

            Result.Success(Unit)
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to clear history"))
        }
    }

    override suspend fun deleteMessage(messageId: String): Result<Unit> {
        return try {
            chatMessageDao.deleteMessage(messageId)
            Result.Success(Unit)
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to delete message"))
        }
    }

    // New Assistants API implementation
    @Suppress("ReturnCount") // Result pattern requires multiple returns for error handling 
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
                return handleHttpError(
                    messageResponse.code(),
                    messageResponse.errorBody()?.string()
                )
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
                return handleHttpError(
                    messagesResponse.code(),
                    messagesResponse.errorBody()?.string()
                )
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
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Unknown error occurred"))
        }
    }

    override suspend fun sendMessageDualAgents(content: String): Result<Unit> {
        return try {
            if (BuildConfig.OPENAI_API_KEY.isBlank()) {
                return Result.Error(ChatError.ApiKeyMissing)
            }

            // Ensure Agent 1 assistant and thread
            val agent1AssistantIdResult = ensureAgentAssistant(
                agentIndex = 1,
                name = "Agent 1 — Planner",
                instructions = com.example.day1_ai_chat_nextgen.domain.model.AgentPrompts.AGENT_1_SYSTEM_PROMPT
            )
            val agent1AssistantId = when (agent1AssistantIdResult) {
                is Result.Success -> agent1AssistantIdResult.data
                is Result.Error -> return Result.Error(agent1AssistantIdResult.exception)
                is Result.Loading -> return Result.Error(ChatError.UnknownError("Unexpected loading state"))
            }

            val agent1ThreadResult = ensureAgentThread(agentIndex = 1, assistantId = agent1AssistantId)
            val agent1Thread = when (agent1ThreadResult) {
                is Result.Success -> agent1ThreadResult.data
                is Result.Error -> return Result.Error(agent1ThreadResult.exception)
                is Result.Loading -> return Result.Error(ChatError.UnknownError("Unexpected loading state"))
            }

            // Post user message to Agent 1
            val messageResponse = assistantsApi.createMessage(
                threadId = agent1Thread.threadId,
                request = CreateMessageRequestDto(role = "user", content = content)
            )
            if (!messageResponse.isSuccessful) {
                return handleHttpError(messageResponse.code(), messageResponse.errorBody()?.string())
            }

            // Save user message locally immediately for stable UI (optimistic persisted)
            val userMessageLocal = ChatMessage(
                id = UUID.randomUUID().toString(),
                content = content,
                role = MessageRole.USER,
                timestamp = System.currentTimeMillis()
            )
            chatMessageDao.insertMessage(userMessageLocal.toEntity())
            chatThreadDao.updateThreadActivity(agent1Thread.id, System.currentTimeMillis())

            // Run Agent 1
            val runResponse = assistantsApi.createRun(
                threadId = agent1Thread.threadId,
                request = CreateRunRequestDto(
                    assistantId = agent1AssistantId,
                    temperature = 0.2,
                    additionalInstructions = com.example.day1_ai_chat_nextgen.domain.model.AgentPrompts.AGENT_1_SYSTEM_PROMPT
                )
            )
            if (!runResponse.isSuccessful) {
                return handleHttpError(runResponse.code(), runResponse.errorBody()?.string())
            }
            val run = runResponse.body() ?: return Result.Error(ChatError.UnknownError("Empty run response"))
            val pollResult = pollRunStatus(agent1Thread.threadId, run.id)
            if (pollResult is Result.Error) return Result.Error(pollResult.exception)

            // Fetch latest assistant message from Agent 1
            val latestResponse = assistantsApi.getMessages(
                threadId = agent1Thread.threadId,
                limit = 1,
                order = "desc"
            )
            if (!latestResponse.isSuccessful) {
                return handleHttpError(latestResponse.code(), latestResponse.errorBody()?.string())
            }
            val lastAssistant = latestResponse.body()?.data?.toDomainMessages()?.firstOrNull()
                ?: return Result.Error(ChatError.UnknownError("No message returned from Agent 1"))

            // Save Agent1 assistant message locally (strip HANDOFF header from persisted text)
            val possiblyStripped = stripHandoffHeader(lastAssistant.content)
            val persistedA1 = lastAssistant.copy(content = possiblyStripped)
            chatMessageDao.insertMessage(persistedA1.toEntity())

            // Divider: Agent 1 → handoff
            if (com.example.day1_ai_chat_nextgen.domain.model.AgentPrompts.extractPayloadForAgent2(lastAssistant.content) != null) {
                insertSystemDivider("Передача сообщения во 2-го агента")
            }

            // If no handoff, finish
            val payload = com.example.day1_ai_chat_nextgen.domain.model.AgentPrompts.extractPayloadForAgent2(lastAssistant.content)
            if (payload == null) {
                chatThreadDao.updateThreadActivity(agent1Thread.id, System.currentTimeMillis())
                return Result.Success(Unit)
            }

            // Ensure Agent 2 assistant and thread
            val agent2AssistantIdResult = ensureAgentAssistant(
                agentIndex = 2,
                name = "Agent 2 — Clown Rewriter",
                instructions = com.example.day1_ai_chat_nextgen.domain.model.AgentPrompts.AGENT_2_SYSTEM_PROMPT
            )
            val agent2AssistantId = when (agent2AssistantIdResult) {
                is Result.Success -> agent2AssistantIdResult.data
                is Result.Error -> return Result.Error(agent2AssistantIdResult.exception)
                is Result.Loading -> return Result.Error(ChatError.UnknownError("Unexpected loading state"))
            }
            val agent2ThreadResult = ensureAgentThread(agentIndex = 2, assistantId = agent2AssistantId)
            val agent2Thread = when (agent2ThreadResult) {
                is Result.Success -> agent2ThreadResult.data
                is Result.Error -> return Result.Error(agent2ThreadResult.exception)
                is Result.Loading -> return Result.Error(ChatError.UnknownError("Unexpected loading state"))
            }

            // Agent 2 receives payload as-is
            val a2MessageResponse = assistantsApi.createMessage(
                threadId = agent2Thread.threadId,
                request = CreateMessageRequestDto(role = "user", content = payload)
            )
            if (!a2MessageResponse.isSuccessful) {
                return handleHttpError(a2MessageResponse.code(), a2MessageResponse.errorBody()?.string())
            }

            // Divider immediately when Agent 2 receives the payload (before Agent 2 reply)
            insertSystemDivider("Сообщение принято агентом 2")

            val a2RunResponse = assistantsApi.createRun(
                threadId = agent2Thread.threadId,
                request = CreateRunRequestDto(
                    assistantId = agent2AssistantId,
                    temperature = 0.2,
                    additionalInstructions = com.example.day1_ai_chat_nextgen.domain.model.AgentPrompts.AGENT_2_SYSTEM_PROMPT
                )
            )
            if (!a2RunResponse.isSuccessful) {
                return handleHttpError(a2RunResponse.code(), a2RunResponse.errorBody()?.string())
            }
            val a2Run = a2RunResponse.body() ?: return Result.Error(ChatError.UnknownError("Empty run response (Agent2)"))
            val a2Poll = pollRunStatus(agent2Thread.threadId, a2Run.id)
            if (a2Poll is Result.Error) return Result.Error(a2Poll.exception)

            val a2Latest = assistantsApi.getMessages(
                threadId = agent2Thread.threadId,
                limit = 1,
                order = "desc"
            )
            if (!a2Latest.isSuccessful) {
                return handleHttpError(a2Latest.code(), a2Latest.errorBody()?.string())
            }
            val a2Reply = a2Latest.body()?.data?.toDomainMessages()?.firstOrNull()
                ?: return Result.Error(ChatError.UnknownError("No message returned from Agent 2"))

            // Persist Agent 2 reply
            chatMessageDao.insertMessage(a2Reply.toEntity())

            // Update activity on both threads
            val now = System.currentTimeMillis()
            chatThreadDao.updateThreadActivity(agent1Thread.id, now)
            chatThreadDao.updateThreadActivity(agent2Thread.id, now)

            Result.Success(Unit)
        } catch (e: IOException) {
            Result.Error(ChatError.NetworkError)
        } catch (e: HttpException) {
            handleHttpError(e.code(), e.message())
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Unknown error"))
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
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to get current thread"))
        }
    }

    @Suppress("ReturnCount") // Result pattern requires multiple returns for error handling
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

            // Add system message for new thread creation
            val newThreadMessage = ChatMessage(
                id = UUID.randomUUID().toString(),
                content = "Новая беседа начата",
                role = MessageRole.SYSTEM,
                timestamp = System.currentTimeMillis()
            )
            chatMessageDao.insertMessage(newThreadMessage.toEntity())

            // If format is specified, send format instructions
            formatId?.let { id ->
                val format = responseFormatDao.getFormat(id)
                if (format != null) {
                    setActiveFormat(format.toDomain())

                    // Send format instruction message to the OpenAI thread
                    sendFormatInstructionMessage(chatThread, format.toDomain())
                }
            }

            Result.Success(chatThread)

        } catch (e: IOException) {
            Result.Error(ChatError.NetworkError)
        } catch (e: HttpException) {
            handleHttpError(e.code(), e.message())
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to create thread"))
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

        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to switch thread"))
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

        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to set format"))
        }
    }

    override suspend fun updateCurrentThreadFormat(format: ResponseFormat): Result<Unit> {
        return try {
            val currentThreadResult = getCurrentThread()
            if (currentThreadResult !is Result.Success || currentThreadResult.data == null) {
                return Result.Error(ChatError.ThreadNotFound)
            }

            val currentThread = currentThreadResult.data

            // Deactivate all formats
            responseFormatDao.deactivateAllFormats()

            // Save and activate new format
            val activeFormat = format.copy(isActive = true)
            responseFormatDao.insertFormat(activeFormat.toEntity())

            // Update current thread's format
            chatThreadDao.updateThreadFormat(currentThread.id, activeFormat.id)

            // Send format instruction message to the thread
            sendFormatInstructionMessage(currentThread, activeFormat)

            Result.Success(Unit)

        } catch (expected: Exception) {
            Result.Error(
                ChatError.UnknownError(
                    expected.message ?: "Failed to update thread format"
                )
            )
        }
    }

    override suspend fun deactivateAllFormats(): Result<Unit> {
        return try {
            responseFormatDao.deactivateAllFormats()
            Result.Success(Unit)
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to deactivate formats"))
        }
    }

    override suspend fun getActiveFormat(): Result<ResponseFormat?> {
        return try {
            val format = responseFormatDao.getActiveFormat()?.toDomain()
            Result.Success(format)
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to get active format"))
        }
    }

    override suspend fun getPredefinedFormats(): Result<List<ResponseFormat>> {
        return try {
            val formats = responseFormatDao.getPredefinedFormats().map { it.toDomain() }
            Result.Success(formats)
        } catch (expected: Exception) {
            Result.Error(
                ChatError.UnknownError(
                    expected.message ?: "Failed to get predefined formats"
                )
            )
        }
    }

    override fun getAllFormats(): Flow<List<ResponseFormat>> {
        return responseFormatDao.getAllFormats().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    @Suppress("ReturnCount") // Result pattern requires multiple returns for error handling
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
        } catch (expected: Exception) {
            Result.Error(
                ChatError.UnknownError(
                    expected.message ?: "Failed to get or create assistant"
                )
            )
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
        } catch (expected: Exception) {
            Result.Error(ChatError.UnknownError(expected.message ?: "Failed to initialize formats"))
        }
    }

    @Suppress("ReturnCount") // Result pattern requires multiple returns for error handling
    private suspend fun createAndRunAssistant(
        thread: ChatThread,
        assistantId: String
    ): Result<Unit> {
        return try {
            // Get format instructions for the run
            val activeFormat = if (thread.activeFormatId != null) {
                responseFormatDao.getFormat(thread.activeFormatId)?.toDomain()
            } else null

            val baseInstructions = ResponseFormat.getDefaultSystemInstructions()
            val additionalInstructions = activeFormat?.instructions?.let { "$baseInstructions\n\n$it" } ?: baseInstructions

            // Create run
            val runResponse = assistantsApi.createRun(

                threadId = thread.threadId,
                request = CreateRunRequestDto(
                    assistantId = assistantId,
                    additionalInstructions = additionalInstructions,
                    temperature = 0.2
                )
            )

            if (!runResponse.isSuccessful) {
                return handleHttpError(runResponse.code(), runResponse.errorBody()?.string())
            }

            val run = runResponse.body()
                ?: return Result.Error(ChatError.UnknownError("Empty run response"))

            // Poll run status
            return pollRunStatus(thread.threadId, run.id)

        } catch (expected: Exception) {
            Result.Error(ChatError.RunFailed)
        }
    }

    @Suppress("ReturnCount") // Polling pattern requires multiple returns for different states
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
                        return Result.Error(ChatError.RunFailed)
                    }

                    "requires_action" -> {
                        return Result.Error(
                            ChatError.RunRequiresAction(
                                run.requiredAction ?: "Unknown action required"
                            )
                        )
                    }

                    "in_progress", "queued" -> {
                        delay(RUN_POLL_INTERVAL_MS)
                        continue
                    }
                }
            } catch (expected: Exception) {
                return Result.Error(ChatError.NetworkError)
            }
        }

        return Result.Error(ChatError.RunTimeout)
    }

    private fun stripHandoffHeader(text: String): String {
        val lines = text.trim().lines()
        if (lines.isEmpty()) return text
        return if (lines.first().trim() == com.example.day1_ai_chat_nextgen.domain.model.AgentPrompts.HANDOFF_PREFIX) {
            lines.drop(1).joinToString("\n").trim()
        } else text
    }

    private suspend fun insertSystemDivider(message: String) {
        val systemMessage = ChatMessage(
            id = UUID.randomUUID().toString(),
            content = message, // icon is inferred by UI parser
            role = MessageRole.SYSTEM,
            timestamp = System.currentTimeMillis()
        )
        chatMessageDao.insertMessage(systemMessage.toEntity())
    }

    private suspend fun ensureAgentAssistant(
        agentIndex: Int,
        name: String,
        instructions: String
    ): Result<String> {
        val key = if (agentIndex == 1) PREF_ASSISTANT1_ID else PREF_ASSISTANT2_ID
        val saved = sharedPreferences.getString(key, null)
        if (saved != null) {
            val resp = assistantsApi.getAssistant(saved)
            if (resp.isSuccessful) return Result.Success(saved)
        }
        val created = assistantsApi.createAssistant(
            request = CreateAssistantRequestDto(
                name = name,
                instructions = instructions
            )
        )
        if (!created.isSuccessful) return handleHttpError(created.code(), created.errorBody()?.string())
        val assistant = created.body() ?: return Result.Error(ChatError.UnknownError("Empty assistant"))
        sharedPreferences.edit().putString(key, assistant.id).apply()
        return Result.Success(assistant.id)
    }

    private suspend fun ensureAgentThread(agentIndex: Int, assistantId: String): Result<ChatThread> {
        val key = if (agentIndex == 1) PREF_AGENT1_THREAD_ID else PREF_AGENT2_THREAD_ID
        val savedLocalId = sharedPreferences.getString(key, null)
        val existing = if (savedLocalId != null) chatThreadDao.getThread(savedLocalId) else null
        if (existing != null) return Result.Success(existing.toDomain())

        val threadResp = assistantsApi.createThread(CreateThreadRequestDto())
        if (!threadResp.isSuccessful) return handleHttpError(threadResp.code(), threadResp.errorBody()?.string())
        val openAiThread = threadResp.body() ?: return Result.Error(ChatError.UnknownError("Empty thread"))
        val chatThread = ChatThread.create(threadId = openAiThread.id, assistantId = assistantId)
        chatThreadDao.insertThread(chatThread.toEntity())
        sharedPreferences.edit().putString(key, chatThread.id).apply()
        return Result.Success(chatThread)
    }

    private suspend fun setActiveFormat(format: ResponseFormat) {
        // This would send format instructions to the current thread
        // Implementation depends on how we want to handle format updates
        // Could send a system message with the format instructions
        // For now, we store the format in the database and apply it in runs
        responseFormatDao.setFormatActive(format.id)
    }

    private suspend fun sendFormatInstructionMessage(thread: ChatThread, format: ResponseFormat) {
        try {
            val formatMessage = """
                🔄 НОВЫЙ ФОРМАТ ОТВЕТОВ УСТАНОВЛЕН:
                
                ${format.name}
                
                ${format.instructions}
                
                Пожалуйста, используй этот формат для всех последующих ответов в данном треде.
            """.trimIndent()

            // Send format instruction message to the thread
            val messageResponse = assistantsApi.createMessage(
                threadId = thread.threadId,
                request = CreateMessageRequestDto(
                    role = "user",
                    content = formatMessage
                )
            )

            if (messageResponse.isSuccessful) {
                // Save the format instruction message locally as a system message
                val systemMessage = ChatMessage(
                    id = UUID.randomUUID().toString(),
                    content = "Формат ответов обновлен: ${format.name}",
                    role = MessageRole.SYSTEM, // Use SYSTEM role for divider display
                    timestamp = System.currentTimeMillis()
                )
                chatMessageDao.insertMessage(systemMessage.toEntity())
            }
        } catch (expected: Exception) {
            // Non-critical error, just log it if needed
            // The format is still saved and will be applied in future runs
        }
    }

    private fun <T> handleHttpError(code: Int, errorBody: String?): Result<T> {
        return when (code) {
            HTTP_UNAUTHORIZED -> Result.Error(ChatError.ApiKeyInvalid)
            HTTP_TOO_MANY_REQUESTS -> Result.Error(ChatError.RateLimitExceeded)
            HTTP_PAYMENT_REQUIRED -> Result.Error(ChatError.InsufficientCredits)
            HTTP_NOT_FOUND -> Result.Error(ChatError.AssistantNotFound)
            else -> {
                val details = try {
                    errorBody?.let {
                        // Parse OpenAI error response if needed
                        it
                    } ?: "HTTP $code"
                } catch (expected: Exception) {
                    "HTTP $code"
                }
                Result.Error(ChatError.ApiError(code, details))
            }
        }
    }
}
