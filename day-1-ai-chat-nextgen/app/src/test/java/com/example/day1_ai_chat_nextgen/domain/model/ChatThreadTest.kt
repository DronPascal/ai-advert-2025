package com.example.day1_ai_chat_nextgen.domain.model

import io.kotest.core.spec.style.BehaviorSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.shouldNotBe

class ChatThreadTest : BehaviorSpec({

    given("ChatThread") {
        `when`("creating thread with factory method") {
            val thread = ChatThread.create(
                threadId = "thread_openai_123",
                assistantId = "asst_456",
                formatId = "format_789",
                title = "Test Chat"
            )

            then("should have correct properties") {
                thread.threadId shouldBe "thread_openai_123"
                thread.assistantId shouldBe "asst_456"
                thread.activeFormatId shouldBe "format_789"
                thread.title shouldBe "Test Chat"
                thread.messageCount shouldBe 0
                thread.isActive shouldBe true
                thread.id shouldNotBe ""
            }
        }

        `when`("creating thread without format") {
            val thread = ChatThread.create(
                threadId = "thread_openai_456",
                assistantId = "asst_789"
            )

            then("should have default values") {
                thread.threadId shouldBe "thread_openai_456"
                thread.assistantId shouldBe "asst_789"
                thread.activeFormatId shouldBe null
                thread.title shouldBe "New Chat"
                thread.messageCount shouldBe 0
                thread.isActive shouldBe true
            }
        }

        `when`("updating thread activity") {
            val originalTime = System.currentTimeMillis() - 1000
            val thread = ChatThread(
                id = "thread_1",
                threadId = "thread_openai_1",
                assistantId = "asst_1",
                activeFormatId = null,
                lastMessageAt = originalTime,
                messageCount = 5
            )

            val updatedThread = thread.withUpdatedActivity()

            then("should increment message count and update timestamp") {
                updatedThread.messageCount shouldBe 6
                updatedThread.lastMessageAt shouldNotBe originalTime
                updatedThread.lastMessageAt shouldBe thread.lastMessageAt // Since we're using current time
                // Other properties should remain the same
                updatedThread.id shouldBe thread.id
                updatedThread.threadId shouldBe thread.threadId
                updatedThread.assistantId shouldBe thread.assistantId
            }
        }

        `when`("updating thread format") {
            val thread = ChatThread(
                id = "thread_1",
                threadId = "thread_openai_1",
                assistantId = "asst_1",
                activeFormatId = "old_format"
            )

            val updatedThread = thread.withFormat("new_format")

            then("should update format ID") {
                updatedThread.activeFormatId shouldBe "new_format"
                // Other properties should remain the same
                updatedThread.id shouldBe thread.id
                updatedThread.threadId shouldBe thread.threadId
                updatedThread.assistantId shouldBe thread.assistantId
                updatedThread.messageCount shouldBe thread.messageCount
            }
        }

        `when`("removing format from thread") {
            val thread = ChatThread(
                id = "thread_1",
                threadId = "thread_openai_1",
                assistantId = "asst_1",
                activeFormatId = "some_format"
            )

            val updatedThread = thread.withFormat(null)

            then("should remove format ID") {
                updatedThread.activeFormatId shouldBe null
                // Other properties should remain the same
                updatedThread.id shouldBe thread.id
                updatedThread.threadId shouldBe thread.threadId
                updatedThread.assistantId shouldBe thread.assistantId
            }
        }

        `when`("updating thread title") {
            val thread = ChatThread(
                id = "thread_1",
                threadId = "thread_openai_1",
                assistantId = "asst_1",
                activeFormatId = null,
                title = "Old Title"
            )

            val updatedThread = thread.withTitle("New Amazing Title")

            then("should update title") {
                updatedThread.title shouldBe "New Amazing Title"
                // Other properties should remain the same
                updatedThread.id shouldBe thread.id
                updatedThread.threadId shouldBe thread.threadId
                updatedThread.assistantId shouldBe thread.assistantId
                updatedThread.activeFormatId shouldBe thread.activeFormatId
            }
        }

        `when`("creating thread with all parameters") {
            val thread = ChatThread(
                id = "custom_id",
                threadId = "thread_openai_custom",
                assistantId = "asst_custom",
                activeFormatId = "format_custom",
                title = "Custom Thread",
                createdAt = 12345L,
                lastMessageAt = 67890L,
                messageCount = 10,
                isActive = false
            )

            then("should preserve all properties") {
                thread.id shouldBe "custom_id"
                thread.threadId shouldBe "thread_openai_custom"
                thread.assistantId shouldBe "asst_custom"
                thread.activeFormatId shouldBe "format_custom"
                thread.title shouldBe "Custom Thread"
                thread.createdAt shouldBe 12345L
                thread.lastMessageAt shouldBe 67890L
                thread.messageCount shouldBe 10
                thread.isActive shouldBe false
            }
        }
    }
})
