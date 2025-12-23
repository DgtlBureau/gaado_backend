# Архитектура проекта Gaado Backend

## Общая архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Основной Backend API                      │
│                  (FastAPI / Cloudflare Workers)              │
│                                                              │
│  - Обработка запросов                                        │
│  - Хранение данных                                           │
│  - Бизнес-логика                                             │
│  - Простой HTTP скраппинг (httpx)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP запросы
                       │ (REST API)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Playwright Worker Service                       │
│              (Отдельный сервис/воркер)                       │
│                                                              │
│  - Запуск браузеров (Playwright)                            │
│  - Рендеринг JavaScript                                      │
│  - Скриншоты                                                 │
│  - Парсинг динамического контента                           │
│  - Возврат HTML/данных в основной API                        │
└─────────────────────────────────────────────────────────────┘
```

## Компоненты

### 1. Основной Backend API (`main.py`)
- **Назначение**: Основной API для обработки запросов
- **Технологии**: FastAPI, может деплоиться на Cloudflare Workers
- **Функции**:
  - Обработка текста
  - Хранение данных
  - Простой HTTP скраппинг (без браузера)
  - Координация с Playwright сервисом

### 2. Playwright Worker Service (отдельный сервис)
- **Назначение**: Выполнение браузерной автоматизации
- **Технологии**: FastAPI + Playwright
- **Функции**:
  - Открытие сайтов через браузер
  - Рендеринг JavaScript
  - Скриншоты
  - Парсинг динамического контента
  - Возврат результатов в основной API

## Варианты развертывания Playwright Worker

### Вариант 1: Отдельный FastAPI сервис (рекомендуется)

**Структура:**
```
gaado_backend/
├── main.py                    # Основной API
├── playwright_worker/         # Отдельный сервис
│   ├── main.py               # FastAPI приложение для Playwright
│   ├── requirements.txt      # Зависимости (playwright, fastapi)
│   └── worker.py             # Логика работы с браузером
```

**Преимущества:**
- ✅ Полный контроль над ресурсами
- ✅ Независимое масштабирование
- ✅ Можно деплоить на любой платформе (VPS, Docker, Railway, Render)
- ✅ Легко тестировать отдельно

**Деплой:**
- VPS (DigitalOcean, Hetzner, AWS EC2)
- Docker контейнер
- Railway, Render, Fly.io
- Kubernetes pod

### Вариант 2: Celery Worker (для локального/серверного развертывания)

**Структура:**
```
gaado_backend/
├── main.py                    # Основной API
├── celery_worker/             # Celery воркер
│   ├── worker.py             # Celery задачи с Playwright
│   └── tasks.py              # Определение задач
```

**Преимущества:**
- ✅ Асинхронная обработка задач
- ✅ Очередь задач (Redis/RabbitMQ)
- ✅ Retry механизм
- ✅ Мониторинг через Flower

### Вариант 3: Cloudflare Workers + External Playwright Service

**Структура:**
```
┌─────────────────────┐
│ Cloudflare Workers   │  ──HTTP──>  ┌─────────────────────┐
│ (Основной API)      │              │ Playwright Service   │
│                     │  <──JSON───  │ (VPS/Docker)         │
└─────────────────────┘              └─────────────────────┘
```

**Преимущества:**
- ✅ Основной API на Cloudflare (быстро, глобально)
- ✅ Playwright на отдельном сервере (ресурсы)
- ✅ Оптимальная стоимость

## Рекомендуемая архитектура для вашего проекта

### Текущая ситуация
- Основной API готов к деплою на Cloudflare Workers
- Playwright интегрирован напрямую в `facebook_client.py`
- Это не будет работать на Cloudflare Workers

### Рекомендуемое решение

**1. Вынести Playwright в отдельный FastAPI сервис**

Создать `playwright_worker/` с собственным API:
- `POST /scrape` - скраппинг через браузер
- `POST /screenshot` - скриншот страницы
- `GET /health` - проверка здоровья

**2. Модифицировать основной API**

В `facebook_client.py`:
- Если нужен браузер → отправлять запрос в Playwright Worker
- Если простой HTTP → использовать httpx напрямую

**3. Деплой**

- **Основной API**: Cloudflare Workers (быстро, дешево)
- **Playwright Worker**: VPS/Docker (ресурсы для браузера)

## Пример взаимодействия

```python
# В основном API (main.py)
async def scrape_with_browser(url: str):
    playwright_service_url = os.getenv("PLAYWRIGHT_SERVICE_URL", "http://localhost:8001")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{playwright_service_url}/scrape",
            json={"url": url, "wait_time": 5}
        )
        return response.json()

# В Playwright Worker (playwright_worker/main.py)
@app.post("/scrape")
async def scrape_page(request: ScrapeRequest):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(request.url)
        await page.wait_for_timeout(request.wait_time * 1000)
        html = await page.content()
        await browser.close()
        return {"html": html, "status": "success"}
```

## Переменные окружения

```bash
# Основной API
PLAYWRIGHT_SERVICE_URL=http://localhost:8001  # URL Playwright Worker

# Playwright Worker
PORT=8001
MAX_CONCURRENT_BROWSERS=5  # Максимум одновременных браузеров
```

## Масштабирование

### Горизонтальное масштабирование Playwright Worker
- Запустить несколько инстансов Playwright Worker
- Использовать load balancer (nginx, Cloudflare Load Balancer)
- Или очередь задач (Celery + Redis)

### Вертикальное масштабирование
- Увеличить RAM (минимум 2GB на инстанс)
- Увеличить CPU (минимум 2 ядра)
- Использовать SSD для кеша браузера

## Безопасность

1. **Аутентификация между сервисами**
   - API ключи
   - JWT токены
   - Внутренняя сеть (VPN)

2. **Ограничения**
   - Rate limiting на Playwright Worker
   - Whitelist доменов для скраппинга
   - Таймауты на запросы

3. **Изоляция**
   - Docker контейнеры
   - Sandbox окружение
   - Ограничение ресурсов

## Мониторинг

- Health checks обоих сервисов
- Логирование всех запросов
- Метрики производительности
- Алерты при ошибках

