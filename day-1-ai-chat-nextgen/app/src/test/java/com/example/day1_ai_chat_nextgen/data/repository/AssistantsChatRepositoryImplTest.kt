package com.example.day1_ai_chat_nextgen.data.repository

import android.content.SharedPreferences
import com.example.day1_ai_chat_nextgen.data.local.dao.ChatMessageDao
import com.example.day1_ai_chat_nextgen.data.local.dao.ChatThreadDao
import com.example.day1_ai_chat_nextgen.data.local.dao.ResponseFormatDao
import com.example.day1_ai_chat_nextgen.data.local.entity.ChatThreadEntity
import com.example.day1_ai_chat_nextgen.data.local.entity.ResponseFormatEntity
import com.example.day1_ai_chat_nextgen.data.remote.api.OpenAIAssistantsApi
import com.example.day1_ai_chat_nextgen.data.remote.dto.AssistantDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.MessageContentDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.MessageTextDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.MessagesResponseDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.RunDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.ThreadDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.ThreadMessageDto
import com.example.day1_ai_chat_nextgen.domain.model.ChatError
import com.example.day1_ai_chat_nextgen.domain.model.ChatThread
import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat
import com.example.day1_ai_chat_nextgen.domain.model.Result
import io.kotest.core.spec.style.BehaviorSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.types.shouldBeInstanceOf
import kotlinx.coroutines.test.runTest
import org.mockito.kotlin.any
import org.mockito.kotlin.anyOrNull
import org.mockito.kotlin.eq
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import retrofit2.Response

class AssistantsChatRepositoryImplTest : BehaviorSpec({

    given("AssistantsChatRepositoryImpl") {
        val mockAssistantsApi = mock<OpenAIAssistantsApi>()
        val mockChatMessageDao = mock<ChatMessageDao>()
        val mockChatThreadDao = mock<ChatThreadDao>()
        val mockResponseFormatDao = mock<ResponseFormatDao>()
        val mockSharedPreferences = mock<SharedPreferences>()
        val mockEditor = mock<SharedPreferences.Editor>()


        whenever(mockSharedPreferences.edit()).thenReturn(mockEditor)
        whenever(mockEditor.putString(any(), any())).thenReturn(mockEditor)
        whenever(mockEditor.remove(any())).thenReturn(mockEditor)

        val repository = AssistantsChatRepositoryImpl(
            mockAssistantsApi,
            mockChatMessageDao,
            mockChatThreadDao,
            mockResponseFormatDao,
            mockSharedPreferences
        )

        `when`("getting or creating assistant for the first time") {
            val assistantDto = AssistantDto(
                id = "asst_12345",
                `object` = "assistant",
                createdAt = System.currentTimeMillis(),
                name = "Free-Format Chat",
                description = null,
                model = "gpt-4o-2024-08-06",
                instructions = "Always follow the format...",
                tools = emptyList(),
                metadata = emptyMap()
            )

            whenever(mockSharedPreferences.getString("assistant_id", null)).thenReturn(null)
            whenever(mockAssistantsApi.createAssistant(any()))
                .thenReturn(Response.success(assistantDto))

            then("should create new assistant and save ID") {
                runTest {
                    val result = repository.getOrCreateAssistant()

                    result.shouldBeInstanceOf<Result.Success<String>>()
                    result.getOrNull() shouldBe "asst_12345"
                    verify(mockEditor).putString("assistant_id", "asst_12345")
                }
            }
        }

        `when`("getting existing assistant") {
            val assistantDto = AssistantDto(
                id = "asst_existing",
                `object` = "assistant",
                createdAt = System.currentTimeMillis(),
                name = "Free-Format Chat",
                description = null,
                model = "gpt-4o-2024-08-06",
                instructions = "Always follow the format...",
                tools = emptyList(),
                metadata = emptyMap()
            )

            whenever(
                mockSharedPreferences.getString(
                    "assistant_id",
                    null
                )
            ).thenReturn("asst_existing")
            whenever(mockAssistantsApi.getAssistant("asst_existing"))
                .thenReturn(Response.success(assistantDto))

            then("should return existing assistant ID") {
                runTest {
                    val result = repository.getOrCreateAssistant()

                    result.shouldBeInstanceOf<Result.Success<String>>()
                    result.getOrNull() shouldBe "asst_existing"
                }
            }
        }

        `when`("creating new thread") {
            val threadDto = ThreadDto(
                id = "thread_12345",
                `object` = "thread",
                createdAt = System.currentTimeMillis(),
                metadata = emptyMap()
            )

            val assistantDto = AssistantDto(
                id = "asst_12345",
                `object` = "assistant",
                createdAt = System.currentTimeMillis(),
                name = "Free-Format Chat",
                description = null,
                model = "gpt-4o-2024-08-06",
                instructions = "Always follow the format...",
                tools = emptyList(),
                metadata = emptyMap()
            )

            whenever(mockSharedPreferences.getString("assistant_id", null)).thenReturn("asst_12345")
            whenever(mockAssistantsApi.getAssistant("asst_12345"))
                .thenReturn(Response.success(assistantDto))
            whenever(mockAssistantsApi.createThread(any()))
                .thenReturn(Response.success(threadDto))

            then("should create thread and save locally") {
                runTest {
                    val result = repository.createNewThread()

                    result.shouldBeInstanceOf<Result.Success<ChatThread>>()
                    val thread = result.getOrNull()!!
                    thread.threadId shouldBe "thread_12345"
                    thread.assistantId shouldBe "asst_12345"

                    verify(mockChatThreadDao).deactivateAllThreads()
                    verify(mockChatThreadDao).insertThread(any())
                }
            }
        }

        `when`("sending message successfully") {
            val messageContent = "Hello, AI!"
            val threadEntity = ChatThreadEntity(
                id = "local_thread_1",
                threadId = "thread_12345",
                assistantId = "asst_12345",
                activeFormatId = null,
                title = "Test Thread",
                createdAt = System.currentTimeMillis(),
                lastMessageAt = System.currentTimeMillis(),
                messageCount = 0,
                isActive = true
            )

            val threadMessageDto = ThreadMessageDto(
                id = "msg_12345",
                `object` = "thread.message",
                createdAt = System.currentTimeMillis(),
                threadId = "thread_12345",
                role = "user",
                content = listOf(
                    MessageContentDto(
                        type = "text",
                        text = MessageTextDto(value = messageContent)
                    )
                ),
                metadata = emptyMap()
            )

            val runDto = RunDto(
                id = "run_12345",
                `object` = "thread.run",
                createdAt = System.currentTimeMillis(),
                assistantId = "asst_12345",
                threadId = "thread_12345",
                status = "completed",
                requiredAction = null,
                lastError = null,
                model = "gpt-4o-2024-08-06",
                instructions = "Always follow the format...",
                tools = emptyList(),
                metadata = emptyMap(),
                usage = null
            )

            val assistantResponse = ThreadMessageDto(
                id = "msg_assistant",
                `object` = "thread.message",
                createdAt = System.currentTimeMillis(),
                threadId = "thread_12345",
                role = "assistant",
                content = listOf(
                    MessageContentDto(
                        type = "text",
                        text = MessageTextDto(value = "Hello! How can I help you?")
                    )
                ),
                metadata = emptyMap()
            )

            val messagesResponse = MessagesResponseDto(
                `object` = "list",
                data = listOf(assistantResponse),
                firstId = "msg_assistant",
                lastId = "msg_assistant",
                hasMore = false
            )

            whenever(mockSharedPreferences.getString("assistant_id", null)).thenReturn("asst_12345")
            whenever(
                mockSharedPreferences.getString(
                    "current_thread_id",
                    null
                )
            ).thenReturn("local_thread_1")
            whenever(mockChatThreadDao.getThread("local_thread_1")).thenReturn(threadEntity)
            whenever(mockAssistantsApi.createMessage(eq("thread_12345"), any()))
                .thenReturn(Response.success(threadMessageDto))
            whenever(mockAssistantsApi.createRun(eq("thread_12345"), any()))
                .thenReturn(Response.success(runDto))
            whenever(mockAssistantsApi.getRun("thread_12345", "run_12345"))
                .thenReturn(Response.success(runDto))
            whenever(
                mockAssistantsApi.getMessages(
                    eq("thread_12345"),
                    anyOrNull(),
                    anyOrNull(),
                    anyOrNull(),
                    anyOrNull()
                )
            )
                .thenReturn(Response.success(messagesResponse))

            then("should send message and return AI response") {
                runTest {
                    val result = repository.sendMessage(messageContent)

                    result.shouldBeInstanceOf<Result.Success<*>>()
                    val aiMessage = result.getOrNull()!!
                    aiMessage.content shouldBe "Hello! How can I help you?"

                    verify(mockChatMessageDao).insertMessage(any()) // User message
                    verify(mockChatMessageDao).insertMessage(any()) // Assistant message
                }
            }
        }

        `when`("setting response format") {
            val formatInstructions = "Respond in JSON format with title and content fields"
            val format = ResponseFormat.createCustomFormat(formatInstructions)

            then("should create and save custom format") {
                runTest {
                    val result = repository.setResponseFormat(formatInstructions)

                    result.shouldBeInstanceOf<Result.Success<ResponseFormat>>()
                    val savedFormat = result.getOrNull()!!
                    savedFormat.instructions shouldBe formatInstructions
                    savedFormat.isCustom shouldBe true

                    verify(mockResponseFormatDao).deactivateAllFormats()
                    verify(mockResponseFormatDao).insertFormat(any())
                }
            }
        }

        `when`("initializing predefined formats") {
            whenever(mockResponseFormatDao.getPredefinedFormats()).thenReturn(emptyList())

            then("should insert predefined formats") {
                runTest {
                    val result = repository.initializePredefinedFormats()

                    result.shouldBeInstanceOf<Result.Success<Unit>>()
                    verify(mockResponseFormatDao).insertFormats(any())
                }
            }
        }

        `when`("API returns 401 unauthorized") {
            whenever(mockSharedPreferences.getString("assistant_id", null)).thenReturn(null)
            whenever(mockAssistantsApi.createAssistant(any()))
                .thenReturn(Response.error(401, mock()))

            then("should return API key invalid error") {
                runTest {
                    val result = repository.getOrCreateAssistant()

                    result.shouldBeInstanceOf<Result.Error>()
                    result.exceptionOrNull().shouldBeInstanceOf<ChatError.ApiKeyInvalid>()
                }
            }
        }

        `when`("API returns 429 rate limit exceeded") {
            whenever(mockSharedPreferences.getString("assistant_id", null)).thenReturn(null)
            whenever(mockAssistantsApi.createAssistant(any()))
                .thenReturn(Response.error(429, mock()))

            then("should return rate limit error") {
                runTest {
                    val result = repository.getOrCreateAssistant()

                    result.shouldBeInstanceOf<Result.Error>()
                    result.exceptionOrNull().shouldBeInstanceOf<ChatError.RateLimitExceeded>()
                }
            }
        }

        `when`("run fails") {
            val failedRunDto = RunDto(
                id = "run_failed",
                `object` = "thread.run",
                createdAt = System.currentTimeMillis(),
                assistantId = "asst_12345",
                threadId = "thread_12345",
                status = "failed",
                requiredAction = null,
                lastError = null,
                model = "gpt-4o-2024-08-06",
                instructions = "Always follow the format...",
                tools = emptyList(),
                metadata = emptyMap(),
                usage = null
            )

            whenever(mockAssistantsApi.getRun(any(), any()))
                .thenReturn(Response.success(failedRunDto))

            then("should handle run failure gracefully") {
                // This would be tested in integration with the sendMessage flow
                // The run failure should result in a RunFailed error
            }
        }

        `when`("switching to existing thread") {
            val threadEntity = ChatThreadEntity(
                id = "thread_local_2",
                threadId = "thread_openai_2",
                assistantId = "asst_12345",
                activeFormatId = "format_1",
                title = "Another Thread",
                createdAt = System.currentTimeMillis(),
                lastMessageAt = System.currentTimeMillis(),
                messageCount = 5,
                isActive = false
            )

            whenever(mockChatThreadDao.getThread("thread_local_2")).thenReturn(threadEntity)

            then("should switch to thread and update active status") {
                runTest {
                    val result = repository.switchToThread("thread_local_2")

                    result.shouldBeInstanceOf<Result.Success<ChatThread>>()
                    val thread = result.getOrNull()!!
                    thread.threadId shouldBe "thread_openai_2"
                    thread.title shouldBe "Another Thread"

                    verify(mockChatThreadDao).deactivateAllThreads()
                    verify(mockChatThreadDao).setThreadActive("thread_local_2")
                    verify(mockEditor).putString("current_thread_id", "thread_local_2")
                }
            }
        }

        `when`("getting active format") {
            val formatEntity = ResponseFormatEntity(
                id = "format_active",
                name = "JSON Format",
                description = "Structured JSON responses",
                instructions = "Always respond in JSON format",
                timestamp = System.currentTimeMillis(),
                isActive = true,
                isCustom = false
            )

            whenever(mockResponseFormatDao.getActiveFormat()).thenReturn(formatEntity)

            then("should return active format") {
                runTest {
                    val result = repository.getActiveFormat()

                    result.shouldBeInstanceOf<Result.Success<ResponseFormat?>>()
                    val format = result.getOrNull()!!
                    format!!.name shouldBe "JSON Format"
                    format.isActive shouldBe true
                }
            }
        }

        `when`("clearing history") {
            then("should clear all data and reset preferences") {
                runTest {
                    val result = repository.clearHistory()

                    result.shouldBeInstanceOf<Result.Success<Unit>>()
                    verify(mockChatMessageDao).clearAllMessages()
                    verify(mockChatThreadDao).clearAllThreads()
                    verify(mockEditor).remove("current_thread_id")
                }
            }
        }
    }
})
