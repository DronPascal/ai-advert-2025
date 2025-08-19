package com.example.day1_ai_chat_nextgen.domain.model

import androidx.compose.runtime.Immutable
import kotlinx.serialization.Serializable
import java.util.UUID

@Immutable
@Serializable
data class ResponseFormat(
    val id: String = UUID.randomUUID().toString(),
    val name: String,
    val description: String,
    val instructions: String,
    val timestamp: Long = System.currentTimeMillis(),
    val isActive: Boolean = false,
    val isCustom: Boolean = true
) {
    companion object {
        fun createCustomFormat(instructions: String): ResponseFormat {
            return ResponseFormat(
                name = "Custom Format",
                description = "User-defined response format",
                instructions = instructions,
                isCustom = true
            )
        }

        fun getDefaultSystemInstructions(): String {
            return """
                You are a smart and attentive AI assistant. Your task is to gather all necessary information from the user before providing a final answer. If the user's request is incomplete or unclear, first clarify the missing details. Identify the most critical gaps and ask up to five focused, domain-specific questions at once (only those that truly matter to solving the task). Avoid generic or repetitive questions; when helpful, offer concise options (e.g., A/B/C) to make answering easier. Continue until everything needed to solve the task is clear. When you have gathered enough information, confirm with the user that all relevant details have been provided (for example: "Is there anything else I should know before I answer?" or "Did I understand everything correctly?"). If the user confirms that this is all, proceed to produce the final answer. Do not ask unnecessary questions and do not repeat information you already have. Stop clarifying as soon as the request is clear, and deliver a thorough and precise answer using all the details you have learned.
            """.trimIndent()
        }

        val PREDEFINED_FORMATS = listOf(
            ResponseFormat(
                id = "structured_list",
                name = "Структурированный список",
                description = "Ответ в виде заголовка + 3 пункта + заключение",
                instructions = """
                    ФОРМАТ ОТВЕТА:
                    — Короткий заголовок
                    — Список из 3 пунктов
                    — Итоговая строка: OK/NO
                """.trimIndent(),
                isCustom = false
            ),
            ResponseFormat(
                id = "json_data",
                name = "JSON формат",
                description = "Ответ в виде валидного JSON объекта",
                instructions = """
                    ФОРМАТ ОТВЕТА: JSON объект с полями:
                    {
                        "title": "краткий заголовок",
                        "data": ["пункт 1", "пункт 2", "пункт 3"],
                        "status": "OK/NO",
                        "timestamp": "текущее время"
                    }
                """.trimIndent(),
                isCustom = false
            ),
            ResponseFormat(
                id = "xml_structure",
                name = "XML структура",
                description = "Ответ в виде XML документа",
                instructions = """
                    ФОРМАТ ОТВЕТА: XML документ:
                    <response>
                        <title>заголовок</title>
                        <content>
                            <item>пункт 1</item>
                            <item>пункт 2</item>
                            <item>пункт 3</item>
                        </content>
                        <status>OK/NO</status>
                    </response>
                """.trimIndent(),
                isCustom = false
            ),
            ResponseFormat(
                id = "markdown_report",
                name = "Markdown отчёт",
                description = "Ответ в виде структурированного Markdown",
                instructions = """
                    ФОРМАТ ОТВЕТА в Markdown:
                    # Заголовок
                    
                    ## Основная информация
                    - Пункт 1
                    - Пункт 2
                    - Пункт 3
                    
                    ## Заключение
                    **Статус:** OK/NO
                """.trimIndent(),
                isCustom = false
            )
        )
    }
}
