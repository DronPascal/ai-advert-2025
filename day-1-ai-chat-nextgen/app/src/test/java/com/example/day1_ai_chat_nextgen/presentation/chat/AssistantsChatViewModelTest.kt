package com.example.day1_ai_chat_nextgen.presentation.chat

import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.ChatThread
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole
import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat
import com.example.day1_ai_chat_nextgen.domain.model.Result
import com.example.day1_ai_chat_nextgen.domain.repository.ChatRepository
import io.kotest.core.spec.style.BehaviorSpec
import io.kotest.matchers.shouldBe
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.mockito.kotlin.mock
import org.mockito.kotlin.verify
import org.mockito.kotlin.whenever

class AssistantsChatViewModelTest : BehaviorSpec({

    given("AssistantsChatViewModel") {
        val testDispatcher = StandardTestDispatcher()
        Dispatchers.setMain(testDispatcher)

        val mockRepository = mock<ChatRepository>()

        // Default successful responses for initialization
        whenever(mockRepository.initializePredefinedFormats()).thenReturn(Result.Success(Unit))
        whenever(mockRepository.getOrCreateAssistant()).thenReturn(Result.Success("asst_12345"))
        whenever(mockRepository.getCurrentThread()).thenReturn(Result.Success(null))
        whenever(mockRepository.getPredefinedFormats()).thenReturn(Result.Success(emptyList()))
        whenever(mockRepository.getMessages()).thenReturn(flowOf(emptyList()))
        whenever(mockRepository.getAllThreads()).thenReturn(flowOf(emptyList()))
        whenever(mockRepository.getAllFormats()).thenReturn(flowOf(emptyList()))

        `when`("initializing with existing thread") {
            val existingThread = ChatThread(
                id = "thread_1",
                threadId = "thread_openai_1",
                assistantId = "asst_12345",
                activeFormatId = "format_1",
                title = "Existing Chat"
            )

            whenever(mockRepository.getCurrentThread()).thenReturn(Result.Success(existingThread))

            then("should set current thread and start observing data") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.currentThread shouldBe existingThread
                    viewModel.uiState.value.isInitializing shouldBe false
                    viewModel.uiState.value.needsFormatSelection shouldBe false

                    verify(mockRepository).initializePredefinedFormats()
                    verify(mockRepository).getOrCreateAssistant()
                    verify(mockRepository).getCurrentThread()
                }
            }
        }

        `when`("initializing without existing thread") {
            whenever(mockRepository.getCurrentThread()).thenReturn(Result.Success(null))
            val predefinedFormats = ResponseFormat.PREDEFINED_FORMATS
            whenever(mockRepository.getPredefinedFormats()).thenReturn(
                Result.Success(
                    predefinedFormats
                )
            )

            then("should show format selection") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.currentThread shouldBe null
                    viewModel.uiState.value.needsFormatSelection shouldBe true
                    viewModel.uiState.value.isInitializing shouldBe false
                    viewModel.uiState.value.availableFormats shouldBe predefinedFormats
                }
            }
        }

        `when`("sending message successfully") {
            val existingThread = ChatThread(
                id = "thread_1",
                threadId = "thread_openai_1",
                assistantId = "asst_12345",
                activeFormatId = null
            )

            val assistantMessage = ChatMessage(
                id = "msg_1",
                content = "Hello! How can I help you?",
                role = MessageRole.ASSISTANT
            )

            whenever(mockRepository.getCurrentThread()).thenReturn(Result.Success(existingThread))
            whenever(mockRepository.sendMessage("Hello")).thenReturn(Result.Success(assistantMessage))

            then("should send message and clear input") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    // Set message input
                    viewModel.onEvent(ChatUiEvent.MessageInputChanged("Hello"))
                    viewModel.uiState.value.messageInput shouldBe "Hello"

                    // Send message
                    viewModel.onEvent(ChatUiEvent.SendMessage)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.messageInput shouldBe ""
                    viewModel.uiState.value.isSendingMessage shouldBe false
                    viewModel.uiState.value.error shouldBe null

                    verify(mockRepository).sendMessage("Hello")
                }
            }
        }

        `when`("selecting predefined format") {
            val format = ResponseFormat(
                id = "format_json",
                name = "JSON Format",
                description = "Structured responses",
                instructions = "Always respond in JSON",
                isCustom = false
            )

            val newThread = ChatThread(
                id = "thread_new",
                threadId = "thread_openai_new",
                assistantId = "asst_12345",
                activeFormatId = "format_json"
            )

            whenever(mockRepository.setResponseFormat(format)).thenReturn(Result.Success(format))
            whenever(mockRepository.createNewThread("format_json")).thenReturn(
                Result.Success(
                    newThread
                )
            )

            then("should set format and create new thread") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.onEvent(ChatUiEvent.SelectPredefinedFormat(format))
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.currentThread shouldBe newThread
                    viewModel.uiState.value.needsFormatSelection shouldBe false
                    viewModel.uiState.value.isSettingFormat shouldBe false

                    verify(mockRepository).setResponseFormat(format)
                    verify(mockRepository).createNewThread("format_json")
                }
            }
        }

        `when`("setting custom format") {
            val customInstructions = "Respond as a pirate would"
            val customFormat = ResponseFormat.createCustomFormat(customInstructions)
            val newThread = ChatThread(
                id = "thread_custom",
                threadId = "thread_openai_custom",
                assistantId = "asst_12345",
                activeFormatId = customFormat.id
            )

            whenever(mockRepository.setResponseFormat(customInstructions)).thenReturn(
                Result.Success(
                    customFormat
                )
            )
            whenever(mockRepository.createNewThread(customFormat.id)).thenReturn(
                Result.Success(
                    newThread
                )
            )

            then("should create custom format and new thread") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.onEvent(ChatUiEvent.SetCustomFormat(customInstructions))
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.currentThread shouldBe newThread
                    viewModel.uiState.value.needsFormatSelection shouldBe false
                    viewModel.uiState.value.isSettingFormat shouldBe false

                    verify(mockRepository).setResponseFormat(customInstructions)
                    verify(mockRepository).createNewThread(customFormat.id)
                }
            }
        }

        `when`("creating new thread") {
            val newThread = ChatThread(
                id = "thread_new2",
                threadId = "thread_openai_new2",
                assistantId = "asst_12345",
                activeFormatId = null
            )

            whenever(mockRepository.createNewThread(null)).thenReturn(Result.Success(newThread))

            then("should create new thread without format") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.onEvent(ChatUiEvent.CreateNewThread)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.currentThread shouldBe newThread
                    viewModel.uiState.value.isCreatingThread shouldBe false
                    viewModel.uiState.value.showThreadDialog shouldBe false

                    verify(mockRepository).createNewThread(null)
                }
            }
        }

        `when`("switching to different thread") {
            val targetThread = ChatThread(
                id = "thread_target",
                threadId = "thread_openai_target",
                assistantId = "asst_12345",
                activeFormatId = "format_1",
                title = "Target Thread"
            )

            whenever(mockRepository.switchToThread("thread_target")).thenReturn(
                Result.Success(
                    targetThread
                )
            )

            then("should switch to target thread") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.onEvent(ChatUiEvent.SwitchToThread("thread_target"))
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.currentThread shouldBe targetThread
                    viewModel.uiState.value.showThreadDialog shouldBe false

                    verify(mockRepository).switchToThread("thread_target")
                }
            }
        }

        `when`("clearing history") {
            whenever(mockRepository.clearHistory()).thenReturn(Result.Success(Unit))
            val predefinedFormats = ResponseFormat.PREDEFINED_FORMATS
            whenever(mockRepository.getPredefinedFormats()).thenReturn(
                Result.Success(
                    predefinedFormats
                )
            )

            then("should clear history and show format selection") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.onEvent(ChatUiEvent.ClearMessages)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.currentThread shouldBe null
                    viewModel.uiState.value.needsFormatSelection shouldBe true
                    viewModel.uiState.value.error shouldBe null

                    verify(mockRepository).clearHistory()
                }
            }
        }

        `when`("skipping format selection") {
            val simpleThread = ChatThread(
                id = "thread_simple",
                threadId = "thread_openai_simple",
                assistantId = "asst_12345",
                activeFormatId = null
            )

            whenever(mockRepository.createNewThread()).thenReturn(Result.Success(simpleThread))

            then("should create thread without format") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.onEvent(ChatUiEvent.SkipFormatSelection)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.currentThread shouldBe simpleThread
                    viewModel.uiState.value.needsFormatSelection shouldBe false
                    viewModel.uiState.value.isCreatingThread shouldBe false

                    verify(mockRepository).createNewThread()
                }
            }
        }

        `when`("showing and hiding format dialog") {
            then("should toggle dialog state") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    // Show dialog
                    viewModel.onEvent(ChatUiEvent.ShowFormatDialog)
                    viewModel.uiState.value.showFormatDialog shouldBe true

                    // Hide dialog
                    viewModel.onEvent(ChatUiEvent.HideFormatDialog)
                    viewModel.uiState.value.showFormatDialog shouldBe false
                    viewModel.uiState.value.formatInput shouldBe ""
                }
            }
        }

        `when`("handling format input changes") {
            then("should update format input state") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.onEvent(ChatUiEvent.FormatInputChanged("Custom format instructions"))
                    viewModel.uiState.value.formatInput shouldBe "Custom format instructions"
                }
            }
        }

        `when`("repository returns error during initialization") {
            whenever(mockRepository.getOrCreateAssistant()).thenReturn(Result.Error(com.example.day1_ai_chat_nextgen.domain.model.ChatError.ApiKeyMissing))

            then("should show error and stop initialization") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    viewModel.uiState.value.error shouldBe "OpenAI API key is not configured."
                    viewModel.uiState.value.isInitializing shouldBe false
                }
            }
        }

        `when`("dismissing error") {
            then("should clear error state") {
                runTest {
                    val viewModel = AssistantsChatViewModel(mockRepository)
                    testDispatcher.scheduler.advanceUntilIdle()

                    // Set an error first
                    viewModel.uiState.value.copy(error = "Test error")

                    viewModel.onEvent(ChatUiEvent.DismissError)
                    viewModel.uiState.value.error shouldBe null
                }
            }
        }
    }
})
