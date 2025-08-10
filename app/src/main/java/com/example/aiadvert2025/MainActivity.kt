package com.example.aiadvert2025

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
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

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { AIAdvert2025Theme { GradientWelcomeScreen() } }
    }
}

@Composable
fun AnimatedBlob(
    size: Float,
    color: Color,
    alpha: Float,
    offsetX: Float,
    offsetY: Float,
    scale: Float = 1f
) {
    Box(
        modifier =
            Modifier
                .size((size * scale).dp)
                .offset(x = offsetX.dp, y = offsetY.dp)
                .background(
                    brush =
                        Brush.radialGradient(
                            colors =
                                listOf(
                                    color.copy(alpha = alpha),
                                    Color.Transparent
                                ),
                            radius = size * scale
                        )
                )
    )
}

@Composable
private fun rememberBlobAnimation(
    from: Float,
    to: Float,
    duration: Int,
    label: String
) = rememberInfiniteTransition(label = "blobs").animateFloat(
    from, to,
    infiniteRepeatable(tween(duration, easing = FastOutSlowInEasing), RepeatMode.Reverse),
    label
)

@Composable
fun GradientWelcomeScreen() {
    // Создаем анимации
    val blob1X by rememberBlobAnimation(0f, 1f, 10000, "blob1X")
    val blob1Y by rememberBlobAnimation(1f, 0f, 12000, "blob1Y")
    val blob2X by rememberBlobAnimation(0f, 0f, 9000, "blob2X")
    val blob2Y by rememberBlobAnimation(1f, 0f, 11000, "blob2Y")
    val blob3Scale by rememberBlobAnimation(0.8f, 1.2f, 7000, "blob3Scale")

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF0F0F23)),
        contentAlignment = Alignment.Center
    ) {
        // Плавающие блобы
        AnimatedBlob(
            size = 400f,
            color = Color(0xFF4C1D95),
            alpha = 0.6f,
            offsetX = blob1X * 100,
            offsetY = blob1Y * 100
        )

        AnimatedBlob(
            size = 300f,
            color = Color(0xFF313173),
            alpha = 0.4f,
            offsetX = blob2X * 120 - 120,
            offsetY = blob2Y * 120 - 60
        )

        AnimatedBlob(
            size = 250f,
            color = Color(0xDF541979),
            alpha = 0.35f,
            offsetX = blob1X * 80 - 40,
            offsetY = -blob2Y * 80 + 40,
            scale = blob3Scale
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
                style =
                    MaterialTheme.typography.displayLarge.copy(
                        brush = Brush.linearGradient(
                            colors = listOf(
                                Color(0xFF6366F1), // Indigo
                                Color(0xFF8B5CF6), // Violet
                                Color(0xFFEC4899), // Pink
                                Color(0xFFF59E0B) // Amber
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
                color = Color.White.copy(alpha = 0.6f + 0.4f * sin(blob1X * 2 * PI).toFloat()),
                lineHeight = 28.sp,
                modifier = Modifier.padding(horizontal = 48.dp)
            )
        }
    }
}

@Preview(showBackground = true)
@Composable
fun GradientWelcomeScreenPreview() {
    AIAdvert2025Theme { GradientWelcomeScreen() }
}
