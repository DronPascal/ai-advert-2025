# Crypto Daily Digest Service

Ежедневный сервис для отправки крипто-сводок через Telegram с использованием OpenAI Responses API и remote MCP серверов.

## Архитектура

Сервис использует **OpenAI Responses API** для оркестрации **remote MCP серверов** + **прямую интеграцию с Telegram**:
- **web3-research-mcp**: Получение рыночных данных и анализ токенов (remote MCP)
- **crypto-whitepapers-mcp**: Поиск и анализ whitepaper'ов (remote MCP)
- **Direct Telegram Bot API**: Отправка сообщений напрямую через Bot API

Модель GPT-4/5 самостоятельно вызывает 2 remote MCP сервера для получения данных, формирует сводку, а Python сервис отправляет результат в Telegram.

## Предварительные требования

### 1. OpenAI API ключ
Получите API ключ от OpenAI с доступом к Responses API.

### 2. Remote MCP серверы в HTTPS режиме
Необходимо развернуть 2 MCP сервера как HTTPS endpoints, доступные из OpenAI cloud:

#### Web3 Research MCP
```bash
# Развернуть как HTTPS сервис (VPS/cloud)
git clone https://github.com/aaronjmars/web3-research-mcp
# + HTTP wrapper + HTTPS reverse proxy
# Результат: https://your-web3-mcp-server.com
```

#### Crypto Whitepapers MCP  
```bash
# Развернуть как HTTPS сервис (VPS/cloud)
git clone https://github.com/kukapay/crypto-whitepapers-mcp
# + HTTP wrapper + HTTPS reverse proxy  
# Результат: https://your-whitepapers-mcp-server.com
```

#### ✅ Telegram Integration
Используется **прямая интеграция** через Telegram Bot API:
- Никаких дополнительных серверов не требуется
- Только Bot Token + User ID в переменных окружения

### 3. Публичные HTTPS URL для Remote MCP
Только 2 MCP сервера должны быть доступны из интернета для OpenAI Responses API:
- Используйте VPS + nginx reverse proxy с HTTPS
- Или облачный хостинг (Vercel, Railway и т.д.)
- **Telegram**: не требует публичных URL, работает через прямой Bot API

## 🚀 Demo Mode: tiktoken + GitMCP Integration

Для быстрого тестирования доступен demo режим с интеграцией двух MCP серверов:

### Демо архитектура
```
OpenAI Responses API
    ↓
tiktoken MCP (https://gitmcp.io/openai/tiktoken) → Факты о токенизации
    ↓
GitMCP (https://api.githubcopilot.com/mcp/) → Релевантные GitHub проекты
    ↓
AI Synthesis → Unified Summary → Telegram
```

### Быстрый тест
```bash
# Настройте только базовые переменные в .env:
OPENAI_API_KEY=your_key
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_USER_ID=your_id

# Запустите demo
./scripts/test_dual_mcp.sh
```

Результат: AI автоматически находит интересные факты о tiktoken, ищет связанные проекты на GitHub и создает объединенную техническую сводку.

---

## Быстрый старт (Production Setup)

### 1. Клонирование и настройка
```bash
git clone <your-repo>
cd day-8-backend

# Скопируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env с вашими настройками
nano .env
```

### 2. Настройка переменных окружения
Отредактируйте `.env` файл:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=gpt-4

# Remote MCP Server URLs (только 2 HTTPS endpoints)
MCP_WEB3_URL=https://your-web3-mcp-server.com
MCP_WHITEPAPER_URL=https://your-whitepapers-mcp-server.com

# Direct Telegram Integration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_USER_ID=7789201703

# Время отправки (22:00 по Амстердаму)
SCHEDULE_HOUR=22
SCHEDULE_MINUTE=0
```

### 3. Запуск с Docker Compose
```bash
# Сборка и запуск
docker-compose up -d

# Проверка логов
docker-compose logs -f crypto-digest

# Остановка
docker-compose down
```

### 4. Тестирование
```bash
# Запуск тестового выполнения (немедленно)
docker-compose run --rm crypto-digest-test

# Или ручной запуск в контейнере
docker-compose exec crypto-digest python scheduler.py --test
```

## Режимы работы

### APScheduler (по умолчанию)
Использует Python APScheduler для планирования:
- Более гибкое управление расписанием
- Лучшее логирование и обработка ошибок
- Graceful shutdown

### Cron режим
Альтернативно можно использовать системный cron:
```bash
# В docker-compose.yml раскомментируйте:
command: ["sh", "-c", "cron && tail -f /var/log/app.log"]
```

## Структура проекта

```
day-8-backend/
├── app/
│   ├── main.py           # Основная логика Responses API
│   └── scheduler.py      # APScheduler планировщик
├── deploy/
│   └── crontab.txt      # Конфигурация cron
├── Dockerfile           # Образ контейнера
├── docker-compose.yml   # Оркестрация сервисов
├── requirements.txt     # Python зависимости
├── .env.example        # Пример переменных окружения
├── .gitignore          # Git исключения
├── .cursorignore       # Cursor исключения
└── README.md           # Документация
```

## Логирование

Логи доступны в нескольких местах:
- `./logs/app.log` - основные логи приложения
- `./logs/scheduler.log` - логи планировщика
- `docker-compose logs crypto-digest` - логи контейнера

## Кэширование

Сервис сохраняет `response_id` последнего запроса для кэширования `tools/list`, что снижает стоимость и время выполнения:
- Кэш хранится в `./cache/last_response_id.txt`
- Автоматически используется при следующем запуске

## Мониторинг

### Health Check
Контейнер включает встроенную проверку здоровья:
```bash
docker-compose ps  # покажет статус
```

### Проверка следующего запуска
```bash
# Подключитесь к контейнеру
docker-compose exec crypto-digest python -c "
from scheduler import CryptoDigestScheduler
s = CryptoDigestScheduler()
s.add_daily_job()
print('Next run:', s.scheduler.get_jobs()[0].next_run_time)
"
```

## Устранение неполадок

### Проблемы с MCP подключением
1. Убедитесь что MCP серверы доступны публично
2. Проверьте URL и аутентификацию
3. Тестируйте endpoints через curl:
```bash
curl -X POST https://your-mcp-server.com/web3/tools/list
```

### Проблемы с OpenAI API
1. Проверьте корректность API ключа
2. Убедитесь что у вас есть доступ к Responses API
3. Проверьте квоты и лимиты

### Проблемы с Telegram
1. Проверьте токен бота и chat_id
2. Убедитесь что бот добавлен в чат
3. Проверьте доступность Telegram MCP сервера

## Развертывание в продакшене

### 1. Использование внешней базы данных (опционально)
Для персистентного хранения метаданных между перезапусками.

### 2. Мониторинг
Рекомендуется добавить:
- Prometheus метрики
- Alerting при ошибках
- Uptime мониторинг

### 3. Безопасность
- Используйте Docker secrets для API ключей
- Настройте firewall для MCP серверов
- Регулярно обновляйте зависимости

### 4. Масштабирование
- Можно запустить несколько инстансов для разных каналов
- Добавить load balancer для MCP серверов
- Использовать managed scheduling (AWS EventBridge, etc.)

## API Reference

### Responses API Configuration
```python
tools = [
    {
        "type": "mcp",
        "server_label": "web3research", 
        "server_url": "https://your-mcp.com/web3",
        "allowed_tools": ["search", "token-research"],
        "require_approval": "never"
    }
]
```

### Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API ключ |
| `OPENAI_MODEL` | No | `gpt-4` | Модель для использования |
| `MCP_WEB3_URL` | Yes | - | URL web3-research-mcp |
| `MCP_WHITEPAPER_URL` | Yes | - | URL crypto-whitepapers-mcp |  
| `TELEGRAM_BOT_TOKEN` | Yes | - | Токен Telegram бота |
| `TELEGRAM_USER_ID` | Yes | - | ID пользователя для отправки сообщений |
| `SCHEDULE_HOUR` | No | `22` | Час отправки (0-23) |
| `SCHEDULE_MINUTE` | No | `0` | Минута отправки (0-59) |

## Ссылки

- [OpenAI Responses API](https://openai.com/index/new-tools-and-features-in-the-responses-api/)
- [MCP Tool Guide](https://cookbook.openai.com/examples/mcp/mcp_tool_guide)
- [web3-research-mcp](https://github.com/aaronjmars/web3-research-mcp)
- [crypto-whitepapers-mcp](https://github.com/kukapay/crypto-whitepapers-mcp)
- [mcp-communicator-telegram](https://github.com/qpd-v/mcp-communicator-telegram)
