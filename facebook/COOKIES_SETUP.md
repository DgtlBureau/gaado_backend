# Настройка Cookies для Facebook Scraper

## Проблема

Facebook Scraper может не находить страницы (например, `premierbankso`) без авторизации через cookies. Это связано с ограничениями Facebook для неавторизованных запросов.

## Решение: Использование Cookies

### Быстрый старт

1. **Запустите скрипт для получения cookies:**
   ```bash
   python3 get_facebook_cookies.py
   ```

2. **Следуйте инструкциям в скрипте:**
   - Войдите в Facebook в браузере
   - Откройте Developer Tools (F12)
   - Получите cookies `c_user` и `xs`
   - Скрипт создаст файл `cookies.txt`

3. **Перезапустите сервер:**
   ```bash
   uvicorn main:app --reload
   ```

Теперь скраппер будет автоматически использовать cookies из файла `cookies.txt`.

## Подробная инструкция

### Способ 1: Через Application/Storage Tab (Рекомендуется)

1. **Откройте Facebook в браузере:**
   - Перейдите на https://www.facebook.com
   - Войдите в свой аккаунт

2. **Откройте Developer Tools:**
   - Нажмите `F12` (или `Cmd+Option+I` на Mac)
   - Или правый клик → "Inspect"

3. **Найдите Cookies:**
   - Перейдите на вкладку **"Application"** (Chrome) или **"Storage"** (Firefox)
   - В левой панели найдите **"Cookies"** → **"https://www.facebook.com"**

4. **Скопируйте значения:**
   - Найдите cookie **`c_user`** - скопируйте его значение (это ваш User ID)
   - Найдите cookie **`xs`** - скопируйте его значение (токен сессии)
   - Опционально: **`datr`** - также может быть полезен

5. **Создайте файл cookies.txt:**
   ```bash
   python3 get_facebook_cookies.py
   ```
   Введите значения cookies по запросу.

### Способ 2: Через Network Tab

1. Откройте Facebook и войдите
2. Откройте Developer Tools (F12)
3. Перейдите на вкладку **"Network"**
4. Обновите страницу (F5)
5. Найдите любой запрос к `facebook.com`
6. Откройте запрос → вкладка **"Headers"**
7. Найдите **"Cookie:"** в Request Headers
8. Скопируйте всю строку Cookie
9. Запустите скрипт и выберите способ 2, вставьте строку Cookie

### Способ 3: Ручное создание файла

Создайте файл `cookies.txt` в формате Netscape:

```
# Netscape HTTP Cookie File
# This file was generated manually

.facebook.com	TRUE	/	FALSE	0	c_user	YOUR_C_USER_VALUE
.facebook.com	TRUE	/	FALSE	0	xs	YOUR_XS_VALUE
.facebook.com	TRUE	/	FALSE	0	datr	YOUR_DATR_VALUE
```

Замените `YOUR_C_USER_VALUE`, `YOUR_XS_VALUE` и `YOUR_DATR_VALUE` на реальные значения из браузера.

## Использование

После создания файла `cookies.txt`, сервер автоматически будет использовать его при создании FacebookScraperClient.

### Через переменную окружения

Вы также можете указать путь к файлу cookies через переменную окружения:

```bash
export FACEBOOK_COOKIES_FILE=/path/to/cookies.txt
uvicorn main:app --reload
```

### Проверка работы

После настройки cookies, проверьте работу скраппера:

```bash
# Через curl
curl "http://localhost:8000/facebook/page/premierbankso"

# Или через веб-интерфейс
# Откройте http://localhost:8000/ и используйте форму скраппера
```

## Важные замечания

⚠️ **Безопасность:**
- **НЕ коммитьте** файл `cookies.txt` в git (он уже добавлен в .gitignore)
- **НЕ делитесь** файлом cookies ни с кем
- Cookies содержат ваши учетные данные для доступа к Facebook

⚠️ **Срок действия:**
- Cookies могут истечь через некоторое время
- Если скраппер перестал работать, обновите cookies
- Обычно cookies действуют несколько дней/недель

⚠️ **Ограничения:**
- Используйте только для публичных страниц
- Не злоупотребляйте запросами (Facebook может заблокировать)
- Соблюдайте Terms of Service Facebook

## Troubleshooting

### Проблема: "Страница не найдена" даже с cookies

**Возможные причины:**
1. Cookies истекли - обновите их
2. Неправильный формат файла cookies.txt
3. Страница действительно недоступна или приватная

**Решение:**
1. Проверьте формат файла cookies.txt
2. Обновите cookies через скрипт
3. Проверьте доступность страницы в браузере

### Проблема: "Cookies не найдены" в логах

**Решение:**
- Убедитесь, что файл `cookies.txt` находится в директории проекта
- Или установите переменную окружения `FACEBOOK_COOKIES_FILE`

### Проблема: Скрипт не запускается

**Решение:**
```bash
chmod +x get_facebook_cookies.py
python3 get_facebook_cookies.py
```

## Альтернативные решения

Если cookies не помогают, рассмотрите:
1. Использование официального Facebook Graph API (требует регистрации приложения)
2. Использование прокси-серверов
3. Добавление задержек между запросами
4. Использование специализированных сервисов для скрапинга

## Полезные ссылки

- [facebook-scraper GitHub](https://github.com/kevinzg/facebook-scraper)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)

