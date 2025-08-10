package com.example.aiadvert2025.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aiadvert2025.BuildConfig
import com.example.aiadvert2025.api.OpenAIChatRequest
import com.example.aiadvert2025.api.OpenAIMessage
import com.example.aiadvert2025.data.ChatMessage
import com.example.aiadvert2025.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ChatViewModel : ViewModel() {
    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val openAIApi = RetrofitClient.openAIApi

    init {
        // Add welcome message from OpenAI
        _messages.value = listOf(
            ChatMessage(
                text = "Привет! Я AI-ассистент ChatGPT. Как дела? О чём хотите поговорить?",
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
                val aiResponse = getOpenAIResponse(userMessage)

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

    private suspend fun getOpenAIResponse(userMessage: String): String {
        try {
            // Проверяем API ключ
            val apiKey = BuildConfig.OPENAI_API_KEY
            if (apiKey.isEmpty() || apiKey == "YOUR_OPENAI_API_KEY_HERE") {
                return "API ключ не настроен корректно"
            }

            // Создаем контекст разговора
            val conversationHistory = buildConversationHistory()
            val messages = conversationHistory + OpenAIMessage("user", userMessage)

            val request = OpenAIChatRequest(
                model = "gpt-3.5-turbo",
                messages = messages,
                max_tokens = 150,
                temperature = 0.7
            )

            val response = openAIApi.createChatCompletion(
                authorization = "Bearer ${BuildConfig.OPENAI_API_KEY}",
                request = request
            )

            if (response.isSuccessful && response.body()?.choices?.isNotEmpty() == true) {
                val choice = response.body()!!.choices.first()
                val message = choice.message

                // Проверяем на отказ модели отвечать
                if (message.refusal != null) {
                    return "Модель отказалась отвечать: ${message.refusal}"
                }

                return message.content.takeIf { it.isNotBlank() }
                    ?: "Получен пустой ответ от OpenAI"
            } else {
                val errorBody = response.errorBody()?.string()
                return "OpenAI API ошибка ${response.code()}: $errorBody"
            }
        } catch (e: Exception) {
            return "Ошибка подключения к OpenAI: ${e.message}"
        }
    }

    private fun buildConversationHistory(): List<OpenAIMessage> {
        // Берем последние 6 сообщений для контекста (3 пары вопрос-ответ)
        val recentMessages = _messages.value.takeLast(6)
        val openAIMessages = mutableListOf<OpenAIMessage>()

        // Добавляем системное сообщение
        openAIMessages.add(
            OpenAIMessage(
                role = "system",
                content = "Ты дружелюбный AI-ассистент. Отвечай на русском языке кратко и по существу."
            )
        )

        // Конвертируем историю чата в формат OpenAI
        for (message in recentMessages) {
            if (message.isFromUser) {
                openAIMessages.add(OpenAIMessage("user", message.text))
            } else {
                openAIMessages.add(OpenAIMessage("assistant", message.text))
            }
        }

        return openAIMessages
    }


    private fun handleApiError() {
        val errorMessage = ChatMessage(
            text = "Извините, произошла ошибка при подключении к OpenAI. Проверьте API ключ и интернет соединение.",
            isFromUser = false
        )
        _messages.value = _messages.value + errorMessage
    }
}
