"""Cache cleaner module for OpenMark.

This module provides automatic cleanup of cached PDF files
based on the configured cache duration.
"""

import os
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class CacheCleaner:
    """Background cache cleaner that removes expired PDF files."""
    
    _instance: Optional['CacheCleaner'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one cleaner runs."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, cache_dir: str, duration_seconds: int, temp_documents: dict):
        """Initialize the cache cleaner.
        
        Args:
            cache_dir: Absolute path to the cache directory
            duration_seconds: Cache duration in seconds
            temp_documents: Reference to the temp_documents dict from api.py
        """
        if self._initialized:
            return
            
        self.cache_dir = cache_dir
        self.duration_seconds = duration_seconds
        self.temp_documents = temp_documents
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._initialized = True
        
        logger.info(f"CacheCleaner initialized: dir={cache_dir}, duration={duration_seconds}s")
    
    def start(self):
        """Start the background cleanup thread."""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("CacheCleaner is already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._thread.start()
        logger.info(f"CacheCleaner started, will run every {self.duration_seconds} seconds")
    
    def stop(self):
        """Stop the background cleanup thread."""
        if self._thread is None:
            return
        
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None
        logger.info("CacheCleaner stopped")
    
    def _cleanup_loop(self):
        """Main cleanup loop running in background thread."""
        while not self._stop_event.is_set():
            try:
                self._perform_cleanup()
            except Exception as e:
                logger.error(f"Error during cache cleanup: {e}")
            
            # Wait for the next cycle
            self._stop_event.wait(timeout=self.duration_seconds)
    
    def _perform_cleanup(self):
        """Perform the actual cleanup of expired cache files."""
        if not os.path.exists(self.cache_dir):
            return
        
        now = datetime.utcnow()
        expired_count = 0
        cleaned_count = 0
        
        # Get list of expired temp_documents
        expired_docs = []
        for temp_doc_id, doc_info in list(self.temp_documents.items()):
            try:
                expires_at = datetime.fromisoformat(doc_info['expires_at'].rstrip('Z'))
                if now > expires_at:
                    expired_docs.append(temp_doc_id)
            except (KeyError, ValueError) as e:
                logger.warning(f"Invalid doc_info for {temp_doc_id}: {e}")
                expired_docs.append(temp_doc_id)
        
        # Remove expired entries from temp_documents and delete cache files
        for temp_doc_id in expired_docs:
            # Remove from temp_documents
            if temp_doc_id in self.temp_documents:
                del self.temp_documents[temp_doc_id]
                expired_count += 1
            
            # Delete cache file
            cache_file = os.path.join(self.cache_dir, f"{temp_doc_id}.pdf")
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    cleaned_count += 1
                    logger.debug(f"Deleted expired cache file: {cache_file}")
                except OSError as e:
                    logger.error(f"Failed to delete cache file {cache_file}: {e}")
        
        # Also clean orphan PDF files (files without corresponding temp_documents entry)
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.pdf') and filename.startswith('temp_'):
                temp_doc_id = filename[:-4]  # Remove .pdf extension
                if temp_doc_id not in self.temp_documents:
                    cache_file = os.path.join(self.cache_dir, filename)
                    # Check file age
                    try:
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
                        if (datetime.now() - file_mtime).total_seconds() > self.duration_seconds:
                            os.remove(cache_file)
                            cleaned_count += 1
                            logger.debug(f"Deleted orphan cache file: {cache_file}")
                    except OSError as e:
                        logger.error(f"Failed to process orphan file {cache_file}: {e}")
        
        if expired_count > 0 or cleaned_count > 0:
            logger.info(f"Cache cleanup: {expired_count} expired documents, {cleaned_count} files deleted")
    
    def is_running(self) -> bool:
        """Check if the cleaner is currently running."""
        return self._thread is not None and self._thread.is_alive()


# Global instance
_cache_cleaner: Optional[CacheCleaner] = None


def init_cache_cleaner(app) -> CacheCleaner:
    """Initialize and start the cache cleaner for the Flask app.
    
    Args:
        app: Flask application instance
        
    Returns:
        CacheCleaner instance
    """
    global _cache_cleaner
    
    from app.routes.api import temp_documents
    
    config = app.config['CONFIG']
    cache_dir_config = config.cache.get('directory', './cache')
    duration_seconds = config.cache.get('duration_seconds', 3600)
    
    # Build absolute path
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(app_root, cache_dir_config.lstrip('./'))
    
    # Create cache directory if it doesn't exist
    os.makedirs(cache_dir, exist_ok=True)
    
    _cache_cleaner = CacheCleaner(cache_dir, duration_seconds, temp_documents)
    _cache_cleaner.start()
    
    return _cache_cleaner


def get_cache_cleaner() -> Optional[CacheCleaner]:
    """Get the global cache cleaner instance."""
    return _cache_cleaner
