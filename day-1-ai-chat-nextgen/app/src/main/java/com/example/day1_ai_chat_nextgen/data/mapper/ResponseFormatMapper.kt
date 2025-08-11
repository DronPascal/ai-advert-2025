package com.example.day1_ai_chat_nextgen.data.mapper

import com.example.day1_ai_chat_nextgen.data.local.entity.ResponseFormatEntity
import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat

fun ResponseFormat.toEntity(): ResponseFormatEntity {
    return ResponseFormatEntity(
        id = id,
        name = name,
        description = description,
        instructions = instructions,
        timestamp = timestamp,
        isActive = isActive,
        isCustom = isCustom
    )
}

fun ResponseFormatEntity.toDomain(): ResponseFormat {
    return ResponseFormat(
        id = id,
        name = name,
        description = description,
        instructions = instructions,
        timestamp = timestamp,
        isActive = isActive,
        isCustom = isCustom
    )
}
