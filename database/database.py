"""
Database module for Supabase PostgreSQL
Provides abstraction layer for database operations
Uses psycopg2 for synchronous operations and Supabase client for Storage
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import asyncpg  # type: ignore

try:
    import psycopg2  # type: ignore
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    psycopg2 = None  # type: ignore

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
    Database wrapper for Supabase PostgreSQL
    
    Uses psycopg2 for synchronous database operations
    Provides Supabase client for Storage (photos/files)
    Also supports asyncpg for async operations if needed
    """
    
    def __init__(self):
        """
        Initialize database connection for Supabase
        
        Automatically connects via psycopg2 and initializes Supabase client.
        Uses environment variables from .env file.
        """
        self.pool = None
        self._supabase_client: Optional[Any] = None  # type: ignore
        self._psycopg2_connection = None
        
        # Auto-connect psycopg2 (for Supabase)
        # if PSYCOPG2_AVAILABLE:
        #     try:
        #         self._connect_psycopg2()
        #     except Exception as e:
        #         logger.warning(f"Failed to auto-connect psycopg2: {e}")
        
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
                        options=ClientOptions(
                            postgrest_client_timeout=10,
                            storage_client_timeout=10,
                            schema="public",
                        )
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
        Database instance (automatically connects via psycopg2 and initializes Supabase client)
    """
    global _db_instance
    
    _db_instance = Database()
    return _db_instance

def close(self):
    """Cleanup Supabase client"""
    
    # Supabase client doesn't need explicit cleanup, but we can reset it
    self._supabase_client = None
