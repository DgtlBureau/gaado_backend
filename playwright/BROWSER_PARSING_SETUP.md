# Автоматический парсинг комментариев через браузер

## Проблема

Facebook загружает комментарии динамически через JavaScript, поэтому простой HTTP-запрос не может их извлечь. Решение — использовать браузер с рендерингом JavaScript.

## Решение: Playwright

Playwright автоматически запускает браузер, рендерит JavaScript и извлекает комментарии. **Никакого ручного просмотра не требуется!**

## Установка

```bash
# 1. Установите Playwright
pip install playwright

# 2. Установите браузер Chromium
playwright install chromium
```

## Использование

### Вариант 1: Через Python код

```python
from facebook_client import FacebookScraperClient

client = FacebookScraperClient(cookies="cookies.txt")

# Автоматически загружает страницу через браузер и извлекает комментарии
result = await client.fetch_and_parse_comments_with_browser(
    "https://www.facebook.com/premierbankso/posts/...",
    limit=100,
    wait_time=5  # секунд ожидания загрузки комментариев
)

print(f"Найдено комментариев: {result['total_count']}")
for comment in result['comments']:
    print(f"{comment['author']}: {comment['text']}")
```

### Вариант 2: Через API

```bash
curl -X POST "http://localhost:8000/facebook/parse-url" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.facebook.com/premierbankso/posts/...",
    "limit": 100,
    "use_browser": true,
    "wait_time": 5
  }'
```

### Вариант 3: Тестовый скрипт

```bash
python test_browser_parsing.py
```

## Параметры

- `url` - URL страницы Facebook с комментариями
- `limit` - Максимальное количество комментариев (по умолчанию 100)
- `wait_time` - Время ожидания загрузки комментариев в секундах (по умолчанию 5)
- `use_browser` - Использовать браузер для рендеринга (только для API)

## Как это работает

1. **Запускает браузер** (Chromium в headless режиме)
2. **Загружает cookies** из файла `cookies.txt` (если есть)
3. **Открывает страницу** Facebook
4. **Ждет загрузки** JavaScript и комментариев
5. **Прокручивает страницу** для загрузки большего количества комментариев
6. **Извлекает HTML** после полного рендеринга
7. **Парсит комментарии** из HTML

## Преимущества

✅ **Полностью автоматический** - никакого ручного просмотра  
✅ **Работает с JavaScript** - извлекает динамически загружаемые комментарии  
✅ **Использует cookies** - для доступа к приватным страницам  
✅ **Настраиваемый** - можно изменить время ожидания и лимит  

## Недостатки

⚠️ Требует установки браузера (Chromium ~170MB)  
⚠️ Медленнее чем простой HTTP запрос (10-30 секунд)  
⚠️ Требует больше ресурсов (память, CPU)  

## Рекомендации

- Используйте `wait_time=5-10` секунд для страниц с большим количеством комментариев
- Убедитесь, что файл `cookies.txt` актуален для доступа к странице
- Для production используйте сервер с достаточным количеством памяти (минимум 2GB RAM)

## Примеры

### Базовое использование

```python
result = await client.fetch_and_parse_comments_with_browser(
    "https://www.facebook.com/premierbankso/posts/...",
    limit=50
)
```

### С увеличенным временем ожидания

```python
result = await client.fetch_and_parse_comments_with_browser(
    "https://www.facebook.com/premierbankso/posts/...",
    limit=100,
    wait_time=10  # Ждем 10 секунд для загрузки всех комментариев
)
```

## Устранение проблем

### Ошибка: "Playwright не установлен"
```bash
pip install playwright
playwright install chromium
```

### Комментарии не найдены
- Увеличьте `wait_time` до 10-15 секунд
- Проверьте, что `cookies.txt` актуален
- Убедитесь, что страница публичная или доступна с вашими cookies

### Браузер не запускается
- Убедитесь, что Chromium установлен: `playwright install chromium`
- Проверьте права доступа к файловой системе
- На Linux может потребоваться установка дополнительных библиотек

