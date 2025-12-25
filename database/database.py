"""
Database module for Cloudflare Workers D1 (SQLite)
Provides abstraction layer for database operations
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    """
    Database wrapper for Cloudflare D1 (SQLite)
    
    Works with D1 database binding in Cloudflare Workers environment
    Falls back to in-memory storage for local development
    """
    
    def __init__(self, db=None):
        """
        Initialize database connection
        
        Args:
            db: D1 database binding (from Cloudflare Workers) or None for local dev
        """
        self.db = db
        self.is_d1_available = db is not None
        
        if not self.is_d1_available:
            logger.warning("D1 database not available, using in-memory storage for local development")
            # Fallback to in-memory storage
            self._scraping_results: Dict[str, Dict[str, Any]] = {}
            self._scraping_status: Dict[str, Dict[str, Any]] = {}
            self._raw_posts: Dict[int, Dict[str, Any]] = {}
            self._raw_comments: Dict[int, Dict[str, Any]] = {}
            self._processed_comments: Dict[int, Dict[str, Any]] = {}
            self._next_post_id = 1
            self._next_comment_id = 1
            self._next_processed_id = 1
    
    async def init_schema(self):
        """
        Initialize database schema (create tables if they don't exist)
        Should be called once during application startup
        """
        if not self.is_d1_available:
            logger.info("Skipping schema initialization (using in-memory storage)")
            return
        
        try:
            # Enable foreign keys
            await self.db.execute("PRAGMA foreign_keys = ON")
            
            # Create scraping_results table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS scraping_results (
                    result_id TEXT PRIMARY KEY,
                    page_username TEXT,
                    url TEXT,
                    data TEXT NOT NULL,  -- JSON string with full result data
                    fetched_at TEXT NOT NULL,
                    saved_at TEXT NOT NULL,
                    total_count INTEGER DEFAULT 0,
                    duration_seconds REAL
                )
            """)
            
            # Create scraping_status table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS scraping_status (
                    result_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    url TEXT,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    duration_seconds REAL,
                    comments_count INTEGER DEFAULT 0,
                    method TEXT,
                    success INTEGER DEFAULT 0,  -- SQLite boolean (0/1)
                    FOREIGN KEY (result_id) REFERENCES scraping_results(result_id)
                )
            """)
            
            # Create users table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    session_token TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create threat_levels table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS threat_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    color_code TEXT,
                    description TEXT
                )
            """)
            
            # Create complaint_categories table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS complaint_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT
                )
            """)
            
            # Create sentiment_types table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL
                )
            """)
            
            # Create raw_posts table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS raw_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fb_post_id TEXT UNIQUE NOT NULL,
                    content TEXT,
                    reaction_count INTEGER DEFAULT 0,
                    share_count INTEGER DEFAULT 0,
                    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create raw_comments table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS raw_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fb_comment_id TEXT UNIQUE NOT NULL,
                    post_id INTEGER NOT NULL,
                    parent_comment_id INTEGER,
                    author_name TEXT,
                    content TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES raw_posts(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_comment_id) REFERENCES raw_comments(id) ON DELETE SET NULL
                )
            """)
            
            # Create processed_comments table
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS processed_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_comment_id INTEGER NOT NULL UNIQUE,
                    category_id INTEGER,
                    sentiment_id INTEGER,
                    threat_level_id INTEGER,
                    translation_en TEXT,
                    confidence_score REAL,
                    dialect TEXT,
                    keywords JSON,
                    is_reviewed BOOLEAN DEFAULT 0,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (raw_comment_id) REFERENCES raw_comments(id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES complaint_categories(id),
                    FOREIGN KEY (sentiment_id) REFERENCES sentiment_types(id),
                    FOREIGN KEY (threat_level_id) REFERENCES threat_levels(id)
                )
            """)
            
            # Create indexes
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_scraping_results_fetched_at 
                ON scraping_results(fetched_at DESC)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_scraping_results_page_username 
                ON scraping_results(page_username)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_complaint_categories_slug 
                ON complaint_categories(slug)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sentiment_types_slug 
                ON sentiment_types(slug)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_threat_levels_slug 
                ON threat_levels(slug)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_posts_fb_post_id 
                ON raw_posts(fb_post_id)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_posts_scraped_at 
                ON raw_posts(scraped_at DESC)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_comments_fb_comment_id 
                ON raw_comments(fb_comment_id)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_comments_post_id 
                ON raw_comments(post_id)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_comments_parent_comment_id 
                ON raw_comments(parent_comment_id)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_comments_created_at 
                ON raw_comments(created_at DESC)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_comments_raw_comment_id 
                ON processed_comments(raw_comment_id)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_comments_category_id 
                ON processed_comments(category_id)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_comments_sentiment_id 
                ON processed_comments(sentiment_id)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_comments_threat_level_id 
                ON processed_comments(threat_level_id)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_comments_is_reviewed 
                ON processed_comments(is_reviewed)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_comments_processed_at 
                ON processed_comments(processed_at DESC)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users(email)
            """)
            
            await self.db.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_session_token 
                ON users(session_token)
            """)
            
            # Seed data
            await self.db.execute("""
                INSERT OR IGNORE INTO threat_levels (slug, name, color_code) VALUES 
                ('nominal', 'Nominal', '#10B981'),
                ('elevated', 'Elevated', '#F59E0B'),
                ('critical', 'Critical', '#EF4444')
            """)
            
            await self.db.execute("""
                INSERT OR IGNORE INTO sentiment_types (slug, name) VALUES 
                ('friendly', 'Friendly'),
                ('anxious', 'Anxious'),
                ('angry', 'Angry')
            """)
            
            await self.db.execute("""
                INSERT OR IGNORE INTO complaint_categories (slug, name) VALUES 
                ('support_service', 'Support Service'),
                ('offline_branch', 'Offline Branch'),
                ('mobile_app', 'Mobile App'),
                ('website', 'Website'),
                ('pricing_policy', 'Pricing Policy')
            """)
            
            await self.db.execute("""
                INSERT OR IGNORE INTO users (email) VALUES ('admin@gaado.bank')
            """)
            
            logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database schema: {e}")
            raise
    
    # ========== Scraping Results Operations ==========
    
    async def save_scraping_result(self, result_id: str, data: Dict[str, Any]) -> str:
        """Save Facebook scraping result"""
        if not self.is_d1_available:
            self._scraping_results[result_id] = {
                **data,
                "result_id": result_id,
                "saved_at": datetime.now().isoformat()
            }
            return result_id
        
        data_json = json.dumps(data)
        fetched_at = data.get("fetched_at", datetime.now().isoformat())
        saved_at = datetime.now().isoformat()
        
        await self.db.execute("""
            INSERT OR REPLACE INTO scraping_results 
            (result_id, page_username, url, data, fetched_at, saved_at, total_count, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, 
            result_id,
            data.get("page_username"),
            data.get("url"),
            data_json,
            fetched_at,
            saved_at,
            data.get("total_count", 0),
            data.get("duration_seconds")
        )
        
        return result_id
    
    async def get_scraping_result(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get scraping result by ID"""
        if not self.is_d1_available:
            return self._scraping_results.get(result_id)
        
        result = await self.db.prepare("""
            SELECT result_id, page_username, url, data, fetched_at, saved_at, total_count, duration_seconds
            FROM scraping_results
            WHERE result_id = ?
        """).bind(result_id).first()
        
        if not result:
            return None
        
        data = json.loads(result["data"])
        return {
            **data,
            "result_id": result["result_id"],
            "saved_at": result["saved_at"]
        }
    
    async def list_scraping_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent scraping results"""
        if not self.is_d1_available:
            results = []
            for result_id, result_data in list(self._scraping_results.items())[-limit:]:
                results.append({
                    "result_id": result_id,
                    "url": result_data.get("url"),
                    "comments_count": result_data.get("total_count", 0),
                    "fetched_at": result_data.get("fetched_at"),
                    "duration_seconds": result_data.get("duration_seconds")
                })
            return results
        
        results = await self.db.prepare("""
            SELECT result_id, url, total_count, fetched_at, duration_seconds
            FROM scraping_results
            ORDER BY fetched_at DESC
            LIMIT ?
        """).bind(limit).all()
        
        return [
            {
                "result_id": r["result_id"],
                "url": r["url"],
                "comments_count": r["total_count"] or 0,
                "fetched_at": r["fetched_at"],
                "duration_seconds": r["duration_seconds"]
            }
            for r in results
        ]
    
    async def get_latest_scraping_result(self) -> Optional[Dict[str, Any]]:
        """Get the latest scraping result"""
        if not self.is_d1_available:
            if not self._scraping_results:
                return None
            latest_key = max(self._scraping_results.keys(), 
                           key=lambda k: self._scraping_results[k].get('fetched_at', ''))
            return self._scraping_results[latest_key]
        
        result = await self.db.prepare("""
            SELECT result_id, page_username, url, data, fetched_at, saved_at, total_count, duration_seconds
            FROM scraping_results
            ORDER BY fetched_at DESC
            LIMIT 1
        """).first()
        
        if not result:
            return None
        
        data = json.loads(result["data"])
        return {
            **data,
            "result_id": result["result_id"],
            "saved_at": result["saved_at"]
        }
    
    # ========== Scraping Status Operations ==========
    
    async def save_scraping_status(self, result_id: str, status_data: Dict[str, Any]) -> str:
        """Save scraping status"""
        if not self.is_d1_available:
            self._scraping_status[result_id] = status_data
            return result_id
        
        await self.db.execute("""
            INSERT OR REPLACE INTO scraping_status
            (result_id, status, url, started_at, completed_at, duration_seconds, comments_count, method, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            result_id,
            status_data.get("status", "unknown"),
            status_data.get("url"),
            status_data.get("started_at", datetime.now().isoformat()),
            status_data.get("completed_at"),
            status_data.get("duration_seconds"),
            status_data.get("comments_count", 0),
            status_data.get("method"),
            1 if status_data.get("success", False) else 0
        )
        
        return result_id
    
    async def get_scraping_status(self, result_id: str) -> Optional[Dict[str, Any]]:
        """Get scraping status by ID"""
        if not self.is_d1_available:
            return self._scraping_status.get(result_id)
        
        result = await self.db.prepare("""
            SELECT result_id, status, url, started_at, completed_at, duration_seconds, comments_count, method, success
            FROM scraping_status
            WHERE result_id = ?
        """).bind(result_id).first()
        
        if not result:
            return None
        
        return {
            "result_id": result["result_id"],
            "status": result["status"],
            "url": result["url"],
            "started_at": result["started_at"],
            "completed_at": result["completed_at"],
            "duration_seconds": result["duration_seconds"],
            "comments_count": result["comments_count"] or 0,
            "method": result["method"],
            "success": bool(result["success"])
        }
    
    # ========== Reference Data Operations ==========
    
    async def get_threat_levels(self) -> List[Dict[str, Any]]:
        """Get all threat levels"""
        if not self.is_d1_available:
            return [
                {"id": 1, "slug": "nominal", "name": "Nominal", "color_code": "#10B981"},
                {"id": 2, "slug": "elevated", "name": "Elevated", "color_code": "#F59E0B"},
                {"id": 3, "slug": "critical", "name": "Critical", "color_code": "#EF4444"}
            ]
        
        results = await self.db.prepare("SELECT id, slug, name, color_code, description FROM threat_levels ORDER BY id").all()
        return [dict(r) for r in results]
    
    async def get_sentiment_types(self) -> List[Dict[str, Any]]:
        """Get all sentiment types"""
        if not self.is_d1_available:
            return [
                {"id": 1, "slug": "friendly", "name": "Friendly"},
                {"id": 2, "slug": "anxious", "name": "Anxious"},
                {"id": 3, "slug": "angry", "name": "Angry"}
            ]
        
        results = await self.db.prepare("SELECT id, slug, name FROM sentiment_types ORDER BY id").all()
        return [dict(r) for r in results]
    
    async def get_complaint_categories(self) -> List[Dict[str, Any]]:
        """Get all complaint categories"""
        if not self.is_d1_available:
            return [
                {"id": 1, "slug": "support_service", "name": "Support Service"},
                {"id": 2, "slug": "offline_branch", "name": "Offline Branch"},
                {"id": 3, "slug": "mobile_app", "name": "Mobile App"},
                {"id": 4, "slug": "website", "name": "Website"},
                {"id": 5, "slug": "pricing_policy", "name": "Pricing Policy"}
            ]
        
        results = await self.db.prepare("SELECT id, slug, name, description FROM complaint_categories ORDER BY id").all()
        return [dict(r) for r in results]
    
    async def get_threat_level_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get threat level by slug"""
        if not self.is_d1_available:
            levels = {
                "nominal": {"id": 1, "slug": "nominal", "name": "Nominal", "color_code": "#10B981"},
                "elevated": {"id": 2, "slug": "elevated", "name": "Elevated", "color_code": "#F59E0B"},
                "critical": {"id": 3, "slug": "critical", "name": "Critical", "color_code": "#EF4444"}
            }
            return levels.get(slug)
        
        result = await self.db.prepare("SELECT id, slug, name, color_code, description FROM threat_levels WHERE slug = ?").bind(slug).first()
        return dict(result) if result else None
    
    async def get_sentiment_type_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get sentiment type by slug"""
        if not self.is_d1_available:
            types = {
                "friendly": {"id": 1, "slug": "friendly", "name": "Friendly"},
                "anxious": {"id": 2, "slug": "anxious", "name": "Anxious"},
                "angry": {"id": 3, "slug": "angry", "name": "Angry"}
            }
            return types.get(slug)
        
        result = await self.db.prepare("SELECT id, slug, name FROM sentiment_types WHERE slug = ?").bind(slug).first()
        return dict(result) if result else None
    
    async def get_complaint_category_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get complaint category by slug"""
        if not self.is_d1_available:
            categories = {
                "support_service": {"id": 1, "slug": "support_service", "name": "Support Service"},
                "offline_branch": {"id": 2, "slug": "offline_branch", "name": "Offline Branch"},
                "mobile_app": {"id": 3, "slug": "mobile_app", "name": "Mobile App"},
                "website": {"id": 4, "slug": "website", "name": "Website"},
                "pricing_policy": {"id": 5, "slug": "pricing_policy", "name": "Pricing Policy"}
            }
            return categories.get(slug)
        
        result = await self.db.prepare("SELECT id, slug, name, description FROM complaint_categories WHERE slug = ?").bind(slug).first()
        return dict(result) if result else None
    
    # ========== Raw Posts Operations ==========
    
    async def save_raw_post(self, fb_post_id: str, content: str = None, 
                           reaction_count: int = 0, share_count: int = 0) -> int:
        """Save or update a raw post"""
        if not self.is_d1_available:
            # Check if post already exists
            for post_id, post_data in self._raw_posts.items():
                if post_data.get("fb_post_id") == fb_post_id:
                    # Update existing post
                    post_data.update({
                        "content": content,
                        "reaction_count": reaction_count,
                        "share_count": share_count,
                        "scraped_at": datetime.now().isoformat()
                    })
                    return post_id
            
            # Create new post
            post_id = self._next_post_id
            self._next_post_id += 1
            self._raw_posts[post_id] = {
                "id": post_id,
                "fb_post_id": fb_post_id,
                "content": content,
                "reaction_count": reaction_count,
                "share_count": share_count,
                "scraped_at": datetime.now().isoformat()
            }
            return post_id
        
        # Try to get existing post
        existing = await self.db.prepare("SELECT id FROM raw_posts WHERE fb_post_id = ?").bind(fb_post_id).first()
        
        if existing:
            # Update existing post
            await self.db.execute("""
                UPDATE raw_posts 
                SET content = ?, reaction_count = ?, share_count = ?, scraped_at = CURRENT_TIMESTAMP
                WHERE fb_post_id = ?
            """, content, reaction_count, share_count, fb_post_id)
            return existing["id"]
        else:
            # Insert new post
            result = await self.db.execute("""
                INSERT INTO raw_posts (fb_post_id, content, reaction_count, share_count)
                VALUES (?, ?, ?, ?)
            """, fb_post_id, content, reaction_count, share_count)
            # Get the inserted ID
            post = await self.db.prepare("SELECT id FROM raw_posts WHERE fb_post_id = ?").bind(fb_post_id).first()
            return post["id"] if post else 0
    
    async def get_raw_post_by_fb_id(self, fb_post_id: str) -> Optional[Dict[str, Any]]:
        """Get raw post by Facebook post ID"""
        if not self.is_d1_available:
            for post_data in self._raw_posts.values():
                if post_data.get("fb_post_id") == fb_post_id:
                    return post_data
            return None
        
        result = await self.db.prepare("""
            SELECT id, fb_post_id, content, reaction_count, share_count, scraped_at
            FROM raw_posts
            WHERE fb_post_id = ?
        """).bind(fb_post_id).first()
        
        return dict(result) if result else None
    
    # ========== Raw Comments Operations ==========
    
    async def save_raw_comment(self, fb_comment_id: str, post_id: int, 
                              author_name: str = None, content: str = None,
                              parent_comment_id: int = None) -> int:
        """Save or update a raw comment"""
        if not self.is_d1_available:
            # Check if comment already exists
            for comment_id, comment_data in self._raw_comments.items():
                if comment_data.get("fb_comment_id") == fb_comment_id:
                    # Update existing comment
                    comment_data.update({
                        "post_id": post_id,
                        "author_name": author_name,
                        "content": content,
                        "parent_comment_id": parent_comment_id,
                        "created_at": datetime.now().isoformat()
                    })
                    return comment_id
            
            # Create new comment
            comment_id = self._next_comment_id
            self._next_comment_id += 1
            self._raw_comments[comment_id] = {
                "id": comment_id,
                "fb_comment_id": fb_comment_id,
                "post_id": post_id,
                "author_name": author_name,
                "content": content,
                "parent_comment_id": parent_comment_id,
                "created_at": datetime.now().isoformat()
            }
            return comment_id
        
        # Try to get existing comment
        existing = await self.db.prepare("SELECT id FROM raw_comments WHERE fb_comment_id = ?").bind(fb_comment_id).first()
        
        if existing:
            # Update existing comment
            await self.db.execute("""
                UPDATE raw_comments 
                SET post_id = ?, author_name = ?, content = ?, parent_comment_id = ?, created_at = CURRENT_TIMESTAMP
                WHERE fb_comment_id = ?
            """, post_id, author_name, content, parent_comment_id, fb_comment_id)
            return existing["id"]
        else:
            # Insert new comment
            await self.db.execute("""
                INSERT INTO raw_comments (fb_comment_id, post_id, author_name, content, parent_comment_id)
                VALUES (?, ?, ?, ?, ?)
            """, fb_comment_id, post_id, author_name, content, parent_comment_id)
            # Get the inserted ID
            comment = await self.db.prepare("SELECT id FROM raw_comments WHERE fb_comment_id = ?").bind(fb_comment_id).first()
            return comment["id"] if comment else 0
    
    async def get_raw_comments_by_post_id(self, post_id: int) -> List[Dict[str, Any]]:
        """Get all raw comments for a post"""
        if not self.is_d1_available:
            return [
                comment_data for comment_data in self._raw_comments.values()
                if comment_data.get("post_id") == post_id
            ]
        
        results = await self.db.prepare("""
            SELECT id, fb_comment_id, post_id, parent_comment_id, author_name, content, created_at
            FROM raw_comments
            WHERE post_id = ?
            ORDER BY created_at ASC
        """).bind(post_id).all()
        
        return [dict(r) for r in results]
    
    async def get_all_raw_comments(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get all raw comments with pagination, including post info"""
        if not self.is_d1_available:
            all_comments = list(self._raw_comments.values())
            total = len(all_comments)
            paginated = all_comments[offset:offset + limit]
            
            # Add post info
            for comment in paginated:
                post_id = comment.get("post_id")
                if post_id and post_id in self._raw_posts:
                    comment["post"] = self._raw_posts[post_id]
            
            return {
                "comments": paginated,
                "total": total,
                "limit": limit,
                "offset": offset
            }
        
        # Get total count
        total_result = await self.db.prepare("SELECT COUNT(*) as count FROM raw_comments").first()
        total = total_result["count"] if total_result else 0
        
        # Get paginated comments with post info
        results = await self.db.prepare("""
            SELECT rc.id, rc.fb_comment_id, rc.post_id, rc.parent_comment_id, 
                   rc.author_name, rc.content, rc.created_at,
                   rp.fb_post_id, rp.content as post_content, rp.reaction_count, rp.share_count
            FROM raw_comments rc
            LEFT JOIN raw_posts rp ON rc.post_id = rp.id
            ORDER BY rc.created_at DESC
            LIMIT ? OFFSET ?
        """).bind(limit, offset).all()
        
        comments = []
        for r in results:
            comment = dict(r)
            comment["post"] = {
                "fb_post_id": r.get("fb_post_id"),
                "content": r.get("post_content"),
                "reaction_count": r.get("reaction_count", 0),
                "share_count": r.get("share_count", 0)
            } if r.get("fb_post_id") else None
            comments.append(comment)
        
        return {
            "comments": comments,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    async def save_raw_posts_and_comments(self, posts_data: List[Dict[str, Any]], 
                                         comments_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Save multiple posts and comments in a batch
        
        Args:
            posts_data: List of post dictionaries with keys: fb_post_id, content, reaction_count, share_count
            comments_data: List of comment dictionaries with keys: fb_comment_id, post_fb_id, author_name, content, parent_comment_id
        
        Returns:
            Dictionary with saved_post_ids and saved_comment_ids
        """
        saved_post_ids = {}
        saved_comment_ids = []
        
        # First, save all posts and create mapping fb_post_id -> db_post_id
        for post_data in posts_data:
            fb_post_id = post_data.get("fb_post_id") or post_data.get("post_id", "")
            if not fb_post_id:
                continue
            
            db_post_id = await self.save_raw_post(
                fb_post_id=fb_post_id,
                content=post_data.get("content") or post_data.get("text", ""),
                reaction_count=post_data.get("reaction_count") or post_data.get("likes", 0),
                share_count=post_data.get("share_count") or post_data.get("shares", 0)
            )
            saved_post_ids[fb_post_id] = db_post_id
        
        # Then, save all comments with proper post_id references
        for comment_data in comments_data:
            post_fb_id = comment_data.get("post_fb_id") or comment_data.get("post_id", "")
            if not post_fb_id or post_fb_id not in saved_post_ids:
                continue
            
            db_post_id = saved_post_ids[post_fb_id]
            fb_comment_id = comment_data.get("fb_comment_id") or comment_data.get("comment_id", "")
            
            # Handle parent comment ID if it exists
            parent_fb_comment_id = comment_data.get("parent_fb_comment_id") or comment_data.get("parent_comment_id")
            parent_db_comment_id = None
            
            if parent_fb_comment_id:
                # Try to find parent comment in already saved comments
                # For simplicity, we'll need to query or track this
                # For now, we'll skip parent relationships in batch saves
                pass
            
            db_comment_id = await self.save_raw_comment(
                fb_comment_id=fb_comment_id or f"temp_{len(saved_comment_ids)}",
                post_id=db_post_id,
                author_name=comment_data.get("author_name") or comment_data.get("author", ""),
                content=comment_data.get("content") or comment_data.get("text", ""),
                parent_comment_id=parent_db_comment_id
            )
            saved_comment_ids.append(db_comment_id)
        
        return {
            "saved_post_ids": saved_post_ids,
            "saved_comment_ids": saved_comment_ids,
            "posts_count": len(saved_post_ids),
            "comments_count": len(saved_comment_ids)
        }
    
    # ========== Processed Comments Operations ==========
    
    async def save_processed_comment(self, raw_comment_id: int, translation_en: str = None,
                                     category_slug: str = None, sentiment_slug: str = None,
                                     threat_level_slug: str = None, confidence_score: float = None,
                                     dialect: str = None, keywords: List[str] = None,
                                     is_reviewed: bool = False) -> int:
        """Save or update processed comment"""
        if not self.is_d1_available:
            # Check if processed comment already exists
            for proc_id, proc_data in self._processed_comments.items():
                if proc_data.get("raw_comment_id") == raw_comment_id:
                    # Update existing
                    proc_data.update({
                        "translation_en": translation_en,
                        "confidence_score": confidence_score,
                        "dialect": dialect,
                        "keywords": keywords or [],
                        "is_reviewed": is_reviewed,
                        "processed_at": datetime.now().isoformat()
                    })
                    return proc_id
            
            # Create new
            proc_id = self._next_processed_id
            self._next_processed_id += 1
            self._processed_comments[proc_id] = {
                "id": proc_id,
                "raw_comment_id": raw_comment_id,
                "translation_en": translation_en,
                "confidence_score": confidence_score,
                "dialect": dialect,
                "keywords": keywords or [],
                "is_reviewed": is_reviewed,
                "processed_at": datetime.now().isoformat()
            }
            return proc_id
        
        # Get reference IDs
        category_id = None
        if category_slug:
            category = await self.get_complaint_category_by_slug(category_slug)
            if category:
                category_id = category["id"]
        
        sentiment_id = None
        if sentiment_slug:
            sentiment = await self.get_sentiment_type_by_slug(sentiment_slug)
            if sentiment:
                sentiment_id = sentiment["id"]
        
        threat_level_id = None
        if threat_level_slug:
            threat_level = await self.get_threat_level_by_slug(threat_level_slug)
            if threat_level:
                threat_level_id = threat_level["id"]
        
        keywords_json = json.dumps(keywords or [])
        
        # Check if processed comment already exists
        existing = await self.db.prepare("SELECT id FROM processed_comments WHERE raw_comment_id = ?").bind(raw_comment_id).first()
        
        if existing:
            # Update existing
            await self.db.execute("""
                UPDATE processed_comments 
                SET category_id = ?, sentiment_id = ?, threat_level_id = ?,
                    translation_en = ?, confidence_score = ?, dialect = ?, keywords = ?,
                    is_reviewed = ?, processed_at = CURRENT_TIMESTAMP
                WHERE raw_comment_id = ?
            """, category_id, sentiment_id, threat_level_id, translation_en, 
                confidence_score, dialect, keywords_json, 1 if is_reviewed else 0, raw_comment_id)
            return existing["id"]
        else:
            # Insert new
            await self.db.execute("""
                INSERT INTO processed_comments 
                (raw_comment_id, category_id, sentiment_id, threat_level_id,
                 translation_en, confidence_score, dialect, keywords, is_reviewed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, raw_comment_id, category_id, sentiment_id, threat_level_id,
                translation_en, confidence_score, dialect, keywords_json, 1 if is_reviewed else 0)
            # Get the inserted ID
            proc = await self.db.prepare("SELECT id FROM processed_comments WHERE raw_comment_id = ?").bind(raw_comment_id).first()
            return proc["id"] if proc else 0
    
    async def get_processed_comments(self, limit: int = 100, offset: int = 0,
                                    is_reviewed: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get processed comments with pagination"""
        if not self.is_d1_available:
            results = list(self._processed_comments.values())
            if is_reviewed is not None:
                results = [r for r in results if r.get("is_reviewed") == is_reviewed]
            return results[offset:offset + limit]
        
        query = """
            SELECT pc.id, pc.raw_comment_id, pc.category_id, pc.sentiment_id, pc.threat_level_id,
                   pc.translation_en, pc.confidence_score, pc.dialect, pc.keywords,
                   pc.is_reviewed, pc.processed_at,
                   cc.slug as category_slug, cc.name as category_name,
                   st.slug as sentiment_slug, st.name as sentiment_name,
                   tl.slug as threat_level_slug, tl.name as threat_level_name, tl.color_code as threat_level_color
            FROM processed_comments pc
            LEFT JOIN complaint_categories cc ON pc.category_id = cc.id
            LEFT JOIN sentiment_types st ON pc.sentiment_id = st.id
            LEFT JOIN threat_levels tl ON pc.threat_level_id = tl.id
        """
        
        params = []
        if is_reviewed is not None:
            query += " WHERE pc.is_reviewed = ?"
            params.append(1 if is_reviewed else 0)
        
        query += " ORDER BY pc.processed_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        results = await self.db.prepare(query).bind(*params).all()
        
        return [
            {
                **dict(r),
                "keywords": json.loads(r["keywords"]) if r["keywords"] else []
            }
            for r in results
        ]
    
    async def insert_mock_data(self) -> Dict[str, Any]:
        """
        Insert mock comments data for testing/development
        
        Returns:
            Dictionary with insertion results
        """
        mock_comments = [
            {
                "somali_text": "Hhhh xayeysiin aa Hees cml udhagaystay xayeysiin Raab ah Faraska Madow waxuu la cadaan wayey hal abuur waye",
                "english_text": "Hahaha, I listened to an advertisement that was like a song, a Rap advertisement. Black Horse couldn't make it clear, it is creativity.",
                "threat_level": "Low",
                "confidence_score": 0.95
            },
            {
                "somali_text": "Waa bankiga kaliya ee dadkiisa cilada heesato ku xaliyo ka wada bax dib usoo bilaaw tirtir ee dib usoo daji",
                "english_text": "It's the only bank that solves its customers' technical issues by telling them to log out, restart, delete, and reinstall.",
                "threat_level": "Low",
                "confidence_score": 0.95
            },
            {
                "somali_text": "Maalinka aad deposit ATM aduunka laga samen karo aad kentaan ayaad top 1 noqondontaan",
                "english_text": "The day you introduce international ATM deposits [deposits that can be done from the world], you will become number one.",
                "threat_level": "Low",
                "confidence_score": 0.98
            },
            {
                "somali_text": "Premier Bank Wah Xaaladiina Xayeysiiska inta may maroysaa Okei dhib ma lehee teamka Xayeysiinta idin Sameysey Jeebka ma u qoyseen ama qado ley u dalab teen Masaakiinta BaL Clip HaLaga soo duuwo ayagoo Shilimaadkooda la siinaayo si VAR-KA aynu u xaqiijino",
                "english_text": "Premier Bank, what is the situation? Is this the extent of the advertising? Okay, no problem, but did you pay [wet the pockets of] the team that made the ad for you, or did you just order them lunch? The poor things, let a clip be filmed of them being paid their money so we can verify it via VAR.",
                "threat_level": "Low",
                "confidence_score": 0.95
            },
            {
                "somali_text": "Bangiga kaliya Cilada ku heysato ku xaliyo cilad kale",
                "english_text": "The only bank that solves the problem facing it with another problem.",
                "threat_level": "Low",
                "confidence_score": 0.95
            },
            {
                "somali_text": "Hadaan heestan xiftiyo tolow card bilaash ah ma leeyahay",
                "english_text": "If I memorize this song, I wonder if I get a free card.",
                "threat_level": "Low",
                "confidence_score": 0.98
            },
            {
                "somali_text": "Aad baa u xayeesiin badan tihiin, aadna waad u liidataam!",
                "english_text": "You advertise very much, and you are very weak [incompetent]!",
                "threat_level": "Low",
                "confidence_score": 0.99
            }
        ]
        
        # Map "Low" threat level to "nominal" slug
        threat_level_slug = "nominal"
        
        # Create a mock post
        mock_post_id = await self.save_raw_post(
            fb_post_id="mock_post_001",
            content="Mock Premier Bank Post for Testing",
            reaction_count=0,
            share_count=0
        )
        
        inserted_comments = []
        
        for idx, mock_comment in enumerate(mock_comments):
            # Create raw comment
            fb_comment_id = f"mock_comment_{idx + 1:03d}"
            raw_comment_id = await self.save_raw_comment(
                fb_comment_id=fb_comment_id,
                post_id=mock_post_id,
                author_name=f"Mock User {idx + 1}",
                content=mock_comment["somali_text"],
                parent_comment_id=None
            )
            
            # Create processed comment
            processed_id = await self.save_processed_comment(
                raw_comment_id=raw_comment_id,
                translation_en=mock_comment["english_text"],
                threat_level_slug=threat_level_slug,
                confidence_score=mock_comment["confidence_score"],
                dialect="Maxa-tiri",
                keywords=[],
                is_reviewed=False
            )
            
            inserted_comments.append({
                "raw_comment_id": raw_comment_id,
                "processed_id": processed_id,
                "fb_comment_id": fb_comment_id
            })
        
        return {
            "success": True,
            "post_id": mock_post_id,
            "comments_inserted": len(inserted_comments),
            "comments": inserted_comments
        }


# Global database instance (will be set during app startup)
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """Get database instance"""
    global _db_instance
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance


def init_database(db=None) -> Database:
    """
    Initialize database instance
    
    Args:
        db: D1 database binding from Cloudflare Workers (or None for local dev)
    
    Returns:
        Database instance
    """
    global _db_instance
    _db_instance = Database(db)
    return _db_instance

