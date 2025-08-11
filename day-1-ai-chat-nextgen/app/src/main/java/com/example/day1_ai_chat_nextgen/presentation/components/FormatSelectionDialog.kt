package com.example.day1_ai_chat_nextgen.presentation.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.example.day1_ai_chat_nextgen.domain.model.ResponseFormat

@Composable
fun FormatSelectionDialog(
    availableFormats: List<ResponseFormat>,
    formatInput: String,
    isSettingFormat: Boolean,
    onFormatInputChanged: (String) -> Unit,
    onSelectPredefinedFormat: (ResponseFormat) -> Unit,
    onSetCustomFormat: (String) -> Unit,
    onSkipSelection: () -> Unit,
    onDismiss: () -> Unit,
    modifier: Modifier = Modifier
) {
    var selectedTab by remember { mutableStateOf(0) }
    val tabs = listOf("Готовые форматы", "Свой формат")

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(
            dismissOnBackPress = true,
            dismissOnClickOutside = true
        )
    ) {
        Surface(
            modifier = modifier.padding(16.dp),
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surface
        ) {
            Column(
                modifier = Modifier.padding(24.dp)
            ) {
                Text(
                    text = "Выберите формат ответов",
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold
                )
                
                Text(
                    text = "AI будет отвечать в выбранном формате",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                TabRow(selectedTabIndex = selectedTab) {
                    tabs.forEachIndexed { index, title ->
                        Tab(
                            selected = selectedTab == index,
                            onClick = { selectedTab = index },
                            text = { Text(title) }
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                when (selectedTab) {
                    0 -> PredefinedFormatsTab(
                        formats = availableFormats.filter { !it.isCustom },
                        onSelectFormat = onSelectPredefinedFormat,
                        isLoading = isSettingFormat
                    )
                    1 -> CustomFormatTab(
                        formatInput = formatInput,
                        onFormatInputChanged = onFormatInputChanged,
                        onSetFormat = onSetCustomFormat,
                        isLoading = isSettingFormat
                    )
                }
                
                Spacer(modifier = Modifier.height(24.dp))
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    TextButton(
                        onClick = onSkipSelection,
                        enabled = !isSettingFormat
                    ) {
                        Text("Пропустить")
                    }
                    
                    Spacer(modifier = Modifier.weight(1f))
                    
                    OutlinedButton(
                        onClick = onDismiss,
                        enabled = !isSettingFormat
                    ) {
                        Text("Отмена")
                    }
                }
            }
        }
    }
}

@Composable
private fun PredefinedFormatsTab(
    formats: List<ResponseFormat>,
    onSelectFormat: (ResponseFormat) -> Unit,
    isLoading: Boolean
) {
    LazyColumn(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(formats) { format ->
            FormatCard(
                format = format,
                onClick = { if (!isLoading) onSelectFormat(format) },
                enabled = !isLoading
            )
        }
    }
}

@Composable
private fun CustomFormatTab(
    formatInput: String,
    onFormatInputChanged: (String) -> Unit,
    onSetFormat: (String) -> Unit,
    isLoading: Boolean
) {
    Column {
        Text(
            text = "Опишите желаемый формат ответов:",
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Medium
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        OutlinedTextField(
            value = formatInput,
            onValueChange = onFormatInputChanged,
            modifier = Modifier
                .fillMaxWidth()
                .height(120.dp),
            placeholder = {
                Text("Например: Отвечай в формате JSON с полями title, description, status")
            },
            enabled = !isLoading
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Button(
            onClick = { onSetFormat(formatInput) },
            modifier = Modifier.fillMaxWidth(),
            enabled = formatInput.isNotBlank() && !isLoading
        ) {
            Text(if (isLoading) "Устанавливаю..." else "Установить формат")
        }
    }
}

@Composable
private fun FormatCard(
    format: ResponseFormat,
    onClick: () -> Unit,
    enabled: Boolean,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        onClick = onClick,
        colors = CardDefaults.cardColors(
            containerColor = if (enabled) 
                MaterialTheme.colorScheme.surfaceVariant 
            else 
                MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
        ),
        enabled = enabled
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = format.name,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            Spacer(modifier = Modifier.height(4.dp))
            
            Text(
                text = format.description,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = format.instructions,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
