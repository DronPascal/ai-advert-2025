# AIAdvert2025 - AI Chat Application

Android приложение с интеграцией OpenAI API для чата с AI-ассистентом.

![demo](https://github.com/user-attachments/assets/10f8bea6-7f7a-42d0-82a0-0790e2b6fd8d)

## 🚀 Возможности

- **Красивый экран приветствия** с анимированными градиентами
- **AI Чат с OpenAI** - интеграция с GPT-3.5-turbo
- **Демо-режим** - работает без API ключа с имитацией ответов
- **Современный UI** - Material 3, тёмная тема
- **Контекст разговора** - AI помнит предыдущие сообщения
- **Безопасность** - API ключи не попадают в репозиторий

## 🛠 Настройка

### 1. Клонирование проекта
```bash
git clone <repository_url>
cd AIAdvert2025
```

### 2. Настройка OpenAI API (необязательно)

Для полной функциональности получите API ключ от OpenAI:

1. Перейдите на [platform.openai.com](https://platform.openai.com/api-keys)
2. Создайте новый API ключ
3. Откройте файл `local.properties` (уже создан)
4. Замените `YOUR_OPENAI_API_KEY_HERE` на ваш настоящий ключ:

```properties
openai_api_key=sk-proj-your-actual-key-here
```

### 3. Сборка и запуск

```bash
./gradlew build
./gradlew installDebug
```

## 🔧 Архитектура

- **UI Layer**: Jetpack Compose
- **Business Logic**: ViewModel + StateFlow  
- **Network**: Retrofit + OkHttp
- **API**: OpenAI GPT-3.5-turbo + JSONPlaceholder (fallback)

## 📱 Использование

1. Запустите приложение
2. На главном экране нажмите "💬 Открыть AI Чат"
3. Начните общение с AI-ассистентом
4. AI автоматически определит режим работы:
   - **С API ключом**: настоящий ChatGPT
   - **Без ключа**: умные демо-ответы

## 🔒 Безопасность

- `local.properties` находится в `.gitignore`
- API ключи не попадают в репозиторий
- Ключи доступны только через BuildConfig

## 🎨 Технологии

- **Kotlin** - основной язык
- **Jetpack Compose** - UI framework
- **Material 3** - дизайн система
- **Retrofit** - HTTP клиент
- **OpenAI API** - AI интеграция
- **StateFlow** - reactive programming
