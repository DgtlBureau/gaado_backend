"""
FastAPI application for processing scraped data
Simplified version without ChromaDB dependencies
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from gemini.gemini_client import GeminiClient
from database.model_parser import ModelParser
from database.database import init_database, get_database
from database.database_api import add_raw_comment, add_processed_comment
from database.models import SaveProcessedCommentRequest
from comments import router as comments_router

# Load environment variables from .env file
load_dotenv()


# Configure logging - INFO level (suppress DEBUG logs from uvicorn/httptools)
# Explicitly set output to stderr (terminal)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True  # Переопределяем существующую конфигурацию
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gaado Backend API",
    description="API for processing scraped data (simplified version)",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)



# Include routers
app.include_router(comments_router)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on application startup"""
    try:
        # init_database() is synchronous and automatically connects via psycopg2 and initializes Supabase client
        init_database()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connections on shutdown"""


class GeminiChatRequest(BaseModel):
    """Model for Gemini chat request"""
    prompt: str = Field(..., description="Text prompt for the AI model")
    model: Optional[str] = Field(default=None, description="Model name (optional, uses default if not specified)")


# Database will be initialized on startup
# Access via get_database() function


@app.get("/", response_class=HTMLResponse)
async def root():
    """Main page with service information"""
    
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
            .navbar {
                background: white;
                padding: 15px 0;
                margin-bottom: 30px;
                border-bottom: 2px solid #e5e7eb;
            }
            .nav-links {
                display: flex;
                gap: 20px;
                justify-content: center;
            }
            .nav-link {
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
                padding: 8px 16px;
                border-radius: 6px;
                transition: all 0.3s ease;
            }
            .nav-link:hover {
                background: #f8f9fa;
            }
            .nav-link.active {
                background: #667eea;
                color: white;
            }
        </style>
        <script>
            // Безопасное форматирование даты
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
            
            async function chatGemini() {
                const prompt = document.getElementById('gemini-prompt').value.trim();
                const button = document.getElementById('gemini-chat-btn');
                const loading = document.getElementById('gemini-loading');
                const resultContainer = document.getElementById('gemini-result-container');
                
                if (!prompt) {
                    alert('Please enter a prompt');
                    return;
                }
                
                // Показываем загрузку
                button.disabled = true;
                loading.classList.add('show');
                resultContainer.classList.remove('show');
                
                try {
                    const response = await fetch('/gemini/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ prompt: prompt })
                    });
                    
                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error('HTTP Error:', response.status, errorText);
                        showGeminiError(`Ошибка сервера (${response.status}): ${errorText}`);
                        return;
                    }
                    
                    const data = await response.json();
                    console.log('Response data:', data);
                    
                    if (data.success) {
                        // Отображаем результат
                        displayGeminiResult(data.response, prompt, data.parsed_data);
                        
                        // Сохраняем в БД если есть parsed_data
                        if (data.parsed_data) {
                            await saveProcessedCommentToDatabase(data.parsed_data, prompt);
                        }
                    } else {
                        showGeminiError(data.error || 'Произошла ошибка при обработке запроса');
                    }
                } catch (error) {
                    console.error('Request error:', error);
                    showGeminiError('Ошибка соединения: ' + error.message);
                } finally {
                    button.disabled = false;
                    loading.classList.remove('show');
                }
            }
            
            async function saveProcessedCommentToDatabase(parsedData, somaliText) {
                // Генерируем временные ID для демонстрации (в реальном приложении они должны приходить из формы)
                const fbCommentId = 'gemini_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                const postId = 1; // Прикрепляем к реальному посту
                
                try {
                    const response = await fetch('/gemini/save', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            fb_comment_id: fbCommentId,
                            post_id: postId,
                            translation_en: parsedData.translation_en,
                            threat_level_slug: parsedData.threat_level_slug,
                            confidence_score: parsedData.confidence_score,
                            dialect: parsedData.dialect,
                            keywords: parsedData.keywords,
                            somali_text: somaliText || parsedData.somali_text
                        })
                    });
                    
                    const saveResult = await response.json();
                    
                    if (saveResult.success) {
                        console.log('Successfully saved to database:', saveResult);
                    } else {
                        console.warn('Failed to save to database:', saveResult.error);
                    }
                } catch (error) {
                    console.error('Error saving to database:', error);
                }
            }
            
            function displayGeminiResult(response, prompt) {
                const container = document.getElementById('gemini-result-container');
                
                let html = `
                    <div class="result-header">
                        <h3>🤖 Response from Gemini</h3>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <strong style="color: #667eea;">Request:</strong>
                        <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; margin-top: 5px; white-space: pre-wrap;">${escapeHtml(prompt)}</div>
                    </div>
                    <div>
                        <strong style="color: #667eea;">Response:</strong>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 5px; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(response)}</div>
                    </div>
                `;
                
                container.innerHTML = html;
                container.classList.add('show');
                container.classList.remove('error');
            }
            
            function showGeminiError(message) {
                const container = document.getElementById('gemini-result-container');
                container.innerHTML = `
                    <div class="result-header">
                        <h3 style="color: #ef4444;">❌ Ошибка</h3>
                    </div>
                    <p style="color: #ef4444;">${escapeHtml(message)}</p>
                `;
                container.classList.add('show', 'error');
            }
            
        </script>
    </head>
    <body>
        <div class="container">
            <nav class="navbar">
                <div class="nav-links">
                    <a href="/" class="nav-link active">Home</a>
                    <a href="/comments" class="nav-link">Feed</a>
                </div>
            </nav>
            
            <h1>🚀 Gaado Backend API</h1>
            
            
            <div class="scraper-section">
                <h2>✨ Google Gemini Chat</h2>
                <p style="color: #666; font-size: 0.85em; margin-top: -10px; margin-bottom: 20px; font-style: italic;">translate this from somali to english</p>
                <div class="scraper-form">
                    <textarea 
                        id="gemini-prompt" 
                        placeholder="Input your prompt here..."
                    >Waa bankiga kaliya ee dadkiisa cilada heesato ku xaliyo ka wada bax dib usoo bilaaw tirtir ee dib usoo daji</textarea>
                    <button id="gemini-chat-btn" onclick="chatGemini()">Send</button>
                </div>
                <div id="gemini-loading" class="loading">
                    <div class="spinner"></div>
                    <p>Response-request with AI.</p>
                </div>
                <div id="gemini-result-container" class="result-container"></div>
            </div>
            
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)



@app.post("/gemini/chat")
async def chat_with_gemini(request: GeminiChatRequest, req: Request):
    """
    Endpoint for chatting with Gemini model
    
    Args:
        request: Request with prompt text and optional model name
        req: FastAPI Request object for accessing environment variables
        
    Returns:
        Response from AI model
    """
    try:
        # Get API key from environment variable
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        # Create client with API key
        client = GeminiClient(api_key=gemini_api_key)
        
        if not client.is_available():
            return {
                "success": False,
                "error": "Gemini client is not available. Check GEMINI_API_KEY."
            }
        
        # Process user request - all logic is encapsulated in the client
        response = client.process_user_request(
            user_prompt=request.prompt,
            model=request.model
        )
        
        # Parse response using ModelParser
        parser = ModelParser()
        processed_comment_data = parser.parse_gemini_response(response)
        
        # Convert ProcessedCommentCreate to dict for response (excluding raw_comment_id)
        parsed_data_dict = None
        if processed_comment_data:
            # Use model_dump() to serialize, excluding raw_comment_id
            parsed_data_dict = processed_comment_data.model_dump(exclude={"raw_comment_id"})
            # Add somali_text from original prompt
            parsed_data_dict["somali_text"] = request.prompt
        
        return {
            "success": True,
            "response": response,
            "model": request.model or client.default_model,
            "parsed_data": parsed_data_dict
        }
    except Exception as e:
        logger.error(f"Error processing Gemini request: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Internal error: {str(e)}"
        }


@app.post("/gemini/save")
async def save_processed_comment(request: SaveProcessedCommentRequest):
    """
    Endpoint for saving processed comment to database
    
    Args:
        request: Request with processed comment data
        
    Returns:
        Success status and saved comment data
    """
    try:
        # First, create raw comment
        raw_comment = add_raw_comment(
            fb_comment_id=request.fb_comment_id,
            post_id=request.post_id,
            content=request.somali_text or ""
        )
        
        if not raw_comment or not raw_comment.get("id"):
            logger.warning("Failed to save raw comment to database")
            return {
                "success": False,
                "error": "Failed to save raw comment to database"
            }
        
        raw_comment_id = raw_comment["id"]
        
        # Then, create processed comment
        processed_comment = add_processed_comment(
            raw_comment_id=raw_comment_id,
            translation_en=request.translation_en,
            threat_level_slug=request.threat_level_slug,
            confidence_score=request.confidence_score,
            dialect=request.dialect,
            keywords=request.keywords,
            is_reviewed=False
        )
        
        if processed_comment:
            logger.info(f"Successfully saved comment to database: raw_comment_id={raw_comment_id}")
            return {
                "success": True,
                "raw_comment_id": raw_comment_id,
                "processed_comment": processed_comment
            }
        else:
            logger.warning("Failed to save processed comment to database")
            return {
                "success": False,
                "error": "Failed to save processed comment to database"
            }
            
    except Exception as e:
        logger.error(f"Error saving to database: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Internal error: {str(e)}"
        }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
    
# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )