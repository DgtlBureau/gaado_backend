-- Cloudflare D1 Database Schema for Gaado Backend
-- This schema is automatically created by the application, but can be used for manual setup

-- ==========================================
-- ЧАСТЬ 1: СТРУКТУРА (DDL)
-- ==========================================

-- Включаем поддержку внешних ключей (на всякий случай, в D1 это обычно по дефолту)
PRAGMA foreign_keys = ON;

-- Documents table for storing text documents
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    metadata TEXT,  -- JSON string
    created_at TEXT NOT NULL
);

-- Scraping results table for Facebook scraping data
CREATE TABLE IF NOT EXISTS scraping_results (
    result_id TEXT PRIMARY KEY,
    page_username TEXT,
    url TEXT,
    data TEXT NOT NULL,  -- JSON string with full result data
    fetched_at TEXT NOT NULL,
    saved_at TEXT NOT NULL,
    total_count INTEGER DEFAULT 0,
    duration_seconds REAL
);

-- Scraping status table for tracking scraping operations
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
);

-- 1. Пользователи (Админы)
-- Источник: [cite: 33]
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    session_token TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. Справочник: Уровни угрозы (Threat Levels)
-- Источник: [cite: 82]
CREATE TABLE IF NOT EXISTS threat_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,      -- 'nominal', 'elevated', 'critical'
    name TEXT NOT NULL,             -- 'Nominal', 'Elevated', 'Critical'
    color_code TEXT,                -- '#10B981' (для UI Shadcn)
    description TEXT
);

-- 3. Справочник: Категории жалоб (Taxonomy)
-- Источник: [cite: 37, 38]
CREATE TABLE IF NOT EXISTS complaint_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,      -- 'mobile_app', 'pricing_policy'
    name TEXT NOT NULL,             -- 'Mobile App', 'Pricing Policy'
    description TEXT
);

-- 4. Справочник: Тональность (Sentiment)
-- Источник: [cite: 39]
CREATE TABLE IF NOT EXISTS sentiment_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,      -- 'friendly', 'anxious', 'angry'
    name TEXT NOT NULL
);

-- 5. Сырые посты (Raw Posts)
-- Источник: [cite: 34]
CREATE TABLE IF NOT EXISTS raw_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fb_post_id TEXT UNIQUE NOT NULL, -- Уникальный ID из Facebook
    content TEXT,                    -- Текст поста
    reaction_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 6. Сырые комментарии (Raw Comments)
-- Источник: [cite: 35]
CREATE TABLE IF NOT EXISTS raw_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fb_comment_id TEXT UNIQUE NOT NULL,
    post_id INTEGER NOT NULL,          -- Ссылка на родительский пост
    parent_comment_id INTEGER,         -- Ссылка на родительский коммент (для веток ответов)
    author_name TEXT,                  -- Имя автора (для отображения в UI)
    content TEXT,                      -- Оригинальный текст на сомалийском
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Связи
    FOREIGN KEY (post_id) REFERENCES raw_posts(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES raw_comments(id) ON DELETE SET NULL
);

-- 7. Обработанные данные (Processed Intelligence)
-- Источник: [cite: 36]
CREATE TABLE IF NOT EXISTS processed_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- СВЯЗЬ 1-К-1: Ссылка на сырой комментарий
    -- UNIQUE гарантирует, что у одного сырого коммента только одна аналитика
    raw_comment_id INTEGER NOT NULL UNIQUE,
    
    -- Ссылки на справочники (Нормализация)
    category_id INTEGER,
    sentiment_id INTEGER,
    threat_level_id INTEGER,
    
    -- Результаты работы AI
    translation_en TEXT,               -- Перевод на английский
    confidence_score REAL,             -- Вероятность (например, 0.98)
    dialect TEXT,                      -- 'Maxa-tiri' или 'Maay' [cite: 36]
    keywords JSON,                     -- Список слов: ["scam", "error"]
    
    -- Статус проверки человеком (Human-in-the-loop)
    is_reviewed BOOLEAN DEFAULT 0,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Внешние ключи
    FOREIGN KEY (raw_comment_id) REFERENCES raw_comments(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES complaint_categories(id),
    FOREIGN KEY (sentiment_id) REFERENCES sentiment_types(id),
    FOREIGN KEY (threat_level_id) REFERENCES threat_levels(id)
);

-- ==========================================
-- ЧАСТЬ 2: НАПОЛНЕНИЕ ДАННЫМИ (SEED DATA)
-- ==========================================

-- 1. Заполняем Threat Levels [cite: 82]
INSERT OR IGNORE INTO threat_levels (slug, name, color_code) VALUES 
('nominal', 'Nominal', '#10B981'),    -- Зеленый (Спокойно)
('elevated', 'Elevated', '#F59E0B'),  -- Оранжевый (Требует внимания)
('critical', 'Critical', '#EF4444');  -- Красный (Алерт!)

-- 2. Заполняем Sentiment Types [cite: 39]
INSERT OR IGNORE INTO sentiment_types (slug, name) VALUES 
('friendly', 'Friendly'),
('anxious', 'Anxious'),
('angry', 'Angry');

-- 3. Заполняем Complaint Categories [cite: 38]
INSERT OR IGNORE INTO complaint_categories (slug, name) VALUES 
('support_service', 'Support Service'),
('offline_branch', 'Offline Branch'),
('mobile_app', 'Mobile App'),
('website', 'Website'),
('pricing_policy', 'Pricing Policy');

-- 4. Создаем тестового админа (опционально)
INSERT OR IGNORE INTO users (email) VALUES ('admin@gaado.bank');

-- ==========================================
-- ЧАСТЬ 3: ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_documents_created_at 
ON documents(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_scraping_results_fetched_at 
ON scraping_results(fetched_at DESC);

CREATE INDEX IF NOT EXISTS idx_scraping_results_page_username 
ON scraping_results(page_username);

CREATE INDEX IF NOT EXISTS idx_scraping_status_status 
ON scraping_status(status);

CREATE INDEX IF NOT EXISTS idx_scraping_status_started_at 
ON scraping_status(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_complaint_categories_slug 
ON complaint_categories(slug);

CREATE INDEX IF NOT EXISTS idx_sentiment_types_slug 
ON sentiment_types(slug);

CREATE INDEX IF NOT EXISTS idx_threat_levels_slug 
ON threat_levels(slug);

CREATE INDEX IF NOT EXISTS idx_raw_posts_fb_post_id 
ON raw_posts(fb_post_id);

CREATE INDEX IF NOT EXISTS idx_raw_posts_scraped_at 
ON raw_posts(scraped_at DESC);

CREATE INDEX IF NOT EXISTS idx_raw_comments_fb_comment_id 
ON raw_comments(fb_comment_id);

CREATE INDEX IF NOT EXISTS idx_raw_comments_post_id 
ON raw_comments(post_id);

CREATE INDEX IF NOT EXISTS idx_raw_comments_parent_comment_id 
ON raw_comments(parent_comment_id);

CREATE INDEX IF NOT EXISTS idx_raw_comments_created_at 
ON raw_comments(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_processed_comments_raw_comment_id 
ON processed_comments(raw_comment_id);

CREATE INDEX IF NOT EXISTS idx_processed_comments_category_id 
ON processed_comments(category_id);

CREATE INDEX IF NOT EXISTS idx_processed_comments_sentiment_id 
ON processed_comments(sentiment_id);

CREATE INDEX IF NOT EXISTS idx_processed_comments_threat_level_id 
ON processed_comments(threat_level_id);

CREATE INDEX IF NOT EXISTS idx_processed_comments_is_reviewed 
ON processed_comments(is_reviewed);

CREATE INDEX IF NOT EXISTS idx_processed_comments_processed_at 
ON processed_comments(processed_at DESC);

CREATE INDEX IF NOT EXISTS idx_users_email 
ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_session_token 
ON users(session_token);
