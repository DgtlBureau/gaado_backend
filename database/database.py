"""
Database module for Supabase
Provides abstraction layer for Supabase operations
"""
import logging
import os
from typing import Optional, Any
from dotenv import load_dotenv

try:
    from supabase import create_client, Client  # type: ignore
    from supabase.client import ClientOptions  # type: ignore
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None  # type: ignore
    Client = None  # type: ignore
    ClientOptions = None  # type: ignore

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)


class Database:
    """
    Database wrapper for Supabase
    
    Provides Supabase client for database and storage operations
    """
    
    def __init__(self):
        """
        Initialize Supabase client
        
        Automatically initializes Supabase client using environment variables from .env file.
        """
        self._supabase_client: Optional[Any] = None  # type: ignore
        
        # Auto-initialize Supabase client if credentials available
        if SUPABASE_AVAILABLE and create_client is not None:
            self._init_supabase_client()
    
    def _init_supabase_client(self):
        """Initialize Supabase client if credentials are available"""
        if self._supabase_client is not None:
            return
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if supabase_url and supabase_key and SUPABASE_AVAILABLE and create_client is not None:
            try:
                if ClientOptions is not None:
                    self._supabase_client = create_client(
                        supabase_url,
                        supabase_key,
                        # options=ClientOptions(
                        #     postgrest_client_timeout=10,
                        #     storage_client_timeout=10,
                        #     schema="public",
                        # )
                    )
                else:
                    self._supabase_client = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Supabase client: {e}")

    @property
    def supabase(self) -> Optional[Any]:  # type: ignore
        """
        Get Supabase client instance
        
        Returns:
            Supabase Client if initialized, None otherwise
        """
        return self._supabase_client

# Global database instance (will be set during app startup)
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """Get database instance"""
    global _db_instance
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance


def init_database() -> Database:
    """
    Initialize database instance for Supabase
    
    Returns:
        Database instance (automatically initializes Supabase client)
    """
    global _db_instance
    
    _db_instance = Database()
    return _db_instance
