package com.example.aiadvert2025

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.aiadvert2025.ui.theme.AIAdvert2025Theme
import kotlin.math.PI
import kotlin.math.sin
import kotlin.math.cos

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AIAdvert2025Theme {
                GradientWelcomeScreen()
            }
        }
    }
}

@Composable
fun GradientWelcomeScreen() {
    // Анимации для плавающих блобов
    val infiniteTransition = rememberInfiniteTransition(label = "blobs")

    val blob1X by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(20000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob1X"
    )

    val blob1Y by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(25000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob1Y"
    )

    val blob2X by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 0f,
        animationSpec = infiniteRepeatable(
            animation = tween(18000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob2X"
    )

    val blob2Y by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(22000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob2Y"
    )

    val blob3Scale by infiniteTransition.animateFloat(
        initialValue = 0.8f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(15000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "blob3Scale"
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0F0F23)),
        contentAlignment = Alignment.Center
    ) {
        // Плавающие цветные блобы как в современных приложениях

        // Первый блоб - большой фиолетовый
        Box(
            modifier = Modifier
                .size(400.dp)
                .offset(
                    x = (blob1X * 200).dp - 100.dp,
                    y = (blob1Y * 300).dp - 150.dp
                )
                .background(
                    brush = Brush.radialGradient(
                        colors = listOf(
                            Color(0xFF2D1B69).copy(alpha = 0.3f),
                            Color.Transparent
                        ),
                        radius = 400f
                    )
                )
        )

        // Второй блоб - средний синий
        Box(
            modifier = Modifier
                .size(300.dp)
                .offset(
                    x = (blob2X * 250).dp + 50.dp,
                    y = (blob2Y * 200).dp + 100.dp
                )
                .background(
                    brush = Brush.radialGradient(
                        colors = listOf(
                            Color(0xFF1A1A2E).copy(alpha = 0.4f),
                            Color.Transparent
                        ),
                        radius = 300f
                    )
                )
        )

        // Третий блоб - маленький с изменяющимся размером
        Box(
            modifier = Modifier
                .size((200 * blob3Scale).dp)
                .offset(
                    x = (-blob1X * 150).dp + 200.dp,
                    y = (-blob2Y * 250).dp + 50.dp
                )
                .background(
                    brush = Brush.radialGradient(
                        colors = listOf(
                            Color(0xFF4C1D95).copy(alpha = 0.25f),
                            Color.Transparent
                        ),
                        radius = 200f * blob3Scale
                    )
                )
        )
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
                        // Основной заголовок со статичным градиентом
            Text(
                text = "AI Advert",
                fontSize = 56.sp,
                fontWeight = FontWeight.ExtraBold,
                textAlign = TextAlign.Center,
                style = MaterialTheme.typography.displayLarge.copy(
                    brush = Brush.linearGradient(
                        colors = listOf(
                            Color(0xFF6366F1), // Indigo
                            Color(0xFF8B5CF6), // Violet
                            Color(0xFFEC4899), // Pink
                            Color(0xFFF59E0B)  // Amber
                        )
                    )
                ),
                modifier = Modifier.padding(horizontal = 32.dp)
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Подзаголовок
            Text(
                text = "2025",
                fontSize = 32.sp,
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center,
                color = Color.White.copy(alpha = 0.9f),
                modifier = Modifier.padding(horizontal = 32.dp)
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Описание с мягкой анимированной прозрачностью
            Text(
                text = "Будущее уже здесь",
                fontSize = 20.sp,
                fontWeight = FontWeight.Medium,
                textAlign = TextAlign.Center,
                color = Color.White.copy(
                    alpha = 0.8f + 0.2f * sin(blob1X * PI).toFloat()
                ),
                lineHeight = 28.sp,
                modifier = Modifier.padding(horizontal = 48.dp)
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
fun GradientWelcomeScreenPreview() {
    AIAdvert2025Theme {
        GradientWelcomeScreen()
    }
}

