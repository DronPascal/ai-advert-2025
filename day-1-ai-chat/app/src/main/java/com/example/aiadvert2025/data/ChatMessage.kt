package com.example.aiadvert2025.data

data class ChatMessage(
    val text: String,
    val isFromUser: Boolean,
    val timestamp: Long = System.currentTimeMillis(),
    val isWelcomeMessage: Boolean = false
)
