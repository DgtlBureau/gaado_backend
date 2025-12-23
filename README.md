# Gaado Backend API

FastAPI application for processing scraped data. Prepared for deployment on Cloudflare Workers.

## Project Structure

```
gaado_backend/
├── main.py                          # Main FastAPI application
├── requirements.txt                 # Full Python dependencies
├── requirements_simple.txt          # Minimal dependencies (no HF/ChromaDB)
├── README.md                        # This file
├── facebook/                        # Facebook scraping module
│   ├── facebook_client.py           # Facebook Graph API client
│   ├── cookies.txt                  # Facebook cookies (optional)
│   ├── get_facebook_cookies.py      # Cookie extraction script
│   ├── FACEBOOK_SETUP.md            # Facebook setup guide
│   ├── COOKIES_SETUP.md             # Cookies setup guide
│   └── test_*.py                     # Facebook test scripts
├── chromadb/                        # ChromaDB module
│   ├── chroma_client.py             # ChromaDB client (optional)
│   └── CHROMADB_SETUP.md            # ChromaDB setup guide
├── huggingface/                     # HuggingFace module
│   └── HUGGINGFACE_SETUP.md         # Hugging Face setup (optional)
├── cloudflare/                      # Cloudflare Workers module
│   ├── wrangler.toml                # Cloudflare Workers configuration
│   └── CLOUDFLARE_WORKERS_SETUP.md  # Cloudflare Workers setup guide
└── playwright/                      # Playwright browser automation
    ├── test_browser_parsing.py      # Browser parsing tests
    └── BROWSER_PARSING_SETUP.md     # Browser setup guide
```

## Features

### Text Processing
- **POST /process** - Process text data with basic analysis (word count, character count, etc.)
- **POST /storage/add** - Add documents to in-memory storage
- **POST /storage/search** - Search documents in storage
- **GET /storage/info** - Get storage information
- **GET /storage/list** - List all documents
- **DELETE /storage/delete** - Delete documents by IDs

### Facebook Scraper API
- **GET /facebook/page/{username}** - Get latest post data from Facebook page (with reactions and comments)
- **POST /facebook/page** - Get Facebook page data (POST method)
- **GET /facebook/page/{username}/info** - Get basic page information
- **POST /facebook/scrape** - Scrape Facebook page (for web interface)
- **POST /facebook/test** - Test Facebook scraper functionality

See [facebook/FACEBOOK_SETUP.md](facebook/FACEBOOK_SETUP.md) for detailed setup instructions.

### System Endpoints
- **GET /health** - Health check endpoint
- **GET /** - Service information

## Installation and Setup

### Local Development

1. Create a virtual environment:
```bash
python -m venv venv
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
uvicorn main:app --reload
```

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

## API Usage

### Process Text

```bash
curl -X POST "http://localhost:8000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test message!",
    "metadata": {
      "source": "example.com",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  }'
```

With storage:
```bash
curl -X POST "http://localhost:8000/process?save_to_storage=true" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test message!",
    "metadata": {"source": "example.com"}
  }'
```

### Add Documents to Storage

```bash
curl -X POST "http://localhost:8000/storage/add" \
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

### Search Documents

```bash
curl -X POST "http://localhost:8000/storage/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "artificial intelligence",
    "n_results": 5
  }'
```

### Example Response

```json
{
  "success": true,
  "input_text": "Hello, this is a test message!",
  "metadata": {
    "source": "example.com",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "analysis": {
    "text_length": 30,
    "word_count": 6,
    "char_count": 30,
    "uppercase_count": 1,
    "digit_count": 0
  },
  "processed_at": "2024-01-01T00:00:00",
  "storage_id": "uuid-here",
  "saved_to_storage": true
}
```

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
