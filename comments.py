"""
Comments module for displaying processed comments from Supabase
Uses database_api.py for Supabase operations
"""
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse
from datetime import datetime
import logging
from dateutil import parser as date_parser
from database.database_api import get_latest_comments
from database.database import get_database

logger = logging.getLogger(__name__)

router = APIRouter()

def escape_html(text: str) -> str:
    """Escape HTML special characters"""
    if not text:
        return ""
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;"))


@router.get("/comments", response_class=HTMLResponse)
def comments_page(limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0)):
    """Comments page with processed comments from Supabase"""
    try:
        # Get processed comments from Supabase (already includes joined data)
        comments_data = get_latest_comments(limit=limit, offset=offset, is_reviewed=None)
        
        # Use the flattened data directly
        total = len(comments_data)  # Approximate total (could be improved with count query)
        fetch_success = True
        
    except Exception as e:
        logger.error(f"Error loading comments: {e}")
        comments_data = []
        total = 0
        fetch_success = False
    
    # Determine status class and icon
    status_class = "online" if fetch_success else "offline"
    status_icon = "🟢" if fetch_success else "🔴"
    fetch_time_str = datetime.now().strftime('%H:%M:%S')
    
    # Build HTML - CSS as regular string, body with variables as f-string
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>COMMENTS - Gaado Backend</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: #1a1a1a;
                color: #e0e0e0;
                min-height: 100vh;
                padding: 0;
            }
            .header {
                background: #2a2a2a;
                padding: 20px 30px;
                border-bottom: 2px solid #3a3a3a;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .header-left {
                display: flex;
                align-items: center;
                gap: 30px;
            }
            .header h1 {
                color: #ffffff;
                font-size: 1.8em;
                font-weight: 700;
                letter-spacing: 1px;
            }
            .header .monitoring {
                color: #b0b0b0;
                font-size: 0.9em;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .header .monitoring::before {
                content: "📘";
                font-size: 1.2em;
            }
            .last-update {
                color: #888;
                font-size: 0.85em;
                margin-left: 20px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .last-update.online {
                color: #10b981;
            }
            .last-update.offline {
                color: #ef4444;
            }
            .live-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #10b981;
                font-weight: 600;
            }
            .live-dot {
                width: 12px;
                height: 12px;
                background: #10b981;
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            .header a {
                padding: 8px 16px;
                background: #3a3a3a;
                color: #e0e0e0;
                text-decoration: none;
                border-radius: 6px;
                transition: all 0.3s ease;
                font-size: 0.9em;
            }
            .header a:hover {
                background: #4a4a4a;
            }
            .nav-links {
                display: flex;
                gap: 15px;
                align-items: center;
            }
            .nav-link {
                padding: 8px 16px;
                background: #3a3a3a;
                color: #e0e0e0;
                text-decoration: none;
                border-radius: 6px;
                transition: all 0.3s ease;
                font-size: 0.9em;
                font-weight: 500;
            }
            .nav-link:hover {
                background: #4a4a4a;
            }
            .nav-link.active {
                background: #667eea;
                color: #ffffff;
            }
            .nav-link.active:hover {
                background: #5568d3;
            }
            .feed-container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
            }
            .comment-entry {
                background: #2a2a2a;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 15px;
                border-left: 4px solid #3a3a3a;
                display: flex;
                gap: 20px;
                transition: all 0.2s ease;
            }
            .comment-entry:hover {
                background: #2f2f2f;
                border-left-color: #667eea;
            }
            .user-badge {
                min-width: 50px;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
            }
            .user-number {
                width: 40px;
                height: 40px;
                background: #3a3a3a;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                color: #e0e0e0;
                font-size: 0.9em;
            }
            .comment-main {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .comment-user-info {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 8px;
            }
            .comment-user-name {
                font-weight: 600;
                color: #ffffff;
                font-size: 1em;
            }
            .comment-meta {
                color: #888;
                font-size: 0.85em;
                display: flex;
                gap: 10px;
            }
            .comment-text {
                color: #e0e0e0;
                font-size: 0.95em;
                line-height: 1.6;
                white-space: pre-wrap;
                word-wrap: break-word;
                margin: 10px 0;
            }
            .highlight-red {
                background: rgba(239, 68, 68, 0.3);
                padding: 2px 4px;
                border-radius: 3px;
                color: #ff6b6b;
            }
            .highlight-green {
                background: rgba(16, 185, 129, 0.3);
                padding: 2px 4px;
                border-radius: 3px;
                color: #10b981;
            }
            .comment-actions {
                display: flex;
                gap: 10px;
                margin-top: 12px;
            }
            .action-btn {
                padding: 6px 12px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 0.85em;
                display: flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s ease;
            }
            .action-btn.reply {
                background: #3a3a3a;
                color: #e0e0e0;
            }
            .action-btn.reply:hover {
                background: #4a4a4a;
            }
            .action-btn.escalate {
                background: #3a3a3a;
                color: #f59e0b;
            }
            .action-btn.escalate:hover {
                background: #4a4a4a;
            }
            .category-badge {
                min-width: 150px;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 10px;
            }
            .category-btn {
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.85em;
                text-align: center;
                min-width: 140px;
            }
            .category-btn.orange {
                background: #f59e0b;
                color: #1a1a1a;
            }
            .category-btn.green {
                background: #10b981;
                color: #1a1a1a;
            }
            .category-btn.red {
                background: #ef4444;
                color: #ffffff;
            }
            .language-tag {
                color: #888;
                font-size: 0.8em;
                margin-top: 8px;
            }
            .translation-text {
                color: #b0b0b0;
                font-size: 0.9em;
                line-height: 1.5;
                margin-top: 10px;
                padding: 10px;
                background: #1f1f1f;
                border-radius: 5px;
                border-left: 3px solid #667eea;
            }
            .translation-label {
                color: #888;
                font-size: 0.75em;
                text-transform: uppercase;
                margin-bottom: 5px;
                font-weight: 600;
            }
            .pagination {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 10px;
                margin-top: 30px;
                padding: 20px;
                background: #2a2a2a;
                border-radius: 8px;
            }
            .pagination button {
                padding: 10px 20px;
                background: #3a3a3a;
                color: #e0e0e0;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.9em;
                transition: all 0.3s ease;
            }
            .pagination button:hover:not(:disabled) {
                background: #4a4a4a;
            }
            .pagination button:disabled {
                background: #1a1a1a;
                color: #555;
                cursor: not-allowed;
            }
            .pagination-info {
                color: #888;
                font-size: 0.9em;
            }
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                background: #2a2a2a;
                border-radius: 8px;
            }
            .empty-state h2 {
                color: #888;
                margin-bottom: 10px;
            }
            .empty-state p {
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-left">
                <h1>COMMENTS</h1>
                <div class="monitoring">Monitoring: Premier Bank Official Page</div>
                <div class="last-update """ + status_class + """">
                    <span>""" + status_icon + """</span>
                    <span>Last update: """ + fetch_time_str + """</span>
                </div>
                <div class="nav-links">
                    <a href="/" class="nav-link">Home</a>
                    <a href="/comments" class="nav-link active">Feed</a>
                </div>
            </div>
        </div>
        
        <div class="feed-container" id="feed-container">
    """
    
    if not comments_data:
        html_content += """
            <div class="empty-state">
                <h2>📭 No comments found</h2>
                <p>Start scraping to add comments to the feed.</p>
            </div>
        """
    else:
        comment_index = total - offset
        for comment in comments_data:
            comment_id = comment.get("id", 0)
            author = comment.get("author_name") or f"User_{comment_id}"
            content = comment.get("content") or ""
            created_at = comment.get("created_at") or ""
            
            category_name = comment.get("category_name") or "General"
            category_slug = comment.get("category_slug") or "general"
            sentiment_slug = comment.get("sentiment_slug") or ""
            threat_level_slug = comment.get("threat_level_slug") or ""
            threat_level_color = comment.get("threat_level_color") or "#10B981"
            translation = comment.get("translation_en") or ""
            dialect = comment.get("dialect") or ""
            confidence_score = comment.get("confidence_score", 0.0)
            
            # Format date
            time_str = ""
            # if created_at:
            #     try:
            #         if isinstance(created_at, str):
            #             dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            #             time_str = dt.strftime("%H:%M:%S")
            #     except (ValueError, AttributeError) as e:
            #         logger.debug(f"Could not parse date: {e}")
            #         pass
            
            # Determine category color based on threat level
            category_color = "orange"
            if threat_level_slug == "nominal":
                category_color = "green"
            elif threat_level_slug == "critical":
                category_color = "red"
            elif sentiment_slug == "friendly":
                category_color = "green"
            
            # Highlight keywords (simple keyword detection)
            highlighted_content = escape_html(content)
            negative_words = ["scam", "error", "broken", "lost", "luntay", "dispute", "problem", "issue"]
            positive_words = ["mahadsanid", "thank", "thanks", "good", "wacan"]
            
            for word in negative_words:
                if word.lower() in highlighted_content.lower():
                    highlighted_content = highlighted_content.replace(word, f'<span class="highlight-red">{word}</span>')
                    highlighted_content = highlighted_content.replace(word.capitalize(), f'<span class="highlight-red">{word.capitalize()}</span>')
            
            for word in positive_words:
                if word.lower() in highlighted_content.lower():
                    highlighted_content = highlighted_content.replace(word, f'<span class="highlight-green">{word}</span>')
                    highlighted_content = highlighted_content.replace(word.capitalize(), f'<span class="highlight-green">{word.capitalize()}</span>')
            
            # Determine language
            language = "ENGLISH"
            if dialect:
                language = f"SOMALI ({dialect.upper()})"
            elif any(ord(c) > 127 for c in content):
                language = "SOMALI"
            
            # Build translation HTML if available
            translation_html = ""
            if translation:
                translation_html = f'<div class="translation-text"><div class="translation-label">English Translation:</div>{escape_html(translation)}</div>'
            
            # Confidence score badge
            confidence_html = ""
            if confidence_score:
                confidence_html = f'<div class="language-tag">Confidence: {confidence_score:.0%}</div>'
            
            html_content += f"""
            <div class="comment-entry">
                <div class="user-badge">
                    <div class="user-number">{comment_index}</div>
                </div>
                <div class="comment-main">
                    <div class="comment-user-info">
                        <div class="comment-user-name">{escape_html(author)}</div>
                        <div class="comment-meta">
                            <span>via Mobile</span>
                        </div>
                    </div>
                    <div class="comment-text">{highlighted_content}</div>
                    {translation_html}
                    <div class="comment-actions">
                        <button class="action-btn reply">
                            <span>💬</span>
                            <span>Reply</span>
                        </button>
                        <button class="action-btn escalate">
                            <span>⚠️</span>
                            <span>Escalate</span>
                        </button>
                    </div>
                    <div class="language-tag">Detected language: {language}</div>
                    {confidence_html}
                </div>
                <div class="category-badge">
                    <div class="category-btn {category_color}" style="background-color: {threat_level_color};">{category_name.replace('_', ' ').title()}</div>
                </div>
            </div>
            """
            comment_index -= 1
    
    # Pagination
    current_limit = limit
    current_offset = offset
    current_page = (current_offset // current_limit) + 1
    total_pages = (total + current_limit - 1) // current_limit if total > 0 else 1
    
    html_content += f"""
        </div>
        
        <div class="pagination">
    """
    
    if current_page > 1:
        prev_offset = max(0, current_offset - current_limit)
        html_content += f'<button onclick="loadPage({prev_offset})">← Previous</button>'
    else:
        html_content += '<button disabled>← Previous</button>'
    
    html_content += f"""
            <span class="pagination-info">
                Page {current_page} of {total_pages} (showing {len(comments_data)} of {total})
            </span>
    """
    
    if current_offset + current_limit < total:
        next_offset = current_offset + current_limit
        html_content += f'<button onclick="loadPage({next_offset})">Next →</button>'
    else:
        html_content += '<button disabled>Next →</button>'
    
    html_content += f"""
        </div>
        
        <script>
            # function loadPage(offset) {{
            #     window.location.href = `/comments?offset=${{offset}}&limit={current_limit}&_t=${{Date.now()}}`;
            # }}
            
            # // Auto-refresh every 30 seconds
            # setTimeout(() => {{
            #     if (document.visibilityState === 'visible') {{
            #         window.location.href = window.location.pathname + window.location.search.split('&_t=')[0] + '&_t=' + Date.now();
            #     }}
            # }}, 30000);
        </script>
    </body>
    </html>
    """
    
    # Add headers to prevent caching
    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }
    
    return HTMLResponse(content=html_content, headers=headers)

