-- PostgreSQL Database Schema for Gaado Backend
-- This schema is automatically created by the application, but can be used for manual setup

-- ==========================================
-- PART 1: STRUCTURE (DDL)
-- ==========================================

-- 1. Users (Admins)
-- Source: [cite: 33]
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    session_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Reference: Threat Levels
-- Source: [cite: 82]
CREATE TABLE IF NOT EXISTS threat_levels (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,      -- 'nominal', 'elevated', 'critical'
    name TEXT NOT NULL,             -- 'Nominal', 'Elevated', 'Critical'
    color_code TEXT,                -- '#10B981' (for UI Shadcn)
    description TEXT
);

-- 3. Reference: Complaint Categories (Taxonomy)
-- Source: [cite: 37, 38]
CREATE TABLE IF NOT EXISTS complaint_categories (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,      -- 'mobile_app', 'pricing_policy'
    name TEXT NOT NULL,             -- 'Mobile App', 'Pricing Policy'
    description TEXT
);

-- 4. Reference: Sentiment Types
-- Source: [cite: 39]
CREATE TABLE IF NOT EXISTS sentiment_types (
    id SERIAL PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,      -- 'friendly', 'anxious', 'angry'
    name TEXT NOT NULL
);

-- 5. Raw Posts
-- Source: [cite: 34]
CREATE TABLE IF NOT EXISTS raw_posts (
    id SERIAL PRIMARY KEY,
    fb_post_id TEXT UNIQUE NOT NULL, -- Unique ID from Facebook
    content TEXT,                    -- Post text
    reaction_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Raw Comments
-- Source: [cite: 35]
CREATE TABLE IF NOT EXISTS raw_comments (
    id SERIAL PRIMARY KEY,
    fb_comment_id TEXT UNIQUE NOT NULL,
    post_id INTEGER NOT NULL,          -- Reference to parent post
    parent_comment_id INTEGER,         -- Reference to parent comment (for reply threads)
    author_name TEXT,                  -- Author name (for UI display)
    content TEXT,                      -- Original text in Somali
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (post_id) REFERENCES raw_posts(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_comment_id) REFERENCES raw_comments(id) ON DELETE SET NULL
);

-- 7. Processed Data (Processed Intelligence)
-- Source: [cite: 36]
CREATE TABLE IF NOT EXISTS processed_comments (
    id SERIAL PRIMARY KEY,
    
    -- ONE-TO-ONE RELATIONSHIP: Reference to raw comment
    -- UNIQUE ensures that one raw comment has only one analytics record
    raw_comment_id INTEGER NOT NULL UNIQUE,
    
    -- References to reference tables (Normalization)
    category_id INTEGER,
    sentiment_id INTEGER,
    threat_level_id INTEGER,
    
    -- AI processing results
    translation_en TEXT,               -- English translation
    confidence_score REAL,             -- Probability (e.g., 0.98)
    dialect TEXT,                      -- 'Maxa-tiri' or 'Maay' [cite: 36]
    keywords JSONB,                    -- List of words: ["scam", "error"]
    risk TEXT,                         -- Risk assessment string from AI
    model_name TEXT,                   -- Model name used for processing (e.g., "Qwen/Qwen2.5-7B-Instruct:together")
    
    -- Human review status (Human-in-the-loop)
    is_reviewed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (raw_comment_id) REFERENCES raw_comments(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES complaint_categories(id),
    FOREIGN KEY (sentiment_id) REFERENCES sentiment_types(id),
    FOREIGN KEY (threat_level_id) REFERENCES threat_levels(id)
);

-- ==========================================
-- PART 2: SEED DATA
-- ==========================================

-- 1. Populate Threat Levels [cite: 82]
INSERT INTO threat_levels (slug, name, color_code) VALUES 
('nominal', 'Nominal', '#10B981'),    -- Green (Calm)
('elevated', 'Elevated', '#F59E0B'),  -- Orange (Requires attention)
('critical', 'Critical', '#EF4444')  -- Red (Alert!)
ON CONFLICT (slug) DO NOTHING;

-- 2. Populate Sentiment Types [cite: 39]
INSERT INTO sentiment_types (slug, name) VALUES 
('friendly', 'Friendly'),
('anxious', 'Anxious'),
('angry', 'Angry')
ON CONFLICT (slug) DO NOTHING;

-- 3. Populate Complaint Categories [cite: 38]
INSERT INTO complaint_categories (slug, name) VALUES 
('support_service', 'Support Service'),
('offline_branch', 'Offline Branch'),
('mobile_app', 'Mobile App'),
('website', 'Website'),
('pricing_policy', 'Pricing Policy')
ON CONFLICT (slug) DO NOTHING;

-- 4. Create test admin (optional)
INSERT INTO users (email) VALUES ('admin@gaado.bank')
ON CONFLICT (email) DO NOTHING;

-- 5. Insert mock test data (raw posts, raw comments, and processed comments)
-- Source: database.py lines 807-848

-- Create mock post
INSERT INTO raw_posts (fb_post_id, content, reaction_count, share_count) VALUES 
('mock_post_001', 'Mock Premier Bank Post for Testing', 0, 0)
ON CONFLICT (fb_post_id) DO NOTHING;

-- Insert raw comments
INSERT INTO raw_comments (fb_comment_id, post_id, author_name, content, parent_comment_id)
SELECT 
    'mock_comment_001',
    (SELECT id FROM raw_posts WHERE fb_post_id = 'mock_post_001'),
    'Mock User 1',
    'Hhhh xayeysiin aa Hees cml udhagaystay xayeysiin Raab ah Faraska Madow waxuu la cadaan wayey hal abuur waye',
    NULL
WHERE NOT EXISTS (SELECT 1 FROM raw_comments WHERE fb_comment_id = 'mock_comment_001');

INSERT INTO raw_comments (fb_comment_id, post_id, author_name, content, parent_comment_id)
SELECT 
    'mock_comment_002',
    (SELECT id FROM raw_posts WHERE fb_post_id = 'mock_post_001'),
    'Mock User 2',
    'Waa bankiga kaliya ee dadkiisa cilada heesato ku xaliyo ka wada bax dib usoo bilaaw tirtir ee dib usoo daji',
    NULL
WHERE NOT EXISTS (SELECT 1 FROM raw_comments WHERE fb_comment_id = 'mock_comment_002');

INSERT INTO raw_comments (fb_comment_id, post_id, author_name, content, parent_comment_id)
SELECT 
    'mock_comment_003',
    (SELECT id FROM raw_posts WHERE fb_post_id = 'mock_post_001'),
    'Mock User 3',
    'Maalinka aad deposit ATM aduunka laga samen karo aad kentaan ayaad top 1 noqondontaan',
    NULL
WHERE NOT EXISTS (SELECT 1 FROM raw_comments WHERE fb_comment_id = 'mock_comment_003');

INSERT INTO raw_comments (fb_comment_id, post_id, author_name, content, parent_comment_id)
SELECT 
    'mock_comment_004',
    (SELECT id FROM raw_posts WHERE fb_post_id = 'mock_post_001'),
    'Mock User 4',
    'Premier Bank Wah Xaaladiina Xayeysiiska inta may maroysaa Okei dhib ma lehee teamka Xayeysiinta idin Sameysey Jeebka ma u qoyseen ama qado ley u dalab teen Masaakiinta BaL Clip HaLaga soo duuwo ayagoo Shilimaadkooda la siinaayo si VAR-KA aynu u xaqiijino',
    NULL
WHERE NOT EXISTS (SELECT 1 FROM raw_comments WHERE fb_comment_id = 'mock_comment_004');

INSERT INTO raw_comments (fb_comment_id, post_id, author_name, content, parent_comment_id)
SELECT 
    'mock_comment_005',
    (SELECT id FROM raw_posts WHERE fb_post_id = 'mock_post_001'),
    'Mock User 5',
    'Bangiga kaliya Cilada ku heysato ku xaliyo cilad kale',
    NULL
WHERE NOT EXISTS (SELECT 1 FROM raw_comments WHERE fb_comment_id = 'mock_comment_005');

INSERT INTO raw_comments (fb_comment_id, post_id, author_name, content, parent_comment_id)
SELECT 
    'mock_comment_006',
    (SELECT id FROM raw_posts WHERE fb_post_id = 'mock_post_001'),
    'Mock User 6',
    'Hadaan heestan xiftiyo tolow card bilaash ah ma leeyahay',
    NULL
WHERE NOT EXISTS (SELECT 1 FROM raw_comments WHERE fb_comment_id = 'mock_comment_006');

INSERT INTO raw_comments (fb_comment_id, post_id, author_name, content, parent_comment_id)
SELECT 
    'mock_comment_007',
    (SELECT id FROM raw_posts WHERE fb_post_id = 'mock_post_001'),
    'Mock User 7',
    'Aad baa u xayeesiin badan tihiin, aadna waad u liidataam!',
    NULL
WHERE NOT EXISTS (SELECT 1 FROM raw_comments WHERE fb_comment_id = 'mock_comment_007');

-- Insert processed comments
INSERT INTO processed_comments (raw_comment_id, threat_level_id, translation_en, confidence_score, dialect, keywords, is_reviewed)
SELECT 
    (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_001'),
    (SELECT id FROM threat_levels WHERE slug = 'nominal'),
    'Hahaha, I listened to an advertisement that was like a song, a Rap advertisement. Black Horse couldn''t make it clear, it is creativity.',
    0.95,
    'Maxa-tiri',
    '[]'::JSONB,
    FALSE
WHERE NOT EXISTS (SELECT 1 FROM processed_comments WHERE raw_comment_id = (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_001'));

INSERT INTO processed_comments (raw_comment_id, threat_level_id, translation_en, confidence_score, dialect, keywords, is_reviewed)
SELECT 
    (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_002'),
    (SELECT id FROM threat_levels WHERE slug = 'nominal'),
    'It''s the only bank that solves its customers'' technical issues by telling them to log out, restart, delete, and reinstall.',
    0.95,
    'Maxa-tiri',
    '[]'::JSONB,
    FALSE
WHERE NOT EXISTS (SELECT 1 FROM processed_comments WHERE raw_comment_id = (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_002'));

INSERT INTO processed_comments (raw_comment_id, threat_level_id, translation_en, confidence_score, dialect, keywords, is_reviewed)
SELECT 
    (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_003'),
    (SELECT id FROM threat_levels WHERE slug = 'nominal'),
    'The day you introduce international ATM deposits [deposits that can be done from the world], you will become number one.',
    0.98,
    'Maxa-tiri',
    '[]'::JSONB,
    FALSE
WHERE NOT EXISTS (SELECT 1 FROM processed_comments WHERE raw_comment_id = (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_003'));

INSERT INTO processed_comments (raw_comment_id, threat_level_id, translation_en, confidence_score, dialect, keywords, is_reviewed)
SELECT 
    (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_004'),
    (SELECT id FROM threat_levels WHERE slug = 'nominal'),
    'Premier Bank, what is the situation? Is this the extent of the advertising? Okay, no problem, but did you pay [wet the pockets of] the team that made the ad for you, or did you just order them lunch? The poor things, let a clip be filmed of them being paid their money so we can verify it via VAR.',
    0.95,
    'Maxa-tiri',
    '[]'::JSONB,
    FALSE
WHERE NOT EXISTS (SELECT 1 FROM processed_comments WHERE raw_comment_id = (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_004'));

INSERT INTO processed_comments (raw_comment_id, threat_level_id, translation_en, confidence_score, dialect, keywords, is_reviewed)
SELECT 
    (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_005'),
    (SELECT id FROM threat_levels WHERE slug = 'nominal'),
    'The only bank that solves the problem facing it with another problem.',
    0.95,
    'Maxa-tiri',
    '[]'::JSONB,
    FALSE
WHERE NOT EXISTS (SELECT 1 FROM processed_comments WHERE raw_comment_id = (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_005'));

INSERT INTO processed_comments (raw_comment_id, threat_level_id, translation_en, confidence_score, dialect, keywords, is_reviewed)
SELECT 
    (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_006'),
    (SELECT id FROM threat_levels WHERE slug = 'nominal'),
    'If I memorize this song, I wonder if I get a free card.',
    0.98,
    'Maxa-tiri',
    '[]'::JSONB,
    FALSE
WHERE NOT EXISTS (SELECT 1 FROM processed_comments WHERE raw_comment_id = (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_006'));

INSERT INTO processed_comments (raw_comment_id, threat_level_id, translation_en, confidence_score, dialect, keywords, is_reviewed)
SELECT 
    (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_007'),
    (SELECT id FROM threat_levels WHERE slug = 'nominal'),
    'You advertise very much, and you are very weak [incompetent]!',
    0.99,
    'Maxa-tiri',
    '[]'::JSONB,
    FALSE
WHERE NOT EXISTS (SELECT 1 FROM processed_comments WHERE raw_comment_id = (SELECT id FROM raw_comments WHERE fb_comment_id = 'mock_comment_007'));

-- ==========================================
-- PART 3: PERFORMANCE INDEXES
-- ==========================================

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
