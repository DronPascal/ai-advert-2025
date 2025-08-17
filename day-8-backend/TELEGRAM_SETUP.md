# 📱 Настройка Telegram Бота

## 🤖 Создание Бота через @BotFather

### Шаг 1: Создайте бота
1. Откройте Telegram и найдите **@BotFather**
2. Отправьте команду `/start`
3. Отправьте команду `/newbot`
4. Введите имя для вашего бота (например, "AI Insights Daily")
5. Введите username для бота (должен заканчиваться на "bot", например "ai_insights_daily_bot")

### Шаг 2: Получите токен
После создания бота @BotFather пришлет вам сообщение с токеном:
```
Use this token to access the HTTP API:
1234567890:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGHI
```

### Шаг 3: Найдите свой User ID
1. Начните чат с вашим новым ботом
2. Отправьте любое сообщение (например, `/start`)
3. Откройте ссылку: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Найдите ваш `chat_id` в ответе JSON

## 🔧 Настройка Environment Variables

### Создайте .env файл:
```bash
# В папке day-8-backend создайте файл .env
cp env.example .env
```

### Заполните реальные данные:
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your_real_openai_key_here
OPENAI_MODEL=gpt-4

# Telegram Integration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyzABCdefGHI
TELEGRAM_USER_ID=7789201703

# Scheduling
SCHEDULE_HOUR=22
SCHEDULE_MINUTE=0
```

## 🧪 Тестирование

### Тест 1: Проверка бота
```bash
cd day-8-backend
export TELEGRAM_BOT_TOKEN="your_real_token_here"
export TELEGRAM_USER_ID="your_user_id"
python3 test_telegram.py
```

Ожидаемый результат:
```
🤖 Bot information:
  Name: AI Insights Daily
  Username: @ai_insights_daily_bot
  ID: 1234567890
✅ Test message sent successfully!
📱 Check your Telegram app for the test message
```

### Тест 2: Полное приложение
```bash
# Для MCP версии
python3 app/main.py

# Для простой версии
python3 app/main_simple.py
```

## 🚨 Устранение Неполадок

### Проблема: "401 Unauthorized"
- ❌ Неправильный токен бота
- ✅ Проверьте токен в @BotFather
- ✅ Убедитесь что нет пробелов в токене

### Проблема: "403 Forbidden" 
- ❌ Бот заблокирован пользователем
- ❌ Неправильный User ID
- ✅ Начните чат с ботом и отправьте `/start`
- ✅ Проверьте User ID через getUpdates

### Проблема: Сообщения не доходят
- ❌ Demo режим включен (`TELEGRAM_BOT_TOKEN="demo_token"`)
- ✅ Установите реальный токен бота
- ✅ Проверьте что бот не заблокирован

### Проблема: "Chat not found"
- ❌ Неправильный User ID
- ❌ Пользователь не начинал чат с ботом
- ✅ Отправьте `/start` боту первым делом

## 📋 Чек-лист для Деплоя

- [ ] ✅ Бот создан через @BotFather
- [ ] ✅ Токен получен и сохранен в .env
- [ ] ✅ User ID определен и сохранен
- [ ] ✅ Тест `test_telegram.py` проходит успешно
- [ ] ✅ Получено тестовое сообщение в Telegram
- [ ] ✅ Основное приложение отправляет сообщения
- [ ] ✅ Планировщик настроен на нужное время

## 🎯 Финальная Проверка

После настройки вы должны получать:
- ✅ Тестовое сообщение от `test_telegram.py`
- ✅ AI Insights сообщения от основного приложения
- ✅ Ежедневные сообщения в 22:00 по расписанию

## 🔒 Безопасность

- 🚫 Никогда не публикуйте токен бота в GitHub
- ✅ Добавьте `.env` в `.gitignore`
- ✅ Используйте environment variables в продакшене
- ✅ Регулярно ротируйте токены через @BotFather
