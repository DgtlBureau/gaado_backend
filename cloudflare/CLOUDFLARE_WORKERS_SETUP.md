# Cloudflare Workers Setup Guide

Complete guide for preparing and deploying the Gaado Backend API to Cloudflare Workers.

## Prerequisites

### 1. Required Tools

Install the following tools on your system:

```bash
# Install Node.js and npm (if not already installed)
# Visit: https://nodejs.org/

# Install Python 3.11+ (Cloudflare Workers requires Python 3.11+)
python3 --version  # Should be 3.11 or higher

# Install uv (Python package installer)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pywrangler (Cloudflare Workers Python CLI)
uv tool install workers-py
```

### 2. Cloudflare Account

1. Sign up for a Cloudflare account: https://dash.cloudflare.com/sign-up
2. Log in to your Cloudflare dashboard

### 3. Authentication

Authenticate with Cloudflare:

```bash
# Using Wrangler (traditional method)
npm install -g wrangler
wrangler login

# Or using pywrangler
uv run pywrangler login
```

## Project Structure Requirements

Your project should have the following structure:

```
gaado_backend/
├── main.py              # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── wrangler.toml        # Cloudflare Workers configuration
└── .gitignore          # Git ignore file
```

## Configuration Files

### 1. wrangler.toml

Ensure your `wrangler.toml` is properly configured:

```toml
name = "gaado-backend"
main = "main.py"
compatibility_date = "2024-01-01"
compatibility_flags = ["python_workers"]

[env.production]
name = "gaado-backend"

[env.staging]
name = "gaado-backend-staging"
```

### 2. requirements.txt

Your `requirements.txt` should include only compatible packages:

```txt
fastapi==0.104.1
pydantic==2.5.0
httpx==0.25.2
python-dotenv==1.0.0
```

**Important Notes:**
- Some packages may not be compatible with Cloudflare Workers
- ChromaDB and sentence-transformers require external services (ChromaDB Cloud)
- **Playwright НЕ РАБОТАЕТ на Cloudflare Workers** - используйте внешний Playwright сервис (см. раздел ниже)
- Test your dependencies locally before deploying

### 3. Playwright на Cloudflare Workers

**⚠️ ВАЖНО:** Playwright не может работать напрямую на Cloudflare Workers из-за ограничений среды выполнения.

**Решение:** Используйте внешний Playwright сервис:

1. **Разверните Playwright Worker на отдельном сервере** (VPS, Railway, Render и т.д.)
2. **Настройте переменную окружения:**
   ```bash
   wrangler secret put PLAYWRIGHT_SERVICE_URL
   # Введите URL вашего Playwright сервиса, например: https://playwright-worker.example.com
   ```
3. **Код автоматически будет использовать внешний сервис** если `PLAYWRIGHT_SERVICE_URL` установлен

Подробнее см. [PLAYWRIGHT_SETUP_RU.md](../PLAYWRIGHT_SETUP_RU.md)

## Code Compatibility

### FastAPI Application

Your FastAPI app should be structured to work with Cloudflare Workers:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "ok"}
```

### Important Limitations

1. **No File System Access**: Workers cannot access local file system
   - Use external storage (ChromaDB Cloud, databases, etc.)
   - Don't rely on local file operations

2. **Execution Time Limits**:
   - Free plan: 10 seconds CPU time per request
   - Paid plans: Up to 30 seconds CPU time
   - Consider using background tasks for long operations

3. **Memory Limits**:
   - Free plan: 128 MB
   - Paid plans: Up to 512 MB

4. **Package Size**:
   - Keep dependencies minimal
   - Large packages may cause deployment issues

## Environment Variables and Secrets

### Setting Secrets

Use Wrangler CLI to set secrets:

```bash
# Required secrets
wrangler secret put HUGGINGFACE_API_TOKEN
# Enter your Hugging Face API token when prompted

# For ChromaDB (required for Workers)
wrangler secret put CHROMA_API_URL
wrangler secret put CHROMA_API_KEY

# Optional secrets
wrangler secret put HUGGINGFACE_MODEL
wrangler secret put CHROMA_COLLECTION_NAME
wrangler secret put EMBEDDING_MODEL
```

### Accessing Secrets in Code

Secrets are available as environment variables:

```python
import os

api_token = os.getenv("HUGGINGFACE_API_TOKEN")
```

## Deployment Steps

### Method 1: Using pywrangler (Recommended)

```bash
# 1. Navigate to project directory
cd /path/to/gaado_backend

# 2. Install dependencies locally (for testing)
uv pip install -r requirements.txt

# 3. Test locally
uv run pywrangler dev

# 4. Deploy to Cloudflare Workers
uv run pywrangler deploy
```

### Method 2: Using Wrangler (Traditional)

```bash
# 1. Ensure wrangler.toml is configured
# 2. Set all required secrets
wrangler secret put HUGGINGFACE_API_TOKEN
# ... (set other secrets)

# 3. Deploy
wrangler deploy

# 4. Deploy to staging
wrangler deploy --env staging
```

## Pre-Deployment Checklist

Before deploying, ensure:

- [ ] Python 3.11+ is being used
- [ ] All dependencies in `requirements.txt` are compatible
- [ ] No file system operations in code
- [ ] All secrets are set via `wrangler secret put`
- [ ] Code tested locally with `pywrangler dev`
- [ ] External services (ChromaDB Cloud) are configured
- [ ] API endpoints are tested locally
- [ ] Error handling is implemented
- [ ] Timeout handling is configured

## Testing Deployment

### 1. Health Check

```bash
curl https://your-worker.workers.dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "storage_count": 0
}
```

### 2. Test API Endpoints

```bash
# Test process endpoint
curl -X POST "https://your-worker.workers.dev/process" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message", "metadata": {"test": true}}'
```

### 3. View Logs

```bash
# Real-time logs
wrangler tail

# Or with pywrangler
uv run pywrangler tail
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Check that all packages are in `requirements.txt`
   - Verify package compatibility with Python 3.11+
   - Some packages may not work in Workers environment

2. **Timeout Errors**
   - Reduce processing time
   - Use lighter models
   - Consider caching results

3. **Memory Errors**
   - Reduce package size
   - Optimize data structures
   - Use external storage for large data

4. **Secret Not Found**
   - Verify secrets are set: `wrangler secret list`
   - Re-set secrets if needed
   - Check environment variable names match

5. **ChromaDB Connection Issues**
   - Verify ChromaDB Cloud credentials
   - Check network connectivity
   - Ensure ChromaDB instance is running

### Debugging Tips

1. **Local Testing**: Always test with `pywrangler dev` before deploying
2. **Check Logs**: Use `wrangler tail` to see real-time errors
3. **Verify Secrets**: Use `wrangler secret list` to confirm secrets
4. **Test Endpoints**: Use curl or Postman to test API endpoints
5. **Check Compatibility**: Review Cloudflare Workers Python documentation

## Performance Optimization

1. **Minimize Dependencies**: Only include necessary packages
2. **Use Caching**: Cache frequently accessed data
3. **Optimize Models**: Use lighter, faster models
4. **Async Operations**: Use async/await for I/O operations
5. **External Storage**: Use external databases for large data

## Monitoring

### View Metrics

1. Go to Cloudflare Dashboard
2. Navigate to Workers & Pages
3. Select your worker
4. View metrics, logs, and analytics

### Set Up Alerts

1. Configure alerts in Cloudflare Dashboard
2. Set up monitoring for errors and timeouts
3. Track API usage and performance

## Next Steps

After successful deployment:

1. ✅ Set up custom domain (optional)
2. ✅ Configure rate limiting
3. ✅ Set up monitoring and alerts
4. ✅ Implement authentication/authorization
5. ✅ Optimize performance
6. ✅ Set up CI/CD pipeline

## Resources

- [Cloudflare Workers Python Documentation](https://developers.cloudflare.com/workers/languages/python/)
- [FastAPI on Cloudflare Workers](https://developers.cloudflare.com/workers/languages/python/packages/fastapi/)
- [Wrangler CLI Documentation](https://developers.cloudflare.com/workers/wrangler/)
- [Cloudflare Workers Limits](https://developers.cloudflare.com/workers/platform/limits/)

## Support

If you encounter issues:

1. Check Cloudflare Workers documentation
2. Review error logs: `wrangler tail`
3. Test locally: `pywrangler dev`
4. Verify configuration: `wrangler.toml` and secrets
5. Check Cloudflare status page

