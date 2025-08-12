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
                Всегда следуй формату ответа, который пользователь зафиксирует в этом треде.
                Если формат ещё не задан — попроси сформулировать его явным текстом.
                При изменении формата последним сообщением — используй новую версию.
                Отвечай на русском языке, если не указано иное.
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
