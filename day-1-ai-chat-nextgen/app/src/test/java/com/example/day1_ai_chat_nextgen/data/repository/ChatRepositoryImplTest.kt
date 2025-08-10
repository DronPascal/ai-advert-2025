package com.example.day1_ai_chat_nextgen.data.repository

import com.example.day1_ai_chat_nextgen.data.local.dao.ChatMessageDao
import com.example.day1_ai_chat_nextgen.data.local.entity.ChatMessageEntity
import com.example.day1_ai_chat_nextgen.data.remote.api.OpenAIApi
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIChatResponseDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIChoiceDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIMessageDto
import com.example.day1_ai_chat_nextgen.data.remote.dto.OpenAIUsageDto
import com.example.day1_ai_chat_nextgen.domain.model.ChatError
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole
import com.example.day1_ai_chat_nextgen.domain.model.Result
import io.kotest.core.spec.style.BehaviorSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.types.shouldBeInstanceOf
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.runTest
import kotlinx.serialization.json.Json
import org.mockito.kotlin.any
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever
import retrofit2.Response

class ChatRepositoryImplTest : BehaviorSpec({

    given("ChatRepositoryImpl") {
        val mockOpenAIApi = mock<OpenAIApi>()
        val mockChatMessageDao = mock<ChatMessageDao>()
        val json = Json { ignoreUnknownKeys = true }
        
        val repository = ChatRepositoryImpl(mockOpenAIApi, mockChatMessageDao, json)

        `when`("getting messages") {
            val entities = listOf(
                ChatMessageEntity(
                    id = "1",
                    content = "Hello",
                    role = "USER",
                    timestamp = System.currentTimeMillis()
                )
            )
            
            whenever(mockChatMessageDao.getAllMessages()).thenReturn(flowOf(entities))

            then("should return mapped domain messages") {
                runTest {
                    repository.getMessages().collect { messages ->
                        messages.size shouldBe 1
                        messages.first().content shouldBe "Hello"
                        messages.first().role shouldBe MessageRole.USER
                    }
                }
            }
        }

        `when`("sending message successfully") {
            val userMessage = ChatMessage(
                id = "test-id",
                content = "Hello, AI!",
                role = MessageRole.USER
            )

            val openAIResponse = OpenAIChatResponseDto(
                id = "response-id",
                `object` = "chat.completion",
                created = System.currentTimeMillis(),
                model = "gpt-3.5-turbo",
                choices = listOf(
                    OpenAIChoiceDto(
                        index = 0,
                        message = OpenAIMessageDto(
                            role = "assistant",
                            content = "Hello! How can I help you?"
                        ),
                        finishReason = "stop"
                    )
                ),
                usage = OpenAIUsageDto(
                    promptTokens = 10,
                    completionTokens = 15,
                    totalTokens = 25
                )
            )

            whenever(mockOpenAIApi.createChatCompletion(any(), any()))
                .thenReturn(Response.success(openAIResponse))

            then("should save user message and return AI response") {
                runTest {
                    val result = repository.sendMessage(userMessage)
                    
                    result.shouldBeInstanceOf<Result.Success<ChatMessage>>()
                    val aiMessage = result.getOrNull()!!
                    aiMessage.content shouldBe "Hello! How can I help you?"
                    aiMessage.role shouldBe MessageRole.ASSISTANT
                    
                    verify(mockChatMessageDao).insertMessage(any())
                }
            }
        }

        `when`("API returns 401 unauthorized") {
            val userMessage = ChatMessage(
                id = "test-id", 
                content = "Test",
                role = MessageRole.USER
            )

            whenever(mockOpenAIApi.createChatCompletion(any(), any()))
                .thenReturn(Response.error(401, mock()))

            then("should return API key invalid error") {
                runTest {
                    val result = repository.sendMessage(userMessage)
                    
                    result.shouldBeInstanceOf<Result.Error>()
                    result.exceptionOrNull().shouldBeInstanceOf<ChatError.ApiKeyInvalid>()
                }
            }
        }

        `when`("API returns 429 rate limit") {
            val userMessage = ChatMessage(
                id = "test-id",
                content = "Test", 
                role = MessageRole.USER
            )

            whenever(mockOpenAIApi.createChatCompletion(any(), any()))
                .thenReturn(Response.error(429, mock()))

            then("should return rate limit error") {
                runTest {
                    val result = repository.sendMessage(userMessage)
                    
                    result.shouldBeInstanceOf<Result.Error>()
                    result.exceptionOrNull().shouldBeInstanceOf<ChatError.RateLimitExceeded>()
                }
            }
        }

        `when`("clearing message history") {
            then("should call dao clear method") {
                runTest {
                    val result = repository.clearHistory()
                    
                    result.shouldBeInstanceOf<Result.Success<Unit>>()
                    verify(mockChatMessageDao).clearAllMessages()
                }
            }
        }

        `when`("deleting a specific message") {
            val messageId = "test-message-id"

            then("should call dao delete method") {
                runTest {
                    val result = repository.deleteMessage(messageId)
                    
                    result.shouldBeInstanceOf<Result.Success<Unit>>()
                    verify(mockChatMessageDao).deleteMessage(messageId)
                }
            }
        }
    }
})
