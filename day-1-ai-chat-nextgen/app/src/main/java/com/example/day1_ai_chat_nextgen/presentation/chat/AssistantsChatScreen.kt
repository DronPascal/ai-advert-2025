package com.example.day1_ai_chat_nextgen.presentation.chat

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.example.day1_ai_chat_nextgen.presentation.components.FormatIndicator
import com.example.day1_ai_chat_nextgen.presentation.components.FormatSelectionDialog
import com.example.day1_ai_chat_nextgen.presentation.components.LoadingIndicator
import com.example.day1_ai_chat_nextgen.presentation.components.MessageBubble
import com.example.day1_ai_chat_nextgen.presentation.components.MessageInput

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AssistantsChatScreen(
    modifier: Modifier = Modifier,
    viewModel: AssistantsChatViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    val listState = rememberLazyListState()
    var showOptionsMenu by remember { mutableStateOf(false) }

    // Auto-scroll to bottom when new messages arrive
    LaunchedEffect(uiState.messages.size) {
        if (uiState.messages.isNotEmpty()) {
            listState.animateScrollToItem(uiState.messages.size - 1)
        }
    }

    // Show error snackbar
    LaunchedEffect(uiState.error) {
        uiState.error?.let { error ->
            snackbarHostState.showSnackbar(error)
            viewModel.onEvent(ChatUiEvent.DismissError)
        }
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "AI Chat",
                            fontWeight = FontWeight.Bold
                        )
                        uiState.currentThread?.let { thread ->
                            Text(
                                text = thread.title,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.7f)
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                ),
                actions = {
                    IconButton(onClick = { showOptionsMenu = true }) {
                        Icon(
                            imageVector = Icons.Default.MoreVert,
                            contentDescription = "Options",
                            tint = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                    
                    DropdownMenu(
                        expanded = showOptionsMenu,
                        onDismissRequest = { showOptionsMenu = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("New Thread") },
                            onClick = {
                                showOptionsMenu = false
                                viewModel.onEvent(ChatUiEvent.CreateNewThread)
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Change Format") },
                            onClick = {
                                showOptionsMenu = false
                                viewModel.onEvent(ChatUiEvent.ShowFormatDialog)
                            }
                        )
                        DropdownMenuItem(
                            text = { Text("Clear History") },
                            onClick = {
                                showOptionsMenu = false
                                viewModel.onEvent(ChatUiEvent.ClearMessages)
                            }
                        )
                    }
                }
            )
        },
        snackbarHost = { SnackbarHost(snackbarHostState) }
    ) { paddingValues ->
        
        when {
            uiState.isInitializing -> {
                InitializingScreen()
            }
            
            uiState.needsFormatSelection -> {
                FormatSelectionScreen(
                    uiState = uiState,
                    onEvent = viewModel::onEvent,
                    modifier = Modifier.padding(paddingValues)
                )
            }
            
            else -> {
                ChatContent(
                    uiState = uiState,
                    onEvent = viewModel::onEvent,
                    listState = listState,
                    modifier = Modifier.padding(paddingValues)
                )
            }
        }
        
        // Dialogs
        if (uiState.showFormatDialog) {
            FormatSelectionDialog(
                availableFormats = uiState.availableFormats,
                formatInput = uiState.formatInput,
                isSettingFormat = uiState.isSettingFormat,
                onFormatInputChanged = { viewModel.onEvent(ChatUiEvent.FormatInputChanged(it)) },
                onSelectPredefinedFormat = { viewModel.onEvent(ChatUiEvent.SelectPredefinedFormat(it)) },
                onSetCustomFormat = { viewModel.onEvent(ChatUiEvent.SetCustomFormat(it)) },
                onSkipSelection = { viewModel.onEvent(ChatUiEvent.SkipFormatSelection) },
                onDismiss = { viewModel.onEvent(ChatUiEvent.HideFormatDialog) }
            )
        }
    }
}

@Composable
private fun InitializingScreen() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            CircularProgressIndicator()
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Инициализация AI ассистента...",
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center
            )
        }
    }
}

@Composable
private fun FormatSelectionScreen(
    uiState: ChatUiState,
    onEvent: (ChatUiEvent) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Добро пожаловать!",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = "Выберите формат, в котором AI будет давать ответы",
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        FormatSelectionDialog(
            availableFormats = uiState.availableFormats,
            formatInput = uiState.formatInput,
            isSettingFormat = uiState.isSettingFormat,
            onFormatInputChanged = { onEvent(ChatUiEvent.FormatInputChanged(it)) },
            onSelectPredefinedFormat = { onEvent(ChatUiEvent.SelectPredefinedFormat(it)) },
            onSetCustomFormat = { onEvent(ChatUiEvent.SetCustomFormat(it)) },
            onSkipSelection = { onEvent(ChatUiEvent.SkipFormatSelection) },
            onDismiss = { onEvent(ChatUiEvent.SkipFormatSelection) }
        )
    }
}

@Composable
private fun ChatContent(
    uiState: ChatUiState,
    onEvent: (ChatUiEvent) -> Unit,
    listState: androidx.compose.foundation.lazy.LazyListState,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxSize()
    ) {
        // Format indicator
        if (uiState.activeFormat != null) {
            FormatIndicator(
                activeFormat = uiState.activeFormat,
                onFormatSettingsClick = { onEvent(ChatUiEvent.ShowFormatDialog) },
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )
        }
        
        // Messages list
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            state = listState,
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            if (uiState.messages.isEmpty() && !uiState.isLoading) {
                item {
                    Box(
                        modifier = Modifier.fillMaxWidth(),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Начните диалог с AI!",
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(32.dp)
                        )
                    }
                }
            }
            
            items(uiState.messages) { message ->
                MessageBubble(
                    message = message
                )
            }
            
            if (uiState.isSendingMessage) {
                item {
                    LoadingIndicator(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp)
                    )
                }
            }
        }
        
        // Message input
        MessageInput(
            value = uiState.messageInput,
            onValueChange = { onEvent(ChatUiEvent.MessageInputChanged(it)) },
            onSendClick = { onEvent(ChatUiEvent.SendMessage) },
            enabled = uiState.canSendMessage,
            modifier = Modifier
                .fillMaxWidth()
                .background(MaterialTheme.colorScheme.surface)
                .padding(16.dp)
        )
    }
}
