"""
CDN/Storage operations module for Supabase
Provides functions for working with photos and files in Supabase Storage
"""
import logging
from typing import Dict, Any, List, Optional
from database.database import get_database

logger = logging.getLogger(__name__)


# ========== Supabase Storage Operations (Photos) ==========

def upload_photo(bucket_name: str, file_path: str, file_data: bytes, 
                 content_type: str = "image/jpeg", file_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Upload a photo to Supabase Storage
    
    Args:
        bucket_name: Name of the storage bucket
        file_path: Path where the file will be stored (e.g., 'photos/image.jpg')
        file_data: Binary file data
        content_type: MIME type of the file (default: 'image/jpeg')
        file_options: Optional file options (cache_control, upsert, etc.)
    
    Returns:
        Dictionary with upload result including path and public URL
    """
    db = get_database()
    return db.upload_photo(bucket_name, file_path, file_data, content_type, file_options)  # type: ignore


def download_photo(bucket_name: str, file_path: str) -> bytes:
    """
    Download a photo from Supabase Storage
    
    Args:
        bucket_name: Name of the storage bucket
        file_path: Path to the file in storage
    
    Returns:
        Binary file data
    """
    db = get_database()
    return db.download_photo(bucket_name, file_path)  # type: ignore


def get_photo_url(bucket_name: str, file_path: str, signed: bool = False, 
                 expires_in: int = 3600) -> str:
    """
    Get public or signed URL for a photo
    
    Args:
        bucket_name: Name of the storage bucket
        file_path: Path to the file in storage
        signed: If True, generate a signed URL (for private files)
        expires_in: Expiration time in seconds for signed URLs (default: 3600)
    
    Returns:
        Public or signed URL string
    """
    db = get_database()
    return db.get_photo_url(bucket_name, file_path, signed, expires_in)  # type: ignore


def delete_photo(bucket_name: str, file_paths: List[str]) -> Dict[str, Any]:
    """
    Delete one or more photos from Supabase Storage
    
    Args:
        bucket_name: Name of the storage bucket
        file_paths: List of file paths to delete
    
    Returns:
        Dictionary with deletion result
    """
    db = get_database()
    return db.delete_photo(bucket_name, file_paths)  # type: ignore


def list_photos(bucket_name: str, folder_path: Optional[str] = None, 
               limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    List photos in a Supabase Storage bucket
    
    Args:
        bucket_name: Name of the storage bucket
        folder_path: Optional folder path to list files from
        limit: Maximum number of files to return
        offset: Number of files to skip
    
    Returns:
        List of file dictionaries with metadata
    """
    db = get_database()
    return db.list_photos(bucket_name, folder_path, limit, offset)  # type: ignore


def create_bucket(bucket_name: str, public: bool = True) -> Dict[str, Any]:
    """
    Create a new storage bucket in Supabase
    
    Args:
        bucket_name: Name of the bucket to create
        public: If True, bucket will be publicly accessible
    
    Returns:
        Dictionary with creation result
    """
    db = get_database()
    return db.create_bucket(bucket_name, public)  # type: ignore
