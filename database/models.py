"""
Database models for Gaado Backend
Pydantic models matching database schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProcessedComment(BaseModel):
    """
    Model for processed_comments table
    Matches schema from database/schema.sql
    """
    # Primary key (set by database)
    id: Optional[int] = None
    
    # Required: Reference to raw comment
    raw_comment_id: int = Field(..., description="ID of the raw comment (ONE-TO-ONE relationship)")
    
    # References to reference tables (Normalization) - stored as IDs in DB, but can accept slugs
    category_id: Optional[int] = Field(default=None, description="Reference to complaint_categories.id")
    sentiment_id: Optional[int] = Field(default=None, description="Reference to sentiment_types.id")
    threat_level_id: Optional[int] = Field(default=None, description="Reference to threat_levels.id")
    
    # AI processing results
    translation_en: Optional[str] = Field(default=None, description="English translation of the comment")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="AI confidence score (0.0-1.0)")
    dialect: Optional[str] = Field(default=None, description="Dialect detected ('Maxa-tiri' or 'Maay')")
    keywords: Optional[List[str]] = Field(default=None, description="List of extracted keywords")
    risk: Optional[str] = Field(default=None, description="Risk assessment string from AI")
    model_name: Optional[str] = Field(default=None, description="Model name used for processing")
    
    # Human review status
    is_reviewed: bool = Field(default=False, description="Whether the comment has been reviewed by human")
    
    # Timestamp (set by database)
    processed_at: Optional[datetime] = None
    
    class Config:
        """Pydantic config"""
        json_schema_extra = {
            "example": {
                "raw_comment_id": 1,
                "translation_en": "This is an English translation",
                "confidence_score": 0.95,
                "dialect": "Maxa-tiri",
                "keywords": ["scam", "error"],
                "threat_level_id": 1,
                "risk": "reputation/service risk",
                "is_reviewed": False
            }
        }


class ProcessedCommentCreate(BaseModel):
    """
    Model for creating a processed comment
    Accepts slugs for reference tables (will be converted to IDs)
    """
    raw_comment_id: Optional[int] = Field(default=None, description="ID of the raw comment (will be set before saving)")
    
    # Can accept slugs for reference tables
    category_slug: Optional[str] = Field(default=None, description="Slug of the complaint category")
    sentiment_slug: Optional[str] = Field(default=None, description="Slug of the sentiment type")
    threat_level_slug: Optional[str] = Field(default=None, description="Slug of the threat level")
    
    # AI processing results
    translation_en: Optional[str] = Field(default=None, description="English translation of the comment")
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="AI confidence score (0.0-1.0)")
    dialect: Optional[str] = Field(default=None, description="Dialect detected ('Maxa-tiri' or 'Maay')")
    keywords: Optional[List[str]] = Field(default=None, description="List of extracted keywords")
    risk: Optional[str] = Field(default=None, description="Risk assessment string from AI")
    model_name: Optional[str] = Field(default=None, description="Model name used for processing")
    
    # Human review status
    is_reviewed: bool = Field(default=False, description="Whether the comment has been reviewed by human")


class SaveProcessedCommentRequest(BaseModel):
    """Model for saving processed comment to database"""
    fb_comment_id: str = Field(..., description="Facebook comment ID")
    post_id: int = Field(..., description="Post ID")
    translation_en: Optional[str] = Field(default=None, description="English translation")
    threat_level_slug: Optional[str] = Field(default=None, description="Threat level slug")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score")
    dialect: Optional[str] = Field(default=None, description="Dialect")
    keywords: Optional[List[str]] = Field(default=None, description="Keywords")
    somali_text: Optional[str] = Field(default=None, description="Original Somali text")
    risk: Optional[str] = Field(default=None, description="Risk assessment string")
    model_name: Optional[str] = Field(default=None, description="Model name used for processing")

