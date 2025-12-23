"""
FastAPI application for processing scraped data
Simplified version without HuggingFace and ChromaDB dependencies
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import os
from datetime import datetime
from facebook.facebook_client import FacebookScraperClient
from huggingface.huggingface_client import HuggingFaceClient

# Настройка логирования - DEBUG для отладки
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
# Включаем DEBUG для facebook_client
logging.getLogger('facebook_client').setLevel(logging.DEBUG)

app = FastAPI(
    title="Gaado Backend API",
    description="API for processing scraped data (simplified version)",
    version="1.0.0"
)


def get_c_user_from_cookies() -> str:
    """
    Извлекает значение c_user из файла facebook/cookies.txt
    
    Returns:
        Значение c_user или "none" если не найдено
    """
    cookies_file = os.getenv("FACEBOOK_COOKIES_FILE", "facebook/cookies.txt")
    
    if not os.path.exists(cookies_file):
        return "none"
    
    try:
        with open(cookies_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('\t')
                    if len(parts) >= 7 and parts[5] == 'c_user':
                        return parts[6] if len(parts) > 6 else "none"
    except Exception as e:
        logger.error(f"Ошибка при чтении cookies: {e}")
        return "none"
    
    return "none"


def get_facebook_client() -> FacebookScraperClient:
    """
    Создает экземпляр FacebookScraperClient с cookies из переменной окружения или файла
    
    Проверяет:
    1. Переменную окружения FACEBOOK_COOKIES_FILE (путь к файлу cookies)
    2. Файл facebook/cookies.txt в папке facebook
    3. Переменную окружения FACEBOOK_COOKIES (прямая строка cookies)
    
    Returns:
        FacebookScraperClient с настроенными cookies (если найдены)
    """
    cookies_file = os.getenv("FACEBOOK_COOKIES_FILE")
    
    # Проверяем переменную окружения с путем к файлу
    if cookies_file and os.path.exists(cookies_file):
        logger.info(f"Используются cookies из файла: {cookies_file}")
        return FacebookScraperClient(cookies=cookies_file)
    
    # Проверяем файл cookies.txt в папке facebook
    if os.path.exists("facebook/cookies.txt"):
        logger.info("Используются cookies из файла: facebook/cookies.txt")
        return FacebookScraperClient(cookies="facebook/cookies.txt")
    
    # Если cookies не найдены, создаем клиент без них
    logger.warning("Cookies не найдены. Facebook scraper может работать с ограничениями.")
    logger.info("Для улучшения работы создайте файл facebook/cookies.txt или установите FACEBOOK_COOKIES_FILE")
    return FacebookScraperClient()


class ScrapedData(BaseModel):
    """Model for incoming scraped data"""
    text: str = Field(..., description="Text content to process")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata about the scraped content"
    )


class DocumentAdd(BaseModel):
    """Model for adding documents"""
    texts: List[str] = Field(..., description="List of texts to add")
    metadatas: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional metadata for each document"
    )
    ids: Optional[List[str]] = Field(
        default=None,
        description="Optional IDs for documents"
    )


class SearchQuery(BaseModel):
    """Model for searching documents"""
    query_text: str = Field(..., description="Search query text")
    n_results: int = Field(default=5, ge=1, le=100, description="Number of results to return")
    filter_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filter"
    )


class FacebookPageRequest(BaseModel):
    """Model for Facebook page data request"""
    page_username: str = Field(..., description="Facebook page username (e.g., 'premierbankso')")


class HTMLParseRequest(BaseModel):
    """Model for HTML parsing request"""
    html_content: str = Field(..., description="HTML content containing Facebook comments")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Maximum number of comments to extract")


class URLParseRequest(BaseModel):
    """Model for URL parsing request"""
    url: str = Field(..., description="URL of Facebook page with comments")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Maximum number of comments to extract")
    use_browser: Optional[bool] = Field(default=False, description="Use browser rendering (Playwright) for JavaScript-heavy pages")
    wait_time: Optional[int] = Field(default=5, ge=1, le=30, description="Wait time in seconds for page to load (only for browser mode)")


class HuggingFaceChatRequest(BaseModel):
    """Model for Hugging Face chat request"""
    prompt: str = Field(..., description="Text prompt for the AI model")
    model: Optional[str] = Field(default=None, description="Model name (optional, uses default if not specified)")


# Простое хранилище в памяти (для демонстрации)
in_memory_storage: Dict[str, Dict[str, Any]] = {}

# Хранилище результатов скраппинга Facebook
facebook_scraping_results: Dict[str, Dict[str, Any]] = {}

# Хранилище статусов выполнения скраппинга
scraping_status: Dict[str, Dict[str, Any]] = {}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Main page with service information"""
    storage_count = len(in_memory_storage)
    c_user = get_c_user_from_cookies()
    # Получаем последний результат скраппинга
    last_scraping_result = None
    if facebook_scraping_results:
        # Берем последний результат
        last_key = max(facebook_scraping_results.keys(), key=lambda k: facebook_scraping_results[k].get('fetched_at', ''))
        last_scraping_result = facebook_scraping_results[last_key]
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gaado Backend API</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 800px;
                width: 100%;
                padding: 40px;
            }
            h1 {
                color: #667eea;
                font-size: 2.5em;
                margin-bottom: 10px;
                text-align: center;
            }
            .subtitle {
                color: #666;
                text-align: center;
                margin-bottom: 30px;
                font-size: 1.1em;
            }
            .status {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9em;
                margin-bottom: 30px;
            }
            .info-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .info-card {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }
            .info-card h3 {
                color: #333;
                font-size: 0.9em;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .info-card p {
                color: #667eea;
                font-size: 1.5em;
                font-weight: bold;
            }
            .links {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-top: 30px;
            }
            .link {
                display: inline-block;
                padding: 12px 24px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 8px;
                transition: all 0.3s ease;
                font-weight: 500;
            }
            .link:hover {
                background: #5568d3;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .link.secondary {
                background: #6b7280;
            }
            .link.secondary:hover {
                background: #4b5563;
            }
            .endpoints {
                margin-top: 30px;
                padding-top: 30px;
                border-top: 2px solid #e5e7eb;
            }
            .endpoints h2 {
                color: #333;
                margin-bottom: 20px;
                font-size: 1.5em;
            }
            .endpoint {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
            }
            .method {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                margin-right: 10px;
                font-size: 0.8em;
            }
            .method.get {
                background: #10b981;
                color: white;
            }
            .method.post {
                background: #3b82f6;
                color: white;
            }
            .method.delete {
                background: #ef4444;
                color: white;
            }
            .scraper-section {
                margin-top: 30px;
                padding: 25px;
                background: #f8f9fa;
                border-radius: 10px;
                border: 2px solid #667eea;
            }
            .scraper-section h2 {
                color: #667eea;
                margin-bottom: 20px;
                font-size: 1.5em;
            }
            .scraper-form {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                align-items: flex-start;
            }
            .scraper-form input,
            .scraper-form textarea {
                flex: 1;
                padding: 12px;
                border: 2px solid #e5e7eb;
                border-radius: 8px;
                font-size: 1em;
                font-family: inherit;
            }
            .scraper-form input:focus,
            .scraper-form textarea:focus {
                outline: none;
                border-color: #667eea;
            }
            .scraper-form textarea {
                min-height: 80px;
                resize: vertical;
            }
            .scraper-form button {
                padding: 12px 30px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 1em;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .scraper-form button:hover {
                background: #5568d3;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            }
            .scraper-form button:disabled {
                background: #9ca3af;
                cursor: not-allowed;
                transform: none;
            }
            .result-container {
                margin-top: 20px;
                padding: 20px;
                background: white;
                border-radius: 10px;
                border-left: 4px solid #10b981;
                display: none;
            }
            .result-container.show {
                display: block;
            }
            .result-container.error {
                border-left-color: #ef4444;
            }
            .result-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }
            .result-header h3 {
                color: #333;
                margin: 0;
            }
            .result-stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat-item {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-item .stat-label {
                font-size: 0.85em;
                color: #666;
                margin-bottom: 5px;
            }
            .stat-item .stat-value {
                font-size: 1.5em;
                font-weight: bold;
                color: #667eea;
            }
            .post-content {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .reactions-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                gap: 10px;
                margin-bottom: 15px;
            }
            .reaction-item {
                background: white;
                padding: 10px;
                border-radius: 6px;
                text-align: center;
                border: 1px solid #e5e7eb;
            }
            .reaction-item .reaction-type {
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }
            .reaction-item .reaction-count {
                font-size: 1.2em;
                color: #333;
            }
            .comments-list {
                max-height: 300px;
                overflow-y: auto;
                margin-top: 15px;
            }
            .comment-item {
                background: white;
                padding: 12px;
                border-radius: 6px;
                margin-bottom: 10px;
                border-left: 3px solid #667eea;
            }
            .comment-author {
                font-weight: bold;
                color: #667eea;
                margin-bottom: 5px;
            }
            .comment-text {
                color: #333;
                margin-bottom: 5px;
            }
            .comment-meta {
                font-size: 0.85em;
                color: #666;
            }
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
                color: #667eea;
            }
            .loading.show {
                display: block;
            }
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
        <script>
            // Безопасное форматирование даты (определяем глобально)
            function formatDate(dateValue) {
                if (!dateValue) return 'Дата не указана';
                try {
                    const date = new Date(dateValue);
                    if (isNaN(date.getTime())) return 'Неверная дата';
                    return date.toLocaleString('ru-RU');
                } catch (e) {
                    console.error('Ошибка форматирования даты:', e, dateValue);
                    return 'Ошибка даты';
                }
            }
            
            async function scrapeFacebook() {
                const username = document.getElementById('fb-username').value.trim();
                const button = document.getElementById('scrape-btn');
                const loading = document.getElementById('loading');
                const resultContainer = document.getElementById('result-container');
                
                if (!username) {
                    alert('Пожалуйста, введите username страницы Facebook');
                    return;
                }
                
                // Показываем загрузку
                button.disabled = true;
                loading.classList.add('show');
                resultContainer.classList.remove('show');
                
                try {
                    const response = await fetch('/facebook/scrape', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ page_username: username })
                    });
                    
                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error('HTTP Error:', response.status, errorText);
                        showError(`Ошибка сервера (${response.status}): ${errorText}`);
                        return;
                    }
                    
                    const data = await response.json();
                    console.log('Response data:', data);
                    
                    if (data.success) {
                        displayResult(data.data);
                    } else {
                        showError(data.error || 'Произошла ошибка при скраппинге');
                    }
                } catch (error) {
                    console.error('Request error:', error);
                    showError('Ошибка соединения: ' + error.message);
                } finally {
                    button.disabled = false;
                    loading.classList.remove('show');
                }
            }
            
            function displayResult(data) {
                const container = document.getElementById('result-container');
                const pageInfo = data.page_info || {};
                const post = data.post || {};
                const reactions = data.reactions || {};
                const comments = data.comments || {};
                
                console.log('Displaying result:', { pageInfo, post, reactions, comments });
                
                let html = `
                    <div class="result-header">
                        <h3>📄 ${pageInfo.name || pageInfo.username || 'Страница'}</h3>
                        <span style="color: #666; font-size: 0.9em;">${data.fetched_at ? formatDate(data.fetched_at) : 'Только что'}</span>
                    </div>
                `;
                
                if (post.text) {
                    html += `
                        <div class="post-content">${escapeHtml(post.text)}</div>
                        <div class="result-stats">
                            <div class="stat-item">
                                <div class="stat-label">Лайки</div>
                                <div class="stat-value">${post.likes || 0}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">Комментарии</div>
                                <div class="stat-value">${comments.total_count || 0}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">Репосты</div>
                                <div class="stat-value">${post.shares || 0}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">Реакций всего</div>
                                <div class="stat-value">${reactions.total_reactions || 0}</div>
                            </div>
                        </div>
                    `;
                    
                    if (reactions.reactions_by_type && Object.keys(reactions.reactions_by_type).length > 0) {
                        html += '<h4 style="margin: 15px 0 10px 0; color: #333;">Реакции по типам:</h4><div class="reactions-grid">';
                        for (const [type, count] of Object.entries(reactions.reactions_by_type)) {
                            if (count > 0) {
                                html += `
                                    <div class="reaction-item">
                                        <div class="reaction-type">${type}</div>
                                        <div class="reaction-count">${count}</div>
                                    </div>
                                `;
                            }
                        }
                        html += '</div>';
                    }
                    
                    if (comments.comments && comments.comments.length > 0) {
                        html += '<h4 style="margin: 20px 0 10px 0; color: #333;">Комментарии:</h4><div class="comments-list">';
                        comments.comments.slice(0, 10).forEach(comment => {
                            let commentTime = '';
                            if (comment.time) {
                                try {
                                    const date = new Date(comment.time);
                                    if (!isNaN(date.getTime())) {
                                        commentTime = date.toLocaleString('ru-RU');
                                    }
                                } catch (e) {
                                    // Игнорируем ошибки парсинга даты
                                }
                            }
                            html += `
                                <div class="comment-item">
                                    <div class="comment-author">${escapeHtml(comment.author || 'Аноним')}</div>
                                    <div class="comment-text">${escapeHtml(comment.text || '')}</div>
                                    <div class="comment-meta">❤️ ${comment.likes || 0}${commentTime ? ' • ' + commentTime : ''}</div>
                                </div>
                            `;
                        });
                        if (comments.total_count > 10) {
                            html += `<div style="text-align: center; color: #666; margin-top: 10px;">... и еще ${comments.total_count - 10} комментариев</div>`;
                        }
                        html += '</div>';
                    }
                } else if (data.error) {
                    html += `<p style="color: #ef4444;">${escapeHtml(data.error)}</p>`;
                }
                
                container.innerHTML = html;
                container.classList.add('show');
                container.classList.remove('error');
            }
            
            function showError(message) {
                const container = document.getElementById('result-container');
                container.innerHTML = `
                    <div class="result-header">
                        <h3 style="color: #ef4444;">❌ Ошибка</h3>
                    </div>
                    <p style="color: #ef4444;">${escapeHtml(message)}</p>
                `;
                container.classList.add('show', 'error');
            }
            
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
            
            async function chatHuggingFace() {
                const prompt = document.getElementById('hf-prompt').value.trim();
                const button = document.getElementById('hf-chat-btn');
                const loading = document.getElementById('hf-loading');
                const resultContainer = document.getElementById('hf-result-container');
                
                if (!prompt) {
                    alert('Пожалуйста, введите запрос');
                    return;
                }
                
                // Показываем загрузку
                button.disabled = true;
                loading.classList.add('show');
                resultContainer.classList.remove('show');
                
                try {
                    const response = await fetch('/huggingface/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ prompt: prompt })
                    });
                    
                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error('HTTP Error:', response.status, errorText);
                        showHfError(`Ошибка сервера (${response.status}): ${errorText}`);
                        return;
                    }
                    
                    const data = await response.json();
                    console.log('Response data:', data);
                    
                    if (data.success) {
                        displayHfResult(data.response, prompt);
                    } else {
                        showHfError(data.error || 'Произошла ошибка при обработке запроса');
                    }
                } catch (error) {
                    console.error('Request error:', error);
                    showHfError('Ошибка соединения: ' + error.message);
                } finally {
                    button.disabled = false;
                    loading.classList.remove('show');
                }
            }
            
            function displayHfResult(response, prompt) {
                const container = document.getElementById('hf-result-container');
                
                let html = `
                    <div class="result-header">
                        <h3>🤖 Ответ от AI</h3>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #667eea;">Ваш запрос:</strong>
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; margin-top: 5px; white-space: pre-wrap;">${escapeHtml(prompt)}</div>
                    </div>
                    <div>
                        <strong style="color: #667eea;">Ответ:</strong>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 5px; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(response)}</div>
                    </div>
                `;
                
                container.innerHTML = html;
                container.classList.add('show');
                container.classList.remove('error');
            }
            
            function showHfError(message) {
                const container = document.getElementById('hf-result-container');
                container.innerHTML = `
                    <div class="result-header">
                        <h3 style="color: #ef4444;">❌ Ошибка</h3>
                    </div>
                    <p style="color: #ef4444;">${escapeHtml(message)}</p>
                `;
                container.classList.add('show', 'error');
            }
            
            // Обработка Enter в поле ввода
            document.addEventListener('DOMContentLoaded', function() {
                const input = document.getElementById('fb-username');
                if (input) {
                    input.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            scrapeFacebook();
                        }
                    });
                }
            });
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Gaado Backend API</h1>
            <p class="subtitle">FastAPI Application for Processing Scraped Data</p>
            <div style="text-align: center;">
                <span class="status">● Online</span>
            </div>
            
            <div class="info-grid">
                <div class="info-card">
                    <h3>Version</h3>
                    <p>1.0.0</p>
                </div>
                <div class="info-card">
                    <h3>Mode</h3>
                    <p>Simplified</p>
                </div>
                <div class="info-card">
                    <h3>Storage</h3>
                    <p>""" + str(storage_count) + """ docs</p>
                </div>
                <div class="info-card">
                    <h3>Cookies</h3>
                    <p>""" + (c_user if c_user != "none" else "none") + """</p>
                </div>
            </div>
            
            <div class="scraper-section">
                <h2>📱 Facebook Scraper</h2>
                <div class="scraper-form">
                    <input 
                        type="text" 
                        id="fb-username" 
                        placeholder="Введите username страницы (например: premierbankso)" 
                        value="premierbankso"
                    />
                    <button id="scrape-btn" onclick="scrapeFacebook()">Скрапить</button>
                </div>
                <div id="loading" class="loading">
                    <div class="spinner"></div>
                    <p>Загрузка данных...</p>
                </div>
                <div id="result-container" class="result-container"></div>
            </div>
            
            <div class="scraper-section">
                <h2>🤖 Hugging Face Chat</h2>
                <div class="scraper-form">
                    <textarea 
                        id="hf-prompt" 
                        placeholder="Введите ваш запрос..."
                    >What is the capital of France?</textarea>
                    <button id="hf-chat-btn" onclick="chatHuggingFace()">Отправить</button>
                </div>
                <div id="hf-loading" class="loading">
                    <div class="spinner"></div>
                    <p>Обработка запроса...</p>
                </div>
                <div id="hf-result-container" class="result-container"></div>
            </div>
            
            <div class="links">
                <a href="/docs" class="link">📚 API Documentation</a>
                <a href="/redoc" class="link secondary">📖 ReDoc</a>
                <a href="/health" class="link secondary">❤️ Health Check</a>
            </div>
            
            <div class="endpoints">
                <h2>Quick API Endpoints</h2>
                <div class="endpoint">
                    <span class="method get">GET</span> /health - Health check endpoint
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /huggingface/chat - Chat with Hugging Face AI
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /storage/add - Add documents to storage
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /storage/search - Search documents
                </div>
                <div class="endpoint">
                    <span class="method get">GET</span> /storage/list - List all documents
                </div>
                <div class="endpoint">
                    <span class="method delete">DELETE</span> /storage/delete - Delete documents
                </div>
                <div class="endpoint">
                    <span class="method get">GET</span> /facebook/page/{username} - Get Facebook page post data
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /facebook/page - Get Facebook page data (POST)
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /facebook/scrape - Scrape Facebook page
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /facebook/test - Test Facebook scraper
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /facebook/parse-html - Parse comments from HTML
                </div>
                <div class="endpoint">
                    <span class="method post">POST</span> /facebook/parse-url - Fetch and parse comments from URL
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "storage_count": len(in_memory_storage)
    }




@app.post("/storage/add")
async def add_documents(documents: DocumentAdd):
    """
    Add documents to in-memory storage
    
    Args:
        documents: Documents to add with optional metadata and IDs
        
    Returns:
        List of document IDs
    """
    import uuid
    
    ids = []
    for i, text in enumerate(documents.texts):
        doc_id = documents.ids[i] if documents.ids and i < len(documents.ids) else str(uuid.uuid4())
        metadata = documents.metadatas[i] if documents.metadatas and i < len(documents.metadatas) else {}
        
        in_memory_storage[doc_id] = {
            "text": text,
            "metadata": metadata,
            "created_at": datetime.now().isoformat()
        }
        ids.append(doc_id)
    
    return {
        "success": True,
        "ids": ids,
        "count": len(ids)
    }


@app.post("/storage/search")
async def search_documents(query: SearchQuery):
    """
    Search for documents in in-memory storage (simple text matching)
    
    Args:
        query: Search query with text and optional filters
        
    Returns:
        Search results with matching documents
    """
    results = []
    query_lower = query.query_text.lower()
    
    for doc_id, doc_data in in_memory_storage.items():
        # Простой поиск по тексту
        text_lower = doc_data["text"].lower()
        
        # Проверка фильтров метаданных
        if query.filter_metadata:
            matches_filter = all(
                doc_data.get("metadata", {}).get(key) == value
                for key, value in query.filter_metadata.items()
            )
            if not matches_filter:
                continue
        
        # Простой поиск по вхождению текста
        if query_lower in text_lower:
            results.append({
                "id": doc_id,
                "text": doc_data["text"],
                "metadata": doc_data.get("metadata", {}),
                "created_at": doc_data.get("created_at"),
                "match_score": text_lower.count(query_lower)  # Простой счетчик совпадений
            })
    
    # Сортировка по количеству совпадений и ограничение результатов
    results.sort(key=lambda x: x["match_score"], reverse=True)
    results = results[:query.n_results]
    
    return {
        "query": query.query_text,
        "results": results,
        "count": len(results)
    }


@app.get("/storage/info")
async def get_storage_info():
    """
    Get information about in-memory storage
    
    Returns:
        Storage information
    """
    return {
        "storage_type": "in-memory",
        "document_count": len(in_memory_storage),
        "total_chars": sum(len(doc["text"]) for doc in in_memory_storage.values()),
        "created_at": datetime.now().isoformat()
    }


@app.delete("/storage/delete")
async def delete_documents(ids: List[str]):
    """
    Delete documents from storage by IDs
    
    Args:
        ids: List of document IDs to delete
        
    Returns:
        Success status
    """
    deleted_count = 0
    for doc_id in ids:
        if doc_id in in_memory_storage:
            del in_memory_storage[doc_id]
            deleted_count += 1
    
    return {
        "success": True,
        "deleted_ids": ids,
        "deleted_count": deleted_count,
        "requested_count": len(ids)
    }


@app.get("/storage/list")
async def list_documents(limit: int = 10, offset: int = 0):
    """
    List all documents in storage
    
    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        
    Returns:
        List of documents
    """
    items = list(in_memory_storage.items())[offset:offset + limit]
    return {
        "documents": [
            {
                "id": doc_id,
                "text": doc_data["text"][:100] + "..." if len(doc_data["text"]) > 100 else doc_data["text"],
                "metadata": doc_data.get("metadata", {}),
                "created_at": doc_data.get("created_at")
            }
            for doc_id, doc_data in items
        ],
        "total": len(in_memory_storage),
        "limit": limit,
        "offset": offset
    }


@app.get("/facebook/page/{page_username}")
async def get_facebook_page_data(page_username: str):
    """
    Получить данные последнего поста со страницы Facebook
    
    Использует facebook-scraper для получения данных без необходимости в Access Token.
    Работает только с публичными страницами.
    
    Возвращает:
    - Информацию о странице
    - Последний пост
    - Реакции к посту (разбитые по типам: LIKE, LOVE, WOW, HAHA, SORRY, ANGER)
    - Все комментарии к посту
    
    Args:
        page_username: Username страницы Facebook (например, 'premierbankso')
    """
    try:
        client = get_facebook_client()
        data = await client.get_page_post_data(page_username)
        return {
            "success": True,
            "data": data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении данных Facebook: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.post("/facebook/page")
async def get_facebook_page_data_post(request: FacebookPageRequest):
    """
    Получить данные последнего поста со страницы Facebook (POST метод)
    
    Использует facebook-scraper для получения данных без необходимости в Access Token.
    Работает только с публичными страницами.
    
    Возвращает:
    - Информацию о странице
    - Последний пост
    - Реакции к посту (разбитые по типам)
    - Все комментарии к посту
    
    Args:
        request: Запрос с username страницы
    """
    try:
        client = get_facebook_client()
        data = await client.get_page_post_data(request.page_username)
        return {
            "success": True,
            "data": data
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении данных Facebook: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.get("/facebook/page/{page_username}/info")
async def get_facebook_page_info(page_username: str):
    """
    Получить базовую информацию о странице Facebook
    
    Использует facebook-scraper для получения данных без необходимости в Access Token.
    
    Args:
        page_username: Username страницы Facebook
    """
    try:
        client = get_facebook_client()
        page_info = await client.get_page_info(page_username)
        return {
            "success": True,
            "page_info": page_info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при получении информации о странице: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@app.post("/facebook/scrape")
async def scrape_facebook_page(request: FacebookPageRequest):
    """
    Эндпоинт для скраппинга Facebook страницы с главной страницы
    
    Использует facebook-scraper для получения данных без необходимости в Access Token.
    Сохраняет результат в памяти для отображения на главной странице.
    
    Args:
        request: Запрос с username страницы
    """
    import uuid
    
    try:
        client = get_facebook_client()
        data = await client.get_page_post_data(request.page_username)
        
        # Сохраняем результат в памяти
        result_id = str(uuid.uuid4())
        facebook_scraping_results[result_id] = {
            **data,
            "page_username": request.page_username,
            "fetched_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": data,
            "result_id": result_id
        }
    except ValueError as e:
        logger.error(f"Ошибка валидации при скраппинге: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Ошибка при скраппинге Facebook: {e}")
        return {
            "success": False,
            "error": f"Внутренняя ошибка: {str(e)}"
        }


@app.get("/facebook/test-simple/{page_username}")
async def test_facebook_scraper_simple(page_username: str):
    """
    ПРОСТОЙ тестовый эндпоинт для проверки базового подключения к Facebook
    Только получение постов, без дополнительных данных
    """
    try:
        logger.info(f"=== ТЕСТ: Простая проверка подключения для {page_username} ===")
        client = get_facebook_client()
        
        # ПРОСТОЙ ТЕСТ - только получение постов
        logger.info("Шаг 1: Получаем посты...")
        posts = await client._get_posts_async(page_username, pages=1)
        
        if not posts:
            return {
                "success": False,
                "error": "Посты не найдены",
                "message": f"Страница {page_username} не вернула посты. Проверьте правильность username."
            }
        
        # Возвращаем только первый пост для проверки
        first_post = posts[0]
        return {
            "success": True,
            "message": f"✅ Подключение работает! Найдено {len(posts)} постов",
            "post_count": len(posts),
            "first_post": {
                "post_id": first_post.get("post_id", "N/A"),
                "text_preview": (first_post.get("text", "") or first_post.get("post_text", ""))[:100],
                "has_text": bool(first_post.get("text") or first_post.get("post_text")),
                "keys": list(first_post.keys())
            }
        }
    except AssertionError as e:
        logger.error(f"AssertionError: {e}")
        return {
            "success": False,
            "error": "AssertionError",
            "message": f"Не удалось извлечь посты. Возможные причины: страница недоступна, приватная или требует авторизации. Ошибка: {str(e)}",
            "details": str(e)
        }
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {type(e).__name__}: {e}", exc_info=True)
        import traceback
        return {
            "success": False,
            "error": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }


@app.post("/facebook/parse-html")
async def parse_comments_from_html(request: HTMLParseRequest):
    """
    Парсинг комментариев напрямую из HTML-структуры Facebook
    
    Этот эндпоинт позволяет извлечь комментарии из HTML-кода страницы Facebook,
    когда стандартный скраппер не работает из-за изменений в структуре Facebook.
    
    Args:
        request: Запрос с HTML-контентом и опциональным лимитом комментариев
        
    Returns:
        Список извлеченных комментариев с авторами, текстом, временем и лайками
    """
    try:
        client = get_facebook_client()
        result = client.parse_comments_from_html(request.html_content, limit=request.limit)
        
        return {
            "success": True,
            "data": result,
            "parsed_at": datetime.now().isoformat()
        }
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"BeautifulSoup не установлен. Установите: pip install beautifulsoup4"
        )
    except Exception as e:
        logger.error(f"Ошибка при парсинге HTML: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при парсинге HTML: {str(e)}"
        )


@app.post("/facebook/parse-url")
async def fetch_and_parse_comments_from_url(request: URLParseRequest):
    """
    Загрузить HTML со страницы Facebook и распарсить комментарии
    
    Этот эндпоинт загружает HTML со страницы Facebook по URL и извлекает комментарии.
    Использует cookies из файла (если доступны) для доступа к странице.
    
    Если use_browser=True, использует Playwright для рендеринга JavaScript,
    что позволяет извлекать комментарии, загружаемые динамически.
    
    Результаты автоматически сохраняются в памяти и могут быть получены через /facebook/results/{result_id}
    
    Args:
        request: Запрос с URL страницы и опциональными параметрами
        
    Returns:
        Результат с данными, статусом выполнения и ID для отслеживания
    """
    import uuid
    
    try:
        result_id = str(uuid.uuid4())
        
        # Сохраняем статус начала
        scraping_status[result_id] = {
            "status": "started",
            "url": request.url,
            "started_at": datetime.now().isoformat(),
            "method": "browser" if request.use_browser else "http"
        }
        
        client = get_facebook_client()
        
        if request.use_browser:
            logger.info(f"Используем браузер для рендеринга JavaScript")
            result = await client.fetch_and_parse_comments_with_browser(
                request.url, 
                limit=request.limit,
                wait_time=request.wait_time
            )
        else:
            logger.info(f"Используем простой HTTP запрос")
            result = await client.fetch_and_parse_comments_from_url(request.url, limit=request.limit)
        
        # Обновляем статус
        scraping_status[result_id] = {
            "status": result.get("status", "completed"),
            "url": request.url,
            "started_at": result.get("started_at"),
            "completed_at": result.get("fetched_at"),
            "duration_seconds": result.get("duration_seconds"),
            "comments_count": result.get("total_count", 0),
            "method": "browser" if request.use_browser else "http",
            "success": result.get("success", True)
        }
        
        # Сохраняем результаты
        facebook_scraping_results[result_id] = {
            **result,
            "result_id": result_id,
            "saved_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": result,
            "result_id": result_id,
            "status": result.get("status", "completed"),
            "message": f"Скрапинг завершен. Найдено {result.get('total_count', 0)} комментариев.",
            "saved": True
        }
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        error_msg = "Необходимые библиотеки не установлены."
        if request.use_browser:
            error_msg += " Для браузера установите: pip install playwright && playwright install chromium"
        else:
            error_msg += " Установите: pip install httpx beautifulsoup4"
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )
    except ValueError as e:
        logger.error(f"Ошибка валидации: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке и парсинге URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке URL: {str(e)}"
        )


@app.get("/facebook/results/{result_id}")
async def get_scraping_result(result_id: str):
    """
    Получить результат скрапинга по ID
    
    Args:
        result_id: ID результата скрапинга
        
    Returns:
        Результат скрапинга с комментариями и метаданными
    """
    if result_id not in facebook_scraping_results:
        raise HTTPException(
            status_code=404,
            detail=f"Результат с ID {result_id} не найден"
        )
    
    result = facebook_scraping_results[result_id]
    status_info = scraping_status.get(result_id, {})
    
    return {
        "success": True,
        "result_id": result_id,
        "status": status_info.get("status", "unknown"),
        "data": result,
        "status_info": status_info
    }


@app.get("/facebook/status/{result_id}")
async def get_scraping_status(result_id: str):
    """
    Получить статус выполнения скрапинга
    
    Args:
        result_id: ID результата скрапинга
        
    Returns:
        Статус выполнения скрапинга
    """
    if result_id not in scraping_status:
        raise HTTPException(
            status_code=404,
            detail=f"Статус для ID {result_id} не найден"
        )
    
    status_info = scraping_status[result_id]
    
    # Проверяем, есть ли результаты
    has_results = result_id in facebook_scraping_results
    
    return {
        "result_id": result_id,
        "status": status_info.get("status", "unknown"),
        "url": status_info.get("url"),
        "started_at": status_info.get("started_at"),
        "completed_at": status_info.get("completed_at"),
        "duration_seconds": status_info.get("duration_seconds"),
        "comments_count": status_info.get("comments_count", 0),
        "has_results": has_results,
        "success": status_info.get("success", False)
    }


@app.get("/facebook/results")
async def list_scraping_results(limit: int = 10):
    """
    Получить список последних результатов скрапинга
    
    Args:
        limit: Максимальное количество результатов
        
    Returns:
        Список результатов скрапинга
    """
    results = []
    for result_id, result_data in list(facebook_scraping_results.items())[-limit:]:
        status_info = scraping_status.get(result_id, {})
        results.append({
            "result_id": result_id,
            "url": result_data.get("url"),
            "status": status_info.get("status", "unknown"),
            "comments_count": result_data.get("total_count", 0),
            "fetched_at": result_data.get("fetched_at"),
            "duration_seconds": result_data.get("duration_seconds")
        })
    
    return {
        "success": True,
        "total": len(facebook_scraping_results),
        "results": results
    }


@app.post("/huggingface/chat")
async def chat_with_huggingface(request: HuggingFaceChatRequest):
    """
    Эндпоинт для чата с Hugging Face моделью
    
    Args:
        request: Запрос с текстом промпта и опциональной моделью
        
    Returns:
        Ответ от AI модели
    """
    try:
        client = HuggingFaceClient()
        
        if not client.is_available():
            return {
                "success": False,
                "error": "HuggingFace клиент не доступен. Проверьте HF_API_KEY."
            }
        
        response = client.simple_chat(
            prompt=request.prompt,
            model=request.model
        )
        
        return {
            "success": True,
            "response": response,
            "model": request.model or client.default_model
        }
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса Hugging Face: {e}")
        return {
            "success": False,
            "error": f"Внутренняя ошибка: {str(e)}"
        }


@app.post("/facebook/test")
async def test_facebook_scraper(request: FacebookPageRequest):
    """
    Тестовый эндпоинт для проверки работы Facebook Scraper
    
    Выполняет полное тестирование всех функций скраппера:
    - Получение информации о странице
    - Получение последнего поста
    - Получение реакций
    - Получение комментариев
    
    Args:
        request: Запрос с username страницы для тестирования
    """
    test_username = request.page_username
    
    try:
        # Инициализация клиента
        client = get_facebook_client()
        
        # Получение информации о странице
        page_info = await client.get_page_info(test_username)
        
        # Получение последнего поста
        latest_post = await client.get_latest_post(test_username)
        
        if not latest_post:
            return {
                "success": False,
                "error": "На странице нет постов или страница недоступна",
                "page_info": page_info
            }
        
        # Получение реакций
        reactions = await client.get_post_reactions(latest_post)
        
        # Получение комментариев
        comments = await client.get_post_comments(latest_post)
        
        return {
            "success": True,
            "test_results": {
                "page_info": page_info,
                "latest_post": {
                    "post_id": latest_post.get("post_id"),
                    "text_preview": latest_post.get("text", "")[:100] + "..." if len(latest_post.get("text", "")) > 100 else latest_post.get("text", ""),
                    "likes": latest_post.get("likes", 0),
                    "comments": latest_post.get("comments", 0),
                    "shares": latest_post.get("shares", 0)
                },
                "reactions": {
                    "total_reactions": reactions.get("total_reactions", 0),
                    "reactions_by_type": reactions.get("reactions_by_type", {})
                },
                "comments": {
                    "total_count": comments.get("total_count", 0),
                    "sample_comments": comments.get("comments", [])[:3]  # Первые 3 комментария
                }
            },
            "message": "Все тесты пройдены успешно!"
        }
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return {
            "success": False,
            "error": f"Ошибка импорта: {e}. Установите библиотеку: pip install facebook-scraper"
        }
    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}")
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )
