package com.example.day1_ai_chat_nextgen.di

import com.example.day1_ai_chat_nextgen.BuildConfig
import com.example.day1_ai_chat_nextgen.data.remote.api.McpBridgeApi
import com.example.day1_ai_chat_nextgen.data.remote.api.OpenAIAssistantsApi
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Named
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    private const val NETWORK_TIMEOUT_SECONDS = 30L

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
        encodeDefaults = true
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient {
        val timeoutSeconds = NETWORK_TIMEOUT_SECONDS
        val builder = OkHttpClient.Builder()
            .connectTimeout(timeoutSeconds, TimeUnit.SECONDS)
            .readTimeout(timeoutSeconds, TimeUnit.SECONDS)
            .writeTimeout(timeoutSeconds, TimeUnit.SECONDS)

        // Add API key interceptor for all requests
        val apiKeyInterceptor = Interceptor { chain ->
            val originalRequest = chain.request()
            val newRequest = originalRequest.newBuilder()
                .addHeader("Authorization", "Bearer ${BuildConfig.OPENAI_API_KEY}")
                .addHeader("Content-Type", "application/json")
                .build()
            chain.proceed(newRequest)
        }
        builder.addInterceptor(apiKeyInterceptor)

        // Only add logging interceptor in debug builds for security
        if (BuildConfig.IS_DEBUG_BUILD) {
            val loggingInterceptor = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BASIC // Avoid logging sensitive data
            }
            builder.addInterceptor(loggingInterceptor)
        }

        return builder.build()
    }

    @Provides
    @Singleton
    @Named("openai")
    fun provideOpenAiRetrofit(
        okHttpClient: OkHttpClient,
        json: Json
    ): Retrofit {
        return Retrofit.Builder()
            .baseUrl("https://api.openai.com/")
            .client(okHttpClient)
            .addConverterFactory(
                json.asConverterFactory("application/json".toMediaType())
            )
            .build()
    }

    @Provides
    @Singleton
    fun provideOpenAIAssistantsApi(@Named("openai") retrofit: Retrofit): OpenAIAssistantsApi {
        return retrofit.create(OpenAIAssistantsApi::class.java)
    }

    @Provides
    @Singleton
    @Named("mcp")
    fun provideMcpBridgeRetrofit(json: Json): Retrofit {
        val baseUrl = if (BuildConfig.IS_DEBUG_BUILD && BuildConfig.MCP_BRIDGE_URL.isNotBlank()) {
            BuildConfig.MCP_BRIDGE_URL
        } else {
            // Fallback to localhost for non-emulator runs
            "http://localhost:8765/"
        }

        // Separate client without auth header injection
        val httpClient = OkHttpClient.Builder()
            .connectTimeout(NETWORK_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .readTimeout(NETWORK_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .writeTimeout(NETWORK_TIMEOUT_SECONDS, TimeUnit.SECONDS)
            .apply {
                if (BuildConfig.IS_DEBUG_BUILD) {
                    val logging = HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC }
                    addInterceptor(logging)
                }
            }
            .build()

        return Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(httpClient)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
    }

    @Provides
    @Singleton
    fun provideMcpBridgeApi(@Named("mcp") mcpRetrofit: Retrofit): McpBridgeApi {
        return mcpRetrofit.create(McpBridgeApi::class.java)
    }
}
