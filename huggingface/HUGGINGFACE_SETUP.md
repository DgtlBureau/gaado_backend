# Подготовка модели на Hugging Face

Это руководство поможет вам подготовить и использовать модель на Hugging Face для проекта Gaado Backend.

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

Или отдельно:
```bash
pip install huggingface_hub
```

### 2. Настройка API ключа

1. **Получите токен API:**
   - Зарегистрируйтесь на [Hugging Face](https://huggingface.co/join)
   - Перейдите в [Settings > Tokens](https://huggingface.co/settings/tokens)
   - Создайте новый токен с правами `read`
   - Скопируйте токен

2. **Установите переменную окружения:**
   ```bash
   export HF_API_KEY="your_token_here"
   ```

   Или создайте файл `.env` в корне проекта:
   ```
   HF_API_KEY=your_token_here
   HF_DEFAULT_MODEL=Qwen/Qwen2.5-7B-Instruct:together
   ```

### 3. Использование HuggingFaceClient

```python
from huggingface import HuggingFaceClient

# Инициализация клиента
client = HuggingFaceClient()

# Простой чат
response = client.simple_chat("What is the capital of France?")
print(response)

# Chat completion с полным контролем
result = client.chat_completion(
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ],
    temperature=0.7,
    max_tokens=100
)
print(result["choices"][0]["message"]["content"])
```

### 4. Локальное тестирование

Запустите тестовый файл:
```bash
python huggingface/test_huggingface_local.py
```

## Варианты использования моделей

### 1. Использование готовых моделей через Inference API

Самый простой способ - использовать готовые модели через Hugging Face Inference API.

#### Шаги:

1. **Получите токен API:**
   - Зарегистрируйтесь на [Hugging Face](https://huggingface.co/join)
   - Перейдите в [Settings > Tokens](https://huggingface.co/settings/tokens)
   - Создайте новый токен с правами `read`
   - Сохраните токен в переменную окружения `HF_API_KEY`

2. **Выберите модель:**
   - Просмотрите доступные модели на [Hugging Face Model Hub](https://huggingface.co/models)
   - Для чата популярные модели:
     - `Qwen/Qwen2.5-7B-Instruct:together` - чат модель (по умолчанию)
     - `meta-llama/Llama-3.1-8B-Instruct` - чат модель от Meta
     - `mistralai/Mistral-7B-Instruct-v0.2` - чат модель от Mistral
   - Для анализа текста:
     - `distilbert-base-uncased-finetuned-sst-2-english` - анализ тональности
     - `sentence-transformers/all-MiniLM-L6-v2` - для создания эмбеддингов
     - `facebook/bart-large-mnli` - классификация текста

3. **Настройте переменные окружения:**
   ```bash
   export HF_API_KEY="your_token_here"
   export HF_DEFAULT_MODEL="Qwen/Qwen2.5-7B-Instruct:together"
   ```

### 2. Загрузка и использование собственной модели

Если вы хотите использовать свою модель:

#### Шаги:

1. **Подготовьте модель:**
   - Обучите или выберите модель
   - Убедитесь, что модель совместима с Hugging Face Transformers

2. **Загрузите модель на Hugging Face:**
   ```bash
   # Установите Hugging Face Hub
   pip install huggingface_hub
   
   # Авторизуйтесь
   huggingface-cli login
   
   # Создайте репозиторий и загрузите модель
   huggingface-cli repo create your-username/your-model-name --type model
   git clone https://huggingface.co/your-username/your-model-name
   # Скопируйте файлы модели в директорию
   git add .
   git commit -m "Add model files"
   git push
   ```

3. **Используйте модель через API:**
   - После загрузки модель будет доступна через Inference API
   - Используйте имя модели: `your-username/your-model-name`

### 3. Использование модели локально (для разработки)

Для локальной разработки можно использовать модель напрямую:

```python
from transformers import pipeline

# Загрузка модели
classifier = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")

# Использование
result = classifier("I love this product!")
print(result)
```

## Рекомендации для Cloudflare Workers

### Ограничения:

1. **Размер модели:** Cloudflare Workers имеют ограничения по памяти
2. **Время выполнения:** Максимальное время выполнения запроса ограничено
3. **Зависимости:** Не все библиотеки доступны в Workers

### Рекомендуемый подход:

1. **Используйте Inference API** вместо локальной загрузки модели
2. **Выбирайте легкие модели** для быстрой обработки
3. **Кэшируйте результаты** когда возможно
4. **Используйте асинхронные запросы** для лучшей производительности

## Примеры моделей для разных задач

### Анализ тональности:
- `distilbert-base-uncased-finetuned-sst-2-english` (по умолчанию)
- `nlptown/bert-base-multilingual-uncased-sentiment`

### Создание эмбеддингов:
- `sentence-transformers/all-MiniLM-L6-v2` (быстрая, легкая)
- `sentence-transformers/all-mpnet-base-v2` (более точная)

### Классификация текста:
- `facebook/bart-large-mnli`
- `typeform/distilbert-base-uncased-mnli`

### Генерация текста:
- `google/flan-t5-base`
- `gpt2` (для генерации)

## Использование HuggingFaceClient

### Базовое использование

```python
from huggingface import HuggingFaceClient

# Инициализация (берет HF_API_KEY из переменных окружения)
client = HuggingFaceClient()

# Проверка доступности
if client.is_available():
    # Простой чат
    response = client.simple_chat("What is Python?")
    print(response)
```

### Использование с системным промптом

```python
response = client.simple_chat(
    prompt="Explain quantum computing",
    system_prompt="You are a helpful assistant that explains complex topics simply."
)
```

### Использование другой модели

```python
response = client.simple_chat(
    prompt="What is the capital of France?",
    model="meta-llama/Llama-3.1-8B-Instruct"
)
```

### Полный контроль через chat_completion

```python
result = client.chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2?"}
    ],
    model="Qwen/Qwen2.5-7B-Instruct:together",
    temperature=0.7,
    max_tokens=150
)

print(result["choices"][0]["message"]["content"])
print(f"Использовано токенов: {result['usage']['total_tokens']}")
```

### Многошаговый разговор

```python
messages = [
    {"role": "user", "content": "My name is Alice"}
]

# Первый ответ
result1 = client.chat_completion(messages=messages)
response1 = result1["choices"][0]["message"]["content"]
print(response1)

# Добавляем ответ в историю и задаем следующий вопрос
messages.append({"role": "assistant", "content": response1})
messages.append({"role": "user", "content": "What's my name?"})

result2 = client.chat_completion(messages=messages)
print(result2["choices"][0]["message"]["content"])
```

## Тестирование модели

### Локальное тестирование

Запустите тестовый файл:
```bash
python huggingface/test_huggingface_local.py
```

Тестовый файл включает:
- Простой чат
- Полный chat completion
- Использование системного промпта
- Использование кастомной модели
- Многошаговый разговор

## Troubleshooting

### Модель не отвечает:
- Проверьте, что модель доступна на Hugging Face
- Убедитесь, что токен API правильный
- Проверьте логи: `wrangler tail` (для Cloudflare Workers)

### Таймауты:
- Используйте более легкие модели
- Увеличьте timeout в коде (если возможно)
- Рассмотрите использование кэширования

### Ошибки авторизации:
- Проверьте токен API
- Убедитесь, что токен имеет правильные права доступа
- Проверьте, что модель публичная или у вас есть доступ

