# Gaado Backend API

FastAPI application for processing scraped data. Prepared for deployment on Cloudflare Workers.

## Project Structure

```
gaado_backend/
├── main.py                          # Main FastAPI application
├── requirements.txt                 # Full Python dependencies
├── requirements_simple.txt          # Minimal dependencies (no HF/ChromaDB)
├── README.md                        # This file
├── chromadb/                        # ChromaDB module
│   ├── chroma_client.py             # ChromaDB client (optional)
│   └── CHROMADB_SETUP.md            # ChromaDB setup guide
├── huggingface/                     # HuggingFace module
│   └── HUGGINGFACE_SETUP.md         # Hugging Face setup (optional)
├── cloudflare/                      # Cloudflare Workers module
│   ├── wrangler.toml                # Cloudflare Workers configuration
│   └── CLOUDFLARE_WORKERS_SETUP.md  # Cloudflare Workers setup guide
└── playwright_docs/                 # Playwright documentation
    └── BROWSER_PARSING_SETUP.md     # Browser setup guide
```

## Features

### System Endpoints
- **GET /health** - Health check endpoint
- **GET /** - Service information

## Installation and Setup

### Local Development

#### Вариант 1: Автоматический запуск (рекомендуется)

```bash
# Просто запустите скрипт - он сам создаст venv, установит зависимости и запустит сервер
./start_server.sh
```

#### Вариант 2: Ручная установка

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
# For simplified version (no external services)
pip install -r requirements_simple.txt

# Or for full version (with HuggingFace/ChromaDB)
pip install -r requirements.txt
```

3. Run the server:
```bash
# Используйте Python из виртуального окружения!
./venv/bin/python -m uvicorn main:app --reload

# Или если venv активирован:
uvicorn main:app --reload
```

**⚠️ ВАЖНО:** Всегда запускайте сервер из виртуального окружения! Не используйте системный Python.

The application will be available at: http://localhost:8000

### API Documentation

After starting the server, automatic API documentation is available:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment to Cloudflare Workers

### Prerequisites

1. Install required tools:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pywrangler
uv tool install workers-py

# Or use traditional Wrangler
npm install -g wrangler
```

2. Authenticate with Cloudflare:
```bash
uv run pywrangler login
# or
wrangler login
```

### Setting Secrets

**Required secrets (if using external services):**

```bash
# Hugging Face token (if using HuggingFace API)
wrangler secret put HUGGINGFACE_API_TOKEN

# ChromaDB (if using ChromaDB Cloud)
wrangler secret put CHROMA_API_URL
wrangler secret put CHROMA_API_KEY
```

**Optional secrets:**
```bash
wrangler secret put HUGGINGFACE_MODEL
wrangler secret put CHROMA_COLLECTION_NAME
wrangler secret put EMBEDDING_MODEL
```

**Important:** For Cloudflare Workers, ChromaDB requires an external instance (ChromaDB Cloud). Local file system is not available in Workers.

### Deployment

1. Deploy to production:
```bash
# Using pywrangler (recommended)
uv run pywrangler deploy

# Or using Wrangler
wrangler deploy
```

2. Deploy to staging:
```bash
wrangler deploy --env staging
```

3. View logs:
```bash
wrangler tail
```

**Complete setup guide:** See [cloudflare/CLOUDFLARE_WORKERS_SETUP.md](cloudflare/CLOUDFLARE_WORKERS_SETUP.md)

## Environment Variables

### Optional (for external services)

**Hugging Face:**
- `HUGGINGFACE_API_TOKEN` - Token for accessing Hugging Face API
- `HUGGINGFACE_API_URL` - Hugging Face API URL (default: https://api-inference.huggingface.co/models)
- `HUGGINGFACE_MODEL` - Default model name

**ChromaDB (Local Development):**
- `CHROMA_HOST` - ChromaDB server host (default: localhost)
- `CHROMA_PORT` - ChromaDB server port (default: 8000)
- `CHROMA_COLLECTION_NAME` - Collection name (default: gaado_documents)
- `EMBEDDING_MODEL` - Embedding model name

**ChromaDB (Cloudflare Workers / Production):**
- `CHROMA_API_URL` - ChromaDB Cloud or external server URL
- `CHROMA_API_KEY` - API key for ChromaDB Cloud

## Additional Documentation

- [Cloudflare Workers Setup Guide](cloudflare/CLOUDFLARE_WORKERS_SETUP.md) - Complete guide for preparing and deploying to Cloudflare Workers
- [Hugging Face Setup](huggingface/HUGGINGFACE_SETUP.md) - Guide for setting up Hugging Face models (optional)
- [ChromaDB Setup](chromadb/CHROMADB_SETUP.md) - Instructions for deploying ChromaDB in different environments (optional)

## Next Steps

1. ✅ Basic FastAPI application setup
2. ✅ Local development environment
3. 📋 Prepare for Cloudflare Workers deployment (see [cloudflare/CLOUDFLARE_WORKERS_SETUP.md](cloudflare/CLOUDFLARE_WORKERS_SETUP.md))
4. 📋 Set up external services (HuggingFace/ChromaDB) if needed
5. 📋 Deploy to Cloudflare Workers

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements_simple.txt
   ```

2. **Run locally:**
   ```bash
   uvicorn main:app --reload
   ```

3. **Test API:**
   - Open http://localhost:8000/docs
   - Or use curl commands

4. **Prepare for deployment:**
   - Follow [cloudflare/CLOUDFLARE_WORKERS_SETUP.md](cloudflare/CLOUDFLARE_WORKERS_SETUP.md)
   - Set up secrets
   - Deploy with `pywrangler deploy`

## Support

If you encounter issues:

1. Check logs: `wrangler tail` (for Workers) or console (locally)
2. Verify configuration: Review `cloudflare/wrangler.toml` and secrets
3. Test locally: Use `pywrangler dev` to simulate Workers environment
4. Review documentation in corresponding .md files
5. Check Cloudflare Workers status and documentation
