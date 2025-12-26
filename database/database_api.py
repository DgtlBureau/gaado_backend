"""
Database API module for Supabase operations
Provides high-level methods for working with Supabase Storage and Database
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from database.database import get_database

logger = logging.getLogger(__name__)


def get_latest_comments(limit: int = 50, offset: int = 0, 
                       is_reviewed: Optional[bool] = None) -> List[Dict[str, Any]]:
    """
    Get latest processed comments from database with joined data from raw_comments and reference tables
    
    Args:
        limit: Maximum number of comments to return (default: 50)
        offset: Number of comments to skip (default: 0)
        is_reviewed: Filter by review status (None = all, True = reviewed only, False = unreviewed only)
    
    Returns:
        List of comment dictionaries with all fields including joined data
    """
    try:
        request_start_time = datetime.now()
        db = get_database()
        supabase = db.supabase
        
        if supabase is None:
            logger.error("Supabase client is not initialized")
            return []
        
        logger.info(f"[SUPABASE] Fetching comments from Supabase (limit={limit}, offset={offset}) at {request_start_time.isoformat()}")
        
        # Build query with joins to get related data
        # Join with raw_comments, complaint_categories, sentiment_types, and threat_levels
        # Supabase PostgREST syntax: table_name!foreign_key_column(*)
        query = (
            supabase.table("processed_comments")
            .select("""
                *,
                raw_comments!raw_comment_id(*),
                complaint_categories!category_id(slug, name),
                sentiment_types!sentiment_id(slug, name),
                threat_levels!threat_level_id(slug, name, color_code)
            """)
        )
        
        # Add filter if needed
        if is_reviewed is not None:
            query = query.eq("is_reviewed", is_reviewed)
        
        # Add ordering, limit and offset
        response = (
            query
            .order("processed_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        
        request_end_time = datetime.now()
        request_duration = (request_end_time - request_start_time).total_seconds()
        
        comments = response.data if hasattr(response, 'data') else []
        logger.info(f"[SUPABASE] Successfully fetched {len(comments)} comments in {request_duration:.3f}s at {request_end_time.isoformat()}")
        
        # Flatten the nested structure for easier access
        flattened_comments = []
        for comment in comments:
            flattened = dict(comment)
            
            # Extract raw_comments data (Supabase returns it as a list or dict)
            raw_comments_data = comment.get("raw_comments")
            if isinstance(raw_comments_data, list) and len(raw_comments_data) > 0:
                raw_comment = raw_comments_data[0]
            elif isinstance(raw_comments_data, dict):
                raw_comment = raw_comments_data
            else:
                raw_comment = {}
            
            if isinstance(raw_comment, dict):
                flattened["author_name"] = raw_comment.get("author_name")
                flattened["content"] = raw_comment.get("content")
                flattened["created_at"] = raw_comment.get("created_at")
                flattened["fb_comment_id"] = raw_comment.get("fb_comment_id")
            
            # Extract complaint_categories data
            categories_data = comment.get("complaint_categories")
            if isinstance(categories_data, list) and len(categories_data) > 0:
                category = categories_data[0]
            elif isinstance(categories_data, dict):
                category = categories_data
            else:
                category = {}
            
            if isinstance(category, dict):
                flattened["category_slug"] = category.get("slug")
                flattened["category_name"] = category.get("name")
            
            # Extract sentiment_types data
            sentiments_data = comment.get("sentiment_types")
            if isinstance(sentiments_data, list) and len(sentiments_data) > 0:
                sentiment = sentiments_data[0]
            elif isinstance(sentiments_data, dict):
                sentiment = sentiments_data
            else:
                sentiment = {}
            
            if isinstance(sentiment, dict):
                flattened["sentiment_slug"] = sentiment.get("slug")
                flattened["sentiment_name"] = sentiment.get("name")
            
            # Extract threat_levels data
            threat_levels_data = comment.get("threat_levels")
            if isinstance(threat_levels_data, list) and len(threat_levels_data) > 0:
                threat_level = threat_levels_data[0]
            elif isinstance(threat_levels_data, dict):
                threat_level = threat_levels_data
            else:
                threat_level = {}
            
            if isinstance(threat_level, dict):
                flattened["threat_level_slug"] = threat_level.get("slug")
                flattened["threat_level_name"] = threat_level.get("name")
                flattened["threat_level_color"] = threat_level.get("color_code")
            
            flattened_comments.append(flattened)
        
        logger.info(f"[SUPABASE] Retrieved {len(flattened_comments)} comments (flattened)")
        
        return flattened_comments
        
    except Exception as e:
        logger.error(f"[SUPABASE] Error getting latest comments: {e}", exc_info=True)
        return []


def add_raw_comment(fb_comment_id: str, post_id: int, author_name: Optional[str] = None,
                   content: Optional[str] = None, parent_comment_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Add a raw comment to the database
    
    Args:
        fb_comment_id: Unique Facebook comment ID
        post_id: ID of the parent post
        author_name: Name of the comment author
        content: Comment text content
        parent_comment_id: ID of parent comment (for reply threads)
    
    Returns:
        Dictionary with inserted comment data or None if error
    """
    try:
        db = get_database()
        supabase = db.supabase
        
        if supabase is None:
            logger.error("Supabase client is not initialized")
            return None
        
        comment_data = {
            "fb_comment_id": fb_comment_id,
            "post_id": post_id,
            "author_name": author_name,
            "content": content,
            "parent_comment_id": parent_comment_id
        }
        
        response = (
            supabase.table("raw_comments")
            .insert([comment_data])
            .execute()
        )
        
        result = response.data[0] if response.data else None
        logger.info(f"Raw comment added: {fb_comment_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error adding raw comment: {e}")
        return None


def add_processed_comment(raw_comment_id: int, translation_en: Optional[str] = None,
                         category_slug: Optional[str] = None, sentiment_slug: Optional[str] = None,
                         threat_level_slug: Optional[str] = None, confidence_score: Optional[float] = None,
                         dialect: Optional[str] = None, keywords: Optional[List[str]] = None,
                         is_reviewed: bool = False) -> Optional[Dict[str, Any]]:
    """
    Add a processed comment to the database
    
    Args:
        raw_comment_id: ID of the raw comment
        translation_en: English translation of the comment
        category_slug: Slug of the complaint category
        sentiment_slug: Slug of the sentiment type
        threat_level_slug: Slug of the threat level
        confidence_score: AI confidence score (0.0-1.0)
        dialect: Dialect detected ('Maxa-tiri' or 'Maay')
        keywords: List of keywords extracted
        is_reviewed: Whether the comment has been reviewed by human
    
    Returns:
        Dictionary with inserted processed comment data or None if error
    """
    try:
        db = get_database()
        supabase = db.supabase
        
        if supabase is None:
            logger.error("Supabase client is not initialized")
            return None
        
        # Get reference IDs from slugs if provided
        category_id = None
        sentiment_id = None
        threat_level_id = None
        
        if category_slug:
            cat_result = (
                supabase.table("complaint_categories")
                .select("id")
                .eq("slug", category_slug)
                .execute()
            )
            if cat_result.data:
                category_id = cat_result.data[0]["id"]
        
        if sentiment_slug:
            sent_result = (
                supabase.table("sentiment_types")
                .select("id")
                .eq("slug", sentiment_slug)
                .execute()
            )
            if sent_result.data:
                sentiment_id = sent_result.data[0]["id"]
        
        if threat_level_slug:
            threat_result = (
                supabase.table("threat_levels")
                .select("id")
                .eq("slug", threat_level_slug)
                .execute()
            )
            if threat_result.data:
                threat_level_id = threat_result.data[0]["id"]
        
        comment_data = {
            "raw_comment_id": raw_comment_id,
            "category_id": category_id,
            "sentiment_id": sentiment_id,
            "threat_level_id": threat_level_id,
            "translation_en": translation_en,
            "confidence_score": confidence_score,
            "dialect": dialect,
            "keywords": keywords or [],
            "is_reviewed": is_reviewed
        }
        
        response = (
            supabase.table("processed_comments")
            .insert([comment_data])
            .execute()
        )
        
        result = response.data[0] if response.data else None
        logger.info(f"Processed comment added for raw_comment_id: {raw_comment_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error adding processed comment: {e}")
        return None


def add_comment_with_processing(fb_comment_id: str, post_id: int, 
                                author_name: Optional[str] = None, content: Optional[str] = None,
                                parent_comment_id: Optional[int] = None,
                                translation_en: Optional[str] = None,
                                category_slug: Optional[str] = None, 
                                sentiment_slug: Optional[str] = None,
                                threat_level_slug: Optional[str] = None,
                                confidence_score: Optional[float] = None,
                                dialect: Optional[str] = None,
                                keywords: Optional[List[str]] = None,
                                is_reviewed: bool = False) -> Optional[Dict[str, Any]]:
    """
    Add both raw comment and processed comment in one operation
    
    Args:
        fb_comment_id: Unique Facebook comment ID
        post_id: ID of the parent post
        author_name: Name of the comment author
        content: Comment text content
        parent_comment_id: ID of parent comment (for reply threads)
        translation_en: English translation of the comment
        category_slug: Slug of the complaint category
        sentiment_slug: Slug of the sentiment type
        threat_level_slug: Slug of the threat level
        confidence_score: AI confidence score (0.0-1.0)
        dialect: Dialect detected ('Maxa-tiri' or 'Maay')
        keywords: List of keywords extracted
        is_reviewed: Whether the comment has been reviewed by human
    
    Returns:
        Dictionary with both raw and processed comment data or None if error
    """
    try:
        # First add raw comment
        raw_comment = add_raw_comment(
            fb_comment_id=fb_comment_id,
            post_id=post_id,
            author_name=author_name,
            content=content,
            parent_comment_id=parent_comment_id
        )
        
        if not raw_comment:
            logger.error("Failed to add raw comment")
            return None
        
        raw_comment_id = raw_comment["id"]
        
        # Then add processed comment
        processed_comment = add_processed_comment(
            raw_comment_id=raw_comment_id,
            translation_en=translation_en,
            category_slug=category_slug,
            sentiment_slug=sentiment_slug,
            threat_level_slug=threat_level_slug,
            confidence_score=confidence_score,
            dialect=dialect,
            keywords=keywords,
            is_reviewed=is_reviewed
        )
        
        if not processed_comment:
            logger.error("Failed to add processed comment")
            return None
        
        return {
            "raw_comment": raw_comment,
            "processed_comment": processed_comment
        }
        
    except Exception as e:
        logger.error(f"Error adding comment with processing: {e}")
        return None

