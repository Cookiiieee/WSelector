"""Memory management utilities for WSelector application."""
import gc
import weakref
import psutil
import logging
import time
from typing import Callable, List, Set, Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages application memory usage and cleanup."""
    
    def __init__(self, max_memory_mb: int = 200, check_interval: int = 30):
        """Initialize memory manager.
        
        Args:
            max_memory_mb: Maximum allowed memory usage in MB
            check_interval: Interval in seconds between memory checks
        """
        self.max_memory_mb = max_memory_mb
        self.check_interval = check_interval
        self._last_check = 0
        self._tracked_resources: List[weakref.ReferenceType] = []
        self._cleanup_handlers: List[Callable] = []
    
    def get_memory_usage(self) -> tuple[float, float]:
        """Get current memory usage in MB and percentage."""
        process = psutil.Process()
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024), process.memory_percent()
    
    def log_memory_usage(self, prefix: str = "") -> float:
        """Log current memory usage with an optional prefix."""
        mb_used, percent = self.get_memory_usage()
        logger.info(f"{prefix}Memory usage: {mb_used:.2f}MB ({percent:.1f}%)")
        return mb_used
    
    def check_memory_usage(self) -> bool:
        """Check if memory usage is too high and perform cleanup if needed.
        
        Returns:
            bool: True if cleanup was performed, False otherwise
        """
        current_time = time.time()
        if current_time - self._last_check < self.check_interval:
            return False
            
        self._last_check = current_time
        
        mb_used, _ = self.get_memory_usage()
        if mb_used > self.max_memory_mb:
            logger.warning(f"Memory usage high: {mb_used:.2f}MB, performing cleanup...")
            self.cleanup()
            return True
            
        return False
    
    def register_resource(self, resource: Any) -> None:
        """Register a resource for cleanup tracking.
        
        Args:
            resource: The resource to track (will be stored as a weak reference)
        """
        if resource is not None:
            self._tracked_resources.append(weakref.ref(resource, self._on_resource_collected))
    
    def register_cleanup_handler(self, handler: Callable) -> None:
        """Register a cleanup handler function.
        
        Args:
            handler: Function to call during cleanup
        """
        if callable(handler) and handler not in self._cleanup_handlers:
            self._cleanup_handlers.append(handler)
    
    def _on_resource_collected(self, ref) -> None:
        """Called when a tracked resource is garbage collected."""
        try:
            if ref in self._tracked_resources:
                self._tracked_resources.remove(ref)
        except Exception as e:
            logger.error(f"Error in resource collection: {e}")
    
    def cleanup(self) -> None:
        """Perform memory cleanup."""
        logger.info("Performing memory cleanup...")
        
        # Run registered cleanup handlers
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error in cleanup handler {handler}: {e}")
        
        # Clear Python's garbage collector
        collected = gc.collect()
        logger.info(f"Garbage collector collected {collected} objects")
        
        # Clear function caches
        self._clear_caches()
        
        # Log memory usage after cleanup
        self.log_memory_usage("After cleanup: ")
    
    def _clear_caches(self) -> None:
        """Clear various caches to free memory."""
        # Clear Python's function caches
        for obj in gc.get_objects():
            if callable(obj) and hasattr(obj, '__code__'):
                if hasattr(obj, 'cache_clear'):  # For @lru_cache decorated functions
                    try:
                        obj.cache_clear()
                    except Exception:
                        pass
        
        # Clear other known caches
        try:
            import functools
            if hasattr(functools, '_lru_cache_wrapper'):
                functools._lru_cache_wrapper.cache_clear()
        except Exception:
            pass

def memory_aware(max_memory_mb: int = 200):
    """Decorator to make a function memory-aware.
    
    Args:
        max_memory_mb: Maximum memory in MB before cleanup is triggered
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check memory before execution
            manager = MemoryManager(max_memory_mb)
            manager.check_memory_usage()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Check memory after execution
                manager.check_memory_usage()
        return wrapper
    return decorator
