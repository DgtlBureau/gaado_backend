# Playwright Worker Service

Отдельный сервис для выполнения браузерной автоматизации с использованием Playwright.

## Назначение

Этот сервис вынесен из основного API по следующим причинам:

1. **Cloudflare Workers не поддерживает Playwright** - нет доступа к браузерам
2. **Ресурсы** - Playwright требует много памяти (2-4GB) и CPU
3. **Изоляция** - браузерные операции не должны блокировать основной API
4. **Масштабирование** - можно масштабировать независимо от основного API

## Установка

```bash
# 1. Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Установить браузеры Playwright
playwright install chromium
```

## Запуск

```bash
# Локально
python main.py

# Или через uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001

# С переменными окружения
PORT=8001 MAX_CONCURRENT_BROWSERS=5 python main.py
```

## API Endpoints

### POST /scrape
Скраппинг страницы через браузер

**Request:**
```json
{
  "url": "https://www.facebook.com/premierbankso/posts/...",
  "wait_time": 5,
  "scroll": true,
  "cookies": [
    {
      "name": "c_user",
      "value": "123456789",
      "domain": ".facebook.com",
      "path": "/"
    }
  ],
  "user_agent": "Mozilla/5.0..."
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://www.facebook.com/...",
  "html": "<html>...</html>",
  "html_size": 123456,
  "duration_seconds": 12.34,
  "fetched_at": "2024-01-01T12:00:00",
  "method": "browser_rendering"
}
```

### POST /screenshot
Сделать скриншот страницы

**Request:**
```json
{
  "url": "https://example.com",
  "wait_time": 5,
  "full_page": false,
  "width": 1920,
  "height": 1080
}
```

**Response:**
```json
{
  "success": true,
  "url": "https://example.com",
  "screenshot": "base64_encoded_image",
  "format": "png",
  "full_page": false,
  "fetched_at": "2024-01-01T12:00:00"
}
```

### GET /health
Проверка здоровья сервиса

**Response:**
```json
{
  "status": "healthy",
  "playwright_available": true,
  "active_browsers": 2,
  "max_concurrent_browsers": 5,
  "timestamp": "2024-01-01T12:00:00"
}
```

### GET /stats
Статистика сервиса

## Переменные окружения

```bash
# Порт сервиса
PORT=8001

# Максимум одновременных браузеров
MAX_CONCURRENT_BROWSERS=5

# Максимальное время ожидания (секунды)
MAX_WAIT_TIME=30

# Разрешенные домены (через запятую, пусто = все разрешены)
ALLOWED_DOMAINS=facebook.com,example.com
```

## Интеграция с основным API

В основном API (`main.py` или `facebook_client.py`) добавьте:

```python
import os
import httpx

PLAYWRIGHT_SERVICE_URL = os.getenv("PLAYWRIGHT_SERVICE_URL", "http://localhost:8001")

async def scrape_with_browser(url: str, wait_time: int = 5):
    """Использовать Playwright Worker для скраппинга"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{PLAYWRIGHT_SERVICE_URL}/scrape",
            json={
                "url": url,
                "wait_time": wait_time,
                "scroll": True
            }
        )
        response.raise_for_status()
        return response.json()
```

## Деплой

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка браузеров Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  playwright-worker:
    build: .
    ports:
      - "8001:8001"
    environment:
      - PORT=8001
      - MAX_CONCURRENT_BROWSERS=5
      - MAX_WAIT_TIME=30
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
```

### VPS (systemd)

Создайте `/etc/systemd/system/playwright-worker.service`:

```ini
[Unit]
Description=Playwright Worker Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/playwright-worker
Environment="PORT=8001"
Environment="MAX_CONCURRENT_BROWSERS=5"
ExecStart=/opt/playwright-worker/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

## Мониторинг

- Health check: `GET /health`
- Статистика: `GET /stats`
- Логи: все операции логируются

## Безопасность

1. **Ограничение доменов**: используйте `ALLOWED_DOMAINS`
2. **Rate limiting**: добавьте rate limiting middleware
3. **Аутентификация**: добавьте API ключи для доступа
4. **Изоляция**: запускайте в Docker контейнере

## Производительность

- **Рекомендуемые ресурсы**: 2-4GB RAM, 2 CPU cores
- **Максимум браузеров**: настраивается через `MAX_CONCURRENT_BROWSERS`
- **Таймауты**: настраиваются через `MAX_WAIT_TIME`

## Troubleshooting

### Браузер не запускается
```bash
# Установите зависимости
playwright install-deps chromium

# Проверьте права доступа
chmod +x /path/to/chromium
```

### Недостаточно памяти
- Уменьшите `MAX_CONCURRENT_BROWSERS`
- Увеличьте RAM сервера
- Используйте `headless=True` (по умолчанию)

### Медленная работа
- Уменьшите `wait_time`
- Используйте SSD для кеша браузера
- Увеличьте CPU cores

