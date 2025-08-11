package com.example.day1_ai_chat_nextgen.domain.usecase

import app.cash.turbine.test
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole
import com.example.day1_ai_chat_nextgen.domain.model.Result
import com.example.day1_ai_chat_nextgen.domain.repository.ChatRepository
import io.kotest.assertions.throwables.shouldThrow
import io.kotest.core.spec.style.BehaviorSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.types.shouldBeInstanceOf
import kotlinx.coroutines.test.runTest
import org.mockito.kotlin.any
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever

class SendMessageUseCaseTest : BehaviorSpec({

    given("SendMessageUseCase") {
        val mockRepository = mock<ChatRepository>()
        val useCase = SendMessageUseCase(mockRepository)

        `when`("sending a valid message") {
            val messageContent = "Hello, AI!"
            val expectedMessage = ChatMessage(
                id = "test-id",
                content = messageContent,
                role = MessageRole.ASSISTANT
            )
            
            whenever(mockRepository.sendMessage(any<ChatMessage>())).thenReturn(Result.Success(expectedMessage))

            then("should emit loading then success") {
                runTest {
                    useCase(messageContent).test {
                        val loadingResult = awaitItem()
                        loadingResult.shouldBeInstanceOf<Result.Loading>()

                        val successResult = awaitItem()
                        successResult.shouldBeInstanceOf<Result.Success<ChatMessage>>()
                        successResult.getOrNull()?.content shouldBe expectedMessage.content

                        awaitComplete()
                    }
                }
            }
        }

        `when`("sending an empty message") {
            then("should emit error") {
                runTest {
                    useCase("").test {
                        val errorResult = awaitItem()
                        errorResult.shouldBeInstanceOf<Result.Error>()
                        errorResult.exceptionOrNull()?.shouldBeInstanceOf<IllegalArgumentException>()

                        awaitComplete()
                    }
                }
            }
        }

        `when`("sending a blank message") {
            then("should emit error") {
                runTest {
                    useCase("   ").test {
                        val errorResult = awaitItem()
                        errorResult.shouldBeInstanceOf<Result.Error>()

                        awaitComplete()
                    }
                }
            }
        }

        `when`("repository returns error") {
            val error = RuntimeException("Network error")
            whenever(mockRepository.sendMessage(any<ChatMessage>())).thenReturn(Result.Error(error))

            then("should emit loading then error") {
                runTest {
                    useCase("Test message").test {
                        val loadingResult = awaitItem()
                        loadingResult.shouldBeInstanceOf<Result.Loading>()

                        val errorResult = awaitItem()
                        errorResult.shouldBeInstanceOf<Result.Error>()
                        errorResult.exceptionOrNull() shouldBe error

                        awaitComplete()
                    }
                }
            }
        }
    }
})
