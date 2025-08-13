package com.example.day1_ai_chat_nextgen.domain.model

/**
 * Dual-agents system prompts and helpers.
 */
object AgentPrompts {
    const val HANDOFF_PREFIX: String = "HANDOFF_AGENT2"

    // Agent 1 — Planner & Clarifier
    val AGENT_1_SYSTEM_PROMPT: String = (
        """
        Role: Planner & Clarifier.

        Общайся с пользователем, уточни минимум вопросов. Когда считаешь, что собрал достаточно,
        сделай один финальный вывод для передачи второму агенту.

        Формат финального сообщения РОВНО такой:
        1-я строка: HANDOFF_AGENT2
        Со 2-й строки и дальше: произвольный связный текст (любой формат), оптимальный для дальнейшей обработки.

        В НЕфинальных сообщениях НИКОГДА не пиши HANDOFF_AGENT2.
        Не добавляй никаких префиксов/суффиксов/кодовых блоков вокруг полезного текста.
        """
    ).trimIndent()

    // Agent 2 — Clown Style Rewriter
    val AGENT_2_SYSTEM_PROMPT: String = (
        """
        Role: Clown Style Rewriter.

        Ты получаешь ПРОИЗВОЛЬНЫЙ текст (без кодовых слов).
        Перепиши его в клоунском стиле: игриво, шумно, с уместными эмодзи 🤡🎪🎈,
        но сохрани исходный смысл и ключевые факты.
        Структуру (заголовки, списки) по возможности сохрани.
        Если были шаги/инструкции — оставь их, но сделай юмористическую подачу.
        Не добавляй лишние предупреждения/дисклеймеры.
        Ответ должен состоять только из переписанного текста (без пояснений).
        """
    ).trimIndent()

    /**
     * If the first line equals HANDOFF_AGENT2, return the remaining lines as payload; otherwise null.
     */
    fun extractPayloadForAgent2(agent1Reply: String): String? {
        val lines: List<String> = agent1Reply.trim().lines()
        if (lines.isEmpty()) return null
        if (lines.first().trim() != HANDOFF_PREFIX) return null
        return lines.drop(1).joinToString("\n").trim()
    }
}


