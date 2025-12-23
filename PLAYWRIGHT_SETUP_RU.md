# Playwright: Что это и как интегрировать в архитектуру

## Что такое Playwright?

**Playwright** — это инструмент для автоматизации браузеров (Chrome, Firefox, Safari). Он:
- Запускает реальный браузер
- Выполняет JavaScript на странице
- Позволяет парсить динамический контент (который загружается через JS)
- Может делать скриншоты
- Может эмулировать мобильные устройства

## Почему Playwright нужно выносить в отдельный сервис?

### ❌ Проблемы текущей архитектуры

1. **Cloudflare Workers не поддерживает Playwright**
   - В Workers нет доступа к браузерам
   - Ваш проект готовится к деплою на Cloudflare Workers
   - Playwright не будет работать там

2. **Ресурсы**
   - Playwright требует много памяти (2-4 GB)
   - Требует CPU для рендеринга
   - Может блокировать основной API

3. **Производительность**
   - Запуск браузера занимает 5-30 секунд
   - Блокирует основной поток обработки запросов

### ✅ Решение: Отдельный Playwright Worker

```
┌─────────────────────────┐
│   Основной API          │  ──HTTP──>  ┌─────────────────────┐
│   (Cloudflare Workers)  │              │ Playwright Worker   │
│                         │  <──JSON───  │ (VPS/Docker)        │
│ - Быстрые запросы       │              │                     │
│ - Обработка данных      │              │ - Запуск браузеров  │
│ - Хранение              │              │ - Рендеринг JS      │
└─────────────────────────┘              │ - Скриншоты         │
                                         └─────────────────────┘
```

## Архитектура решения

### 1. Основной Backend API (`main.py`)
- Остается на Cloudflare Workers
- Быстрые операции
- Координация с Playwright Worker через HTTP

### 2. Playwright Worker Service (`playwright_worker/`)
- Отдельный FastAPI сервис
- Запускается на VPS/Docker (не на Cloudflare Workers)
- Выполняет браузерные операции

## Как это работает?

### Пример взаимодействия:

```python
# В основном API (main.py)
# Когда нужен браузер для скраппинга:

async def scrape_facebook_with_browser(url: str):
    playwright_service = "http://playwright-worker:8001"
    
    # Отправляем запрос в Playwright Worker
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{playwright_service}/scrape",
            json={"url": url, "wait_time": 5}
        )
        result = response.json()
        
    # Получаем HTML с отрендеренным JavaScript
    html = result["html"]
    
    # Парсим комментарии из HTML
    comments = parse_comments(html)
    
    return comments
```

### Playwright Worker получает запрос:
1. Запускает браузер (Chromium)
2. Открывает URL
3. Ждет загрузки JavaScript
4. Прокручивает страницу
5. Извлекает HTML
6. Возвращает HTML в основной API

## Быстрый старт

### 1. Запустить Playwright Worker локально

```bash
cd playwright_worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
python main.py
```

Сервис будет доступен на `http://localhost:8001`

### 2. Настроить основной API

В `.env` или переменных окружения:
```bash
PLAYWRIGHT_SERVICE_URL=http://localhost:8001
USE_EXTERNAL_PLAYWRIGHT=true
```

### 3. Модифицировать `facebook_client.py`

Добавьте проверку на использование внешнего Playwright Worker:

```python
if USE_EXTERNAL_PLAYWRIGHT:
    # Используем внешний сервис
    result = await fetch_with_external_playwright(url, wait_time)
else:
    # Используем локальный Playwright (только для разработки)
    result = await fetch_with_local_playwright(url, wait_time)
```

## Деплой

### Playwright Worker на VPS

```bash
# 1. Установить на сервере
git clone <repo>
cd playwright_worker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Запустить через systemd или supervisor
# См. playwright_worker/README.md
```

### Основной API на Cloudflare Workers

```bash
# Деплой как обычно
wrangler deploy

# Установить переменную окружения
wrangler secret put PLAYWRIGHT_SERVICE_URL
# Ввести: https://your-playwright-worker.com
```

## Преимущества такой архитектуры

✅ **Основной API остается быстрым** - не блокируется браузерными операциями  
✅ **Масштабирование** - можно запустить несколько Playwright Workers  
✅ **Изоляция** - проблемы с браузером не влияют на основной API  
✅ **Гибкость** - можно использовать разные платформы для каждого сервиса  
✅ **Стоимость** - Cloudflare Workers дешево, Playwright Worker только когда нужно  

## Альтернативы

### Вариант 1: Celery Worker (для локального/серверного развертывания)
- Используйте Celery + Redis для очереди задач
- Playwright Worker как Celery worker
- Основной API отправляет задачи в очередь

### Вариант 2: Serverless функции (AWS Lambda, Google Cloud Functions)
- Playwright можно запустить в Lambda (с ограничениями)
- Дороже, но проще управление

### Вариант 3: Готовые сервисы
- ScrapingBee, ScraperAPI, Browserless.io
- Платные, но не нужно поддерживать инфраструктуру

## Рекомендации

1. **Для разработки**: Используйте локальный Playwright Worker (`localhost:8001`)
2. **Для production**: 
   - Основной API → Cloudflare Workers
   - Playwright Worker → VPS (DigitalOcean, Hetzner) или Docker
3. **Мониторинг**: Добавьте health checks и логирование
4. **Безопасность**: Ограничьте доступ к Playwright Worker (API ключи, VPN)

## Дополнительная информация

- [ARCHITECTURE.md](ARCHITECTURE.md) - Подробная архитектура проекта
- [playwright_worker/README.md](playwright_worker/README.md) - Документация Playwright Worker
- [playwright_worker/integration_example.py](playwright_worker/integration_example.py) - Пример интеграции

## Вопросы?

**Q: Можно ли оставить Playwright в основном API?**  
A: Только для локальной разработки. На Cloudflare Workers не будет работать.

**Q: Сколько стоит Playwright Worker?**  
A: Зависит от провайдера. VPS с 2GB RAM стоит ~$5-10/месяц.

**Q: Можно ли использовать бесплатные варианты?**  
A: Да, можно использовать Railway, Render (с ограничениями) или свой сервер.

**Q: Как масштабировать?**  
A: Запустите несколько инстансов Playwright Worker и используйте load balancer.

