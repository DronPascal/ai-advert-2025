package com.example.day1_ai_chat_nextgen.di

import com.example.day1_ai_chat_nextgen.data.repository.ChatRepositoryImpl
import com.example.day1_ai_chat_nextgen.domain.repository.ChatRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindChatRepository(
        chatRepositoryImpl: ChatRepositoryImpl
    ): ChatRepository
}
