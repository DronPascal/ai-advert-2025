package com.example.aiadvert2025.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.aiadvert2025.BuildConfig
import com.example.aiadvert2025.api.OpenAIChatRequest
import com.example.aiadvert2025.api.OpenAIMessage
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

    private val fallbackApi = RetrofitClient.apiService
    private val openAIApi = RetrofitClient.openAIApi
    
    // Проверяем, есть ли API ключ OpenAI
    private val hasOpenAIKey = BuildConfig.OPENAI_API_KEY.isNotEmpty() && 
                              BuildConfig.OPENAI_API_KEY != "YOUR_OPENAI_API_KEY_HERE"

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
        val welcomeText = if (hasOpenAIKey) {
            "Привет! Я AI-ассистент на базе OpenAI. Как дела? О чём хотите поговорить?"
        } else {
            "Привет! Я работаю в демо-режиме. Добавьте OpenAI API ключ в local.properties для полной функциональности!"
        }
        
        _messages.value = listOf(
            ChatMessage(
                text = welcomeText,
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
                val aiResponse = if (hasOpenAIKey) {
                    // Используем OpenAI API
                    getOpenAIResponse(userMessage)
                } else {
                    // Используем демо-режим
                    getDemoResponse(userMessage)
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
    
    private suspend fun getOpenAIResponse(userMessage: String): String {
        try {
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
                return response.body()!!.choices.first().message.content
            } else {
                return "Извините, OpenAI API недоступен. Попробуйте позже."
            }
        } catch (e: Exception) {
            return "Ошибка подключения к OpenAI: ${e.message}"
        }
    }
    
    private suspend fun getDemoResponse(userMessage: String): String {
        // Simulate network delay
        delay(1000L + (500L..2000L).random())
        
        // Try to get data from fallback API to demonstrate network connectivity
        return try {
            val randomId = (1..100).random()
            val response = fallbackApi.getPost(randomId)
            
            if (response.isSuccessful) {
                val post = response.body()
                generateContextualResponse(userMessage, post?.title)
            } else {
                generateSimpleResponse(userMessage)
            }
        } catch (e: Exception) {
            generateSimpleResponse(userMessage)
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
        val errorText = if (hasOpenAIKey) {
            "Извините, произошла ошибка при подключении к OpenAI. Попробуйте позже."
        } else {
            "Извините, произошла ошибка при подключении к серверу. Но я всё равно готов с вами пообщаться!"
        }
        
        val errorMessage = ChatMessage(
            text = errorText,
            isFromUser = false
        )
        _messages.value = _messages.value + errorMessage
    }
}
