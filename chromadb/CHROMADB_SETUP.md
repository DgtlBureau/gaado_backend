# Настройка ChromaDB для Gaado Backend

ChromaDB используется для хранения векторных представлений документов и семантического поиска.

## Варианты развертывания

### 1. Локальная разработка (файловая система)

Для локальной разработки ChromaDB использует файловую систему:

```bash
# Установка зависимостей
pip install chromadb sentence-transformers

# ChromaDB автоматически создаст директорию ./chroma_db
# Данные будут сохраняться локально
```

**Переменные окружения:**
```bash
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=gaado_documents
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### 2. ChromaDB Server (для production)

Для production рекомендуется использовать отдельный сервер ChromaDB:

#### Установка ChromaDB Server:

```bash
# Через Docker
docker pull chromadb/chroma
docker run -p 8000:8000 chromadb/chroma

# Или через pip
pip install chromadb[server]
chroma run --host localhost --port 8000
```

#### Подключение:

```bash
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=gaado_documents
```

### 3. ChromaDB Cloud (для Cloudflare Workers)

Для развертывания на Cloudflare Workers используйте ChromaDB Cloud:

1. **Зарегистрируйтесь на [ChromaDB Cloud](https://www.trychroma.com/)**
2. **Создайте инстанс и получите API ключ**
3. **Настройте переменные окружения:**

```bash
CHROMA_API_URL=https://your-instance.chromadb.cloud
CHROMA_API_KEY=your_api_key_here
CHROMA_COLLECTION_NAME=gaado_documents
```

Для Cloudflare Workers установите секреты:

```bash
wrangler secret put CHROMA_API_URL
wrangler secret put CHROMA_API_KEY
```

## Использование API

### Добавление документов

```bash
curl -X POST "http://localhost:8000/chromadb/add" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "This is a sample document about AI",
      "Another document about machine learning"
    ],
    "metadatas": [
      {"source": "doc1", "category": "AI"},
      {"source": "doc2", "category": "ML"}
    ]
  }'
```

### Поиск документов

```bash
curl -X POST "http://localhost:8000/chromadb/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "artificial intelligence",
    "n_results": 5
  }'
```

### Получение информации о коллекции

```bash
curl "http://localhost:8000/chromadb/info"
```

### Удаление документов

```bash
curl -X DELETE "http://localhost:8000/chromadb/delete" \
  -H "Content-Type: application/json" \
  -d '["document-id-1", "document-id-2"]'
```

## Интеграция с обработкой данных

При обработке данных через `/process` можно автоматически сохранять в ChromaDB:

```bash
curl -X POST "http://localhost:8000/process?save_to_chromadb=true" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I love this product!",
    "metadata": {"source": "review"}
  }'
```

## Модели эмбеддингов

Рекомендуемые модели для создания эмбеддингов:

- `sentence-transformers/all-MiniLM-L6-v2` (по умолчанию) - быстрая, легкая
- `sentence-transformers/all-mpnet-base-v2` - более точная
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` - мультиязычная

Измените модель через переменную окружения:

```bash
export EMBEDDING_MODEL="sentence-transformers/all-mpnet-base-v2"
```

## Troubleshooting

### Ошибка подключения к ChromaDB:

1. Проверьте, что ChromaDB сервер запущен (для server mode)
2. Проверьте переменные окружения
3. Проверьте сетевые настройки и firewall

### Ошибка загрузки модели эмбеддингов:

1. Убедитесь, что модель доступна на Hugging Face
2. Проверьте интернет-соединение (модель загружается при первом использовании)
3. Рассмотрите использование локальной модели

### Проблемы с памятью:

1. Используйте более легкие модели эмбеддингов
2. Ограничьте размер коллекции
3. Используйте ChromaDB Cloud для production

### Для Cloudflare Workers:

1. **Обязательно используйте ChromaDB Cloud** - локальная файловая система недоступна
2. Установите секреты через `wrangler secret put`
3. Проверьте логи: `wrangler tail`

## Рекомендации

1. **Для разработки:** Используйте локальную файловую систему
2. **Для staging:** Используйте ChromaDB Server
3. **Для production:** Используйте ChromaDB Cloud
4. **Для Cloudflare Workers:** Только ChromaDB Cloud или внешний сервер

## Дополнительные ресурсы

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [ChromaDB Cloud](https://www.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)

