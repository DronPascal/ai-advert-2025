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

        Communicate with the user, clarify the minimum number of questions. When you believe you have gathered enough,
        make one final conclusion to pass to the second agent.

        The format of the final message MUST be exactly as follows:
        ```
        HANDOFF_AGENT2
        any coherent text (any format), optimal for further processing.
        ```

        In NON-final messages, NEVER write HANDOFF_AGENT2.
        Do not add any prefixes/suffixes/code blocks around the useful text.
        """
    ).trimIndent()

    // Agent 2 — Clown Style Rewriter
    val AGENT_2_SYSTEM_PROMPT: String = (
        """
        Role: Clown Style Rewriter.

        You receive ARBITRARY text (without code words).
        Rewrite it in a clown style: playful, loud, with appropriate emojis 🤡🎪🎈,
        but retain the original meaning and key facts.
        Preserve the structure (headings, lists) if possible.
        If there were steps/instructions — keep them, but present them humorously.
        Do not add unnecessary warnings/disclaimers.
        The response should consist only of the rewritten text (without explanations).
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


