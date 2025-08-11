package com.example.day1_ai_chat_nextgen.presentation.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Stable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.day1_ai_chat_nextgen.domain.model.ChatMessage
import com.example.day1_ai_chat_nextgen.domain.model.MessageRole

@Stable
data class MessageBubbleColors(
    val userBackground: Color,
    val assistantBackground: Color,
    val textColor: Color
)

@Composable
fun MessageBubble(
    message: ChatMessage,
    modifier: Modifier = Modifier,
    colors: MessageBubbleColors = MessageBubbleDefaults.colors()
) {
    when (message.role) {
        MessageRole.SYSTEM -> {
            // Parse system message to extract icon and display proper divider
            val (icon, text) = parseSystemMessage(message.content)
            SystemMessageDivider(
                message = text,
                icon = icon,
                modifier = modifier
            )
        }
        else -> {
            Row(
                modifier = modifier.fillMaxWidth(),
                horizontalArrangement = when (message.role) {
                    MessageRole.USER -> Arrangement.End
                    MessageRole.ASSISTANT -> Arrangement.Start
                    MessageRole.SYSTEM -> Arrangement.Center
                }
            ) {
                Card(
                    modifier = Modifier
                        .widthIn(max = 280.dp)
                        .clip(
                            RoundedCornerShape(
                                topStart = 16.dp,
                                topEnd = 16.dp,
                                bottomStart = if (message.role == MessageRole.USER) 16.dp else 4.dp,
                                bottomEnd = if (message.role == MessageRole.USER) 4.dp else 16.dp
                            )
                        ),
                    colors = CardDefaults.cardColors(
                        containerColor = when (message.role) {
                            MessageRole.USER -> colors.userBackground
                            MessageRole.ASSISTANT -> colors.assistantBackground
                            MessageRole.SYSTEM -> colors.assistantBackground
                        }
                    ),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
                ) {
                    Text(
                        text = message.content,
                        modifier = Modifier.padding(12.dp),
                        color = colors.textColor,
                        fontSize = 16.sp,
                        fontWeight = if (message.role == MessageRole.SYSTEM) FontWeight.Medium else FontWeight.Normal,
                        lineHeight = 20.sp
                    )
                }
            }
        }
    }
}

private fun parseSystemMessage(content: String): Pair<String, String> {
    return when {
        content.contains("Формат ответов обновлен", ignoreCase = true) ||
        content.contains("формат", ignoreCase = true) -> "🔄" to content
        content.contains("Новая беседа", ignoreCase = true) ||
        content.contains("новый тред", ignoreCase = true) ||
        content.contains("new thread", ignoreCase = true) -> "✨" to content
        content.contains("Беседа очищена", ignoreCase = true) ||
        content.contains("История очищена", ignoreCase = true) -> "🗑️" to content
        else -> "ℹ️" to content
    }
}

object MessageBubbleDefaults {
    @Composable
    fun colors(): MessageBubbleColors = MessageBubbleColors(
        userBackground = Color(0xFF6366F1),
        assistantBackground = Color(0xFF1A1A2E),
        textColor = Color.White
    )
}
