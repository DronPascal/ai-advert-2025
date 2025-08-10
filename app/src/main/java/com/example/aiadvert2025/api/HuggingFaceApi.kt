package com.example.aiadvert2025.api

import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Path

// Using JSONPlaceholder for demo (public free API)
data class Post(
    val userId: Int,
    val id: Int,
    val title: String,
    val body: String
)

interface ApiService {
    @GET("posts/{id}")
    suspend fun getPost(@Path("id") id: Int): Response<Post>
}
