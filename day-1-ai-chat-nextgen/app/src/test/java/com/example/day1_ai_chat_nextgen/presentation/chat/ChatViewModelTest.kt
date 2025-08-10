package com.example.day1_ai_chat_nextgen.presentation.chat

import app.cash.turbine.test
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole
import com.example.day1_ai_chat_nextgen.domain.model.Result
import com.example.day1_ai_chat_nextgen.domain.usecase.GetMessagesUseCase
import com.example.day1_ai_chat_nextgen.domain.usecase.SendMessageUseCase
import io.kotest.core.spec.style.BehaviorSpec
import io.kotest.matchers.shouldBe
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.mockito.kotlin.any
import org.mockito.kotlin.mock
import org.mockito.kotlin.whenever

@OptIn(ExperimentalCoroutinesApi::class)
class ChatViewModelTest : BehaviorSpec({

    val testDispatcher = StandardTestDispatcher()

    beforeTest {
        Dispatchers.setMain(testDispatcher)
    }

    afterTest {
        Dispatchers.resetMain()
    }

    given("ChatViewModel") {
        val mockGetMessagesUseCase = mock<GetMessagesUseCase>()
        val mockSendMessageUseCase = mock<SendMessageUseCase>()

        val initialMessages = listOf(
            ChatMessage(
                id = "1",
                content = "Hello",
                role = MessageRole.USER
            )
        )

        whenever(mockGetMessagesUseCase()).thenReturn(flowOf(initialMessages))

        `when`("initialized") {
            val viewModel = ChatViewModel(mockGetMessagesUseCase, mockSendMessageUseCase)

            then("should load initial messages") {
                runTest {
                    viewModel.uiState.test {
                        val state = awaitItem()
                        state.messages shouldBe initialMessages
                        state.isLoading shouldBe false
                    }
                }
            }
        }

        `when`("message input changes") {
            val viewModel = ChatViewModel(mockGetMessagesUseCase, mockSendMessageUseCase)
            val newMessage = "Test message"

            then("should update message input in state") {
                runTest {
                    viewModel.onEvent(ChatUiEvent.MessageInputChanged(newMessage))
                    
                    viewModel.uiState.test {
                        val state = awaitItem()
                        state.messageInput shouldBe newMessage
                    }
                }
            }
        }

        `when`("sending a message successfully") {
            val viewModel = ChatViewModel(mockGetMessagesUseCase, mockSendMessageUseCase)
            val testMessage = "Test message"
            val responseMessage = ChatMessage(
                id = "2",
                content = "AI Response",
                role = MessageRole.ASSISTANT
            )

            whenever(mockSendMessageUseCase(any())).thenReturn(
                flowOf(
                    Result.Loading,
                    Result.Success(responseMessage)
                )
            )

            then("should clear input and show loading state") {
                runTest {
                    // Set initial message
                    viewModel.onEvent(ChatUiEvent.MessageInputChanged(testMessage))
                    
                    viewModel.uiState.test {
                        val initialState = awaitItem()
                        initialState.messageInput shouldBe testMessage
                        
                        viewModel.onEvent(ChatUiEvent.SendMessage)
                        
                        val loadingState = awaitItem()
                        loadingState.messageInput shouldBe ""
                        loadingState.isSendingMessage shouldBe true
                        
                        val successState = awaitItem()
                        successState.isSendingMessage shouldBe false
                        successState.error shouldBe null
                    }
                }
            }
        }

        `when`("send message fails") {
            val viewModel = ChatViewModel(mockGetMessagesUseCase, mockSendMessageUseCase)
            val testMessage = "Test message"
            val errorMessage = "Network error"

            whenever(mockSendMessageUseCase(any())).thenReturn(
                flowOf(
                    Result.Loading,
                    Result.Error(RuntimeException(errorMessage))
                )
            )

            then("should show error state") {
                runTest {
                    viewModel.onEvent(ChatUiEvent.MessageInputChanged(testMessage))
                    
                    viewModel.uiState.test {
                        awaitItem() // Initial state
                        
                        viewModel.onEvent(ChatUiEvent.SendMessage)
                        
                        awaitItem() // Loading state
                        
                        val errorState = awaitItem()
                        errorState.isSendingMessage shouldBe false
                        errorState.error shouldBe errorMessage
                    }
                }
            }
        }

        `when`("dismissing error") {
            val viewModel = ChatViewModel(mockGetMessagesUseCase, mockSendMessageUseCase)

            then("should clear error from state") {
                runTest {
                    viewModel.onEvent(ChatUiEvent.DismissError)
                    
                    viewModel.uiState.test {
                        val state = awaitItem()
                        state.error shouldBe null
                    }
                }
            }
        }
    }
})
