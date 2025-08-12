package com.example.day1_ai_chat_nextgen.domain.model

import io.kotest.core.spec.style.BehaviorSpec
import io.kotest.matchers.shouldBe
import io.kotest.matchers.shouldNotBe

class ResponseFormatTest : BehaviorSpec({

    given("ResponseFormat") {
        `when`("creating custom format") {
            val instructions = "Respond as a pirate would speak"
            val customFormat = ResponseFormat.createCustomFormat(instructions)

            then("should have correct properties") {
                customFormat.name shouldBe "Custom Format"
                customFormat.description shouldBe "User-defined response format"
                customFormat.instructions shouldBe instructions
                customFormat.isCustom shouldBe true
                customFormat.isActive shouldBe false
                customFormat.id shouldNotBe ""
            }
        }

        `when`("getting default system instructions") {
            val instructions = ResponseFormat.getDefaultSystemInstructions()

            then("should contain clarification workflow in English") {
                instructions shouldBe """
                    You are a smart and attentive AI assistant. Your task is to gather all necessary information from the user before providing a final answer. If the user's request is incomplete or unclear, first clarify the missing details. Identify the most critical gaps and ask up to five focused, domain-specific questions at once (only those that truly matter to solving the task). Avoid generic or repetitive questions; when helpful, offer concise options (e.g., A/B/C) to make answering easier. Continue until everything needed to solve the task is clear. When you have gathered enough information, confirm with the user that all relevant details have been provided (for example: "Is there anything else I should know before I answer?" or "Did I understand everything correctly?"). If the user confirms that this is all, proceed to produce the final answer. Do not ask unnecessary questions and do not repeat information you already have. Stop clarifying as soon as the request is clear, and deliver a thorough and precise answer using all the details you have learned.
                """.trimIndent()
            }
        }

        `when`("accessing predefined formats") {
            val predefinedFormats = ResponseFormat.PREDEFINED_FORMATS

            then("should have expected number of formats") {
                predefinedFormats.size shouldBe 4
            }

            then("should contain structured list format") {
                val structuredList = predefinedFormats.find { it.id == "structured_list" }
                structuredList shouldNotBe null
                structuredList!!.name shouldBe "Структурированный список"
                structuredList.isCustom shouldBe false
                structuredList.instructions.contains("Короткий заголовок") shouldBe true
            }

            then("should contain JSON format") {
                val jsonFormat = predefinedFormats.find { it.id == "json_data" }
                jsonFormat shouldNotBe null
                jsonFormat!!.name shouldBe "JSON формат"
                jsonFormat.isCustom shouldBe false
                jsonFormat.instructions.contains("JSON объект") shouldBe true
            }

            then("should contain XML format") {
                val xmlFormat = predefinedFormats.find { it.id == "xml_structure" }
                xmlFormat shouldNotBe null
                xmlFormat!!.name shouldBe "XML структура"
                xmlFormat.isCustom shouldBe false
                xmlFormat.instructions.contains("XML документ") shouldBe true
            }

            then("should contain Markdown format") {
                val markdownFormat = predefinedFormats.find { it.id == "markdown_report" }
                markdownFormat shouldNotBe null
                markdownFormat!!.name shouldBe "Markdown отчёт"
                markdownFormat.isCustom shouldBe false
                markdownFormat.instructions.contains("Markdown") shouldBe true
            }
        }

        `when`("creating format with all parameters") {
            val format = ResponseFormat(
                id = "test_format",
                name = "Test Format",
                description = "Test description",
                instructions = "Test instructions",
                timestamp = 12345L,
                isActive = true,
                isCustom = false
            )

            then("should preserve all properties") {
                format.id shouldBe "test_format"
                format.name shouldBe "Test Format"
                format.description shouldBe "Test description"
                format.instructions shouldBe "Test instructions"
                format.timestamp shouldBe 12345L
                format.isActive shouldBe true
                format.isCustom shouldBe false
            }
        }
    }
})
