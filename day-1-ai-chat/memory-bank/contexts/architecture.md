# Architecture Context

Layers and key files:
- UI (Compose): `app/src/main/java/com/example/aiadvert2025/MainActivity.kt`, `ChatActivity.kt`, theme files under `ui/theme/`.
- State/Logic: `viewmodel/ChatViewModel.kt`.
- Models: `data/ChatMessage.kt`.
- Network: `api/OpenAIApi.kt`, `network/RetrofitClient.kt`.

Patterns:
- MVVM + StateFlow for state management.
- Material 3 for design system.
- Retrofit for network calls.

Future additions:
- Repository for chat persistence (e.g., Room/DataStore) behind an interface.
- MVI-style reducers in `ChatViewModel` if state/events grow.



