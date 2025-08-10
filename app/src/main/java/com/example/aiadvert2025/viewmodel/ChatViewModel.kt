package com.example.aiadvert2025.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aiadvert2025.data.ChatMessage
import com.example.aiadvert2025.network.RetrofitClient
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ChatViewModel : ViewModel() {
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val api = RetrofitClient.apiService

    // Predefined AI responses for demo
    private val aiResponses = listOf(
        "Это очень интересный вопрос! Расскажите больше.",
        "Понимаю вас. Что вы об этом думаете?",
        "Это действительно важная тема. Хотите обсудить детали?",
        "Интересная точка зрения! А как вы к этому пришли?",
        "Спасибо за вопрос. Это заставляет задуматься.",
        "Хороший вопрос! Я думаю, это зависит от контекста.",
        "Согласен с вами. Это действительно важно учитывать.",
        "Понятно! А что вас больше всего интересует в этой теме?",
        "Отличная мысль! Можете привести пример?",
        "Я вижу вашу точку зрения. Это очень логично."
    )

    init {
        // Add welcome message
        _messages.value = listOf(
            ChatMessage(
                text = "Привет! Я AI-ассистент. Как дела? О чём хотите поговорить?",
                isFromUser = false
            )
        )
    }

    fun sendMessage(text: String) {
        // Add user message
        val userMessage = ChatMessage(text = text, isFromUser = true)
        _messages.value = _messages.value + userMessage

        // Get AI response
        getAIResponse(text)
    }

    private fun getAIResponse(userMessage: String) {
        viewModelScope.launch {
            _isLoading.value = true

            try {
                // Simulate network delay
                delay(1000L + (500L..2000L).random())

                // Try to get data from API to demonstrate network connectivity
                val randomId = (1..100).random()
                val response = api.getPost(randomId)

                val aiResponse = if (response.isSuccessful) {
                    // Use post title/body for more dynamic responses
                    val post = response.body()
                    generateContextualResponse(userMessage, post?.title)
                } else {
                    // Fallback to predefined responses
                    generateSimpleResponse(userMessage)
                }

                val aiMessage = ChatMessage(
                    text = aiResponse,
                    isFromUser = false
                )
                _messages.value = _messages.value + aiMessage

            } catch (e: Exception) {
                e.printStackTrace()
                handleApiError()
            } finally {
                _isLoading.value = false
            }
        }
    }

    private fun generateContextualResponse(userMessage: String, apiTitle: String?): String {
        return when {
            userMessage.contains("привет", ignoreCase = true) ||
            userMessage.contains("здравствуй", ignoreCase = true) ->
                "Привет! Очень рад общению с вами. Как настроение?"

            userMessage.contains("как дела", ignoreCase = true) ||
            userMessage.contains("как поживаешь", ignoreCase = true) ->
                "У меня всё отлично, спасибо за вопрос! А как у вас дела?"

            userMessage.contains("что", ignoreCase = true) &&
            userMessage.contains("умеешь", ignoreCase = true) ->
                "Я могу поддержать беседу на разные темы, ответить на вопросы и просто пообщаться. О чём хотите поговорить?"

            userMessage.contains("спасибо", ignoreCase = true) ->
                "Пожалуйста! Всегда рад помочь."

            userMessage.contains("пока", ignoreCase = true) ||
            userMessage.contains("до свидания", ignoreCase = true) ->
                "До свидания! Было приятно пообщаться с вами."

            apiTitle != null ->
                "Интересно! Кстати, недавно читал про \"${apiTitle.take(30)}${if (apiTitle.length > 30) "..." else ""}\". ${aiResponses.random()}"

            else -> aiResponses.random()
        }
    }

    private fun generateSimpleResponse(userMessage: String): String {
        return when {
            userMessage.contains("?") -> "Хороший вопрос! " + aiResponses.random()
            userMessage.length > 50 -> "Вы подняли важную тему. " + aiResponses.random()
            else -> aiResponses.random()
        }
    }

    private fun handleApiError() {
        val errorMessage = ChatMessage(
            text = "Извините, произошла ошибка при подключении к серверу. Но я всё равно готов с вами пообщаться!",
            isFromUser = false
        )
        _messages.value = _messages.value + errorMessage
    }
}
