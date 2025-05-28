"""Memory management for WSelector application."""
import gc
import weakref
import psutil
import logging
import time
import os
import threading
from typing import List, Dict, Set, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

class ResourceTracker:
    """Track and manage application resources."""
    
    def __init__(self, max_memory_mb: int = 200):
        """Initialize the resource tracker.
        
        Args:
            max_memory_mb: Maximum allowed memory usage in MB
        """
        self.max_memory_mb = max_memory_mb
        self._tracked_resources: List[weakref.ReferenceType] = []
        self._cleanup_handlers: List[Callable] = []
        self._last_cleanup = 0
        self._cleanup_interval = 30  # seconds
        
    def track(self, obj: Any) -> None:
        """Track an object for cleanup.
        
        Args:
            obj: Object to track
        """
        if obj is not None:
            self._tracked_resources.append(weakref.ref(obj, self._on_resource_collected))
    
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
            logger.debug(f"Error in resource collection: {e}")
    
    def get_memory_usage(self) -> tuple[float, float]:
        """Get current memory usage in MB and percentage.
        
        Returns:
            tuple: (memory_used_mb, memory_percent)
        """
        process = psutil.Process()
        mem_info = process.memory_info()
        return mem_info.rss / (1024 * 1024), process.memory_percent()
    
    def log_memory_usage(self, prefix: str = "") -> float:
        """Log current memory usage.
        
        Args:
            prefix: Optional prefix for the log message
            
        Returns:
            float: Memory usage in MB
        """
        mb_used, percent = self.get_memory_usage()
        logger.info(f"{prefix}Memory usage: {mb_used:.2f}MB ({percent:.1f}%)")
        return mb_used
    
    def should_cleanup(self) -> bool:
        """Check if cleanup is needed based on memory usage and time.
        
        Returns:
            bool: True if cleanup should be performed
        """
        current_time = time.time()
        
        # Check if cleanup interval has passed
        if current_time - self._last_cleanup < self._cleanup_interval:
            return False
            
        # Check memory usage
        mb_used, _ = self.get_memory_usage()
        return mb_used > self.max_memory_mb
    
    def cleanup(self) -> bool:
        """Perform memory cleanup if needed.
        
        Returns:
            bool: True if cleanup was performed, False otherwise
        """
        if not self.should_cleanup():
            return False
            
        self._last_cleanup = time.time()
        logger.info("Performing memory cleanup...")
        
        # Run registered cleanup handlers
        for handler in self._cleanup_handlers:
            try:
                handler()
            except Exception as e:
                logger.error(f"Error in cleanup handler {handler}: {e}")
        
        # Force garbage collection
        collected = gc.collect()
        logger.debug(f"Garbage collector collected {collected} objects")
        
        # Log memory usage after cleanup
        self.log_memory_usage("After cleanup: ")
        return True

def memory_aware(max_memory_mb: int = 200):
    """Decorator to make a function memory-aware.
    
    Args:
        max_memory_mb: Maximum memory in MB before cleanup is triggered
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a tracker for this function call
            tracker = ResourceTracker(max_memory_mb)
            
            try:
                # Check memory before execution
                tracker.log_memory_usage("Before calling function: ")
                
                # Call the function
                result = func(*args, **kwargs)
                
                # Check memory after execution
                tracker.log_memory_usage("After function execution: ")
                
                return result
            finally:
                # Always clean up
                tracker.cleanup()
        return wrapper
    return decorator

class MemoryMonitor:
    """Monitor memory usage of the application."""
    
    def __init__(self, interval: float = 1.0, log_file: Optional[str] = None):
        """Initialize memory monitor.
        
        Args:
            interval: Time between memory checks in seconds
            log_file: Optional file to log memory usage to
        """
        self.interval = interval
        self.process = psutil.Process()
        self.running = False
        self.peak_memory = 0
        self.log_file = log_file
        self.start_time = time.time()
        
        # Ensure log directory exists
        if self.log_file:
            os.makedirs(os.path.dirname(os.path.abspath(self.log_file)), exist_ok=True)
    
    def get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def log_memory_usage(self) -> None:
        """Log current memory usage to the info log."""
        current_time = time.time() - self.start_time
        current_mem = self.get_memory_mb()
        self.peak_memory = max(self.peak_memory, current_mem)
        
        logger.info(f"Memory usage: {current_time:.1f}s | {current_mem:.1f}MB | Peak: {self.peak_memory:.1f}MB")
        
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(f"{time.time()},{current_mem},{self.peak_memory}\n")
    
    def _monitor_loop(self) -> None:
        """The monitoring loop that runs in a separate thread."""
        while self.running:
            self.log_memory_usage()
            time.sleep(self.interval)

    def start(self) -> None:
        """Start monitoring memory usage in a separate daemon thread."""
        if hasattr(self, '_monitor_thread') and self._monitor_thread.is_alive():
            logger.warning("Memory monitor is already running")
            return
            
        self.running = True
        self.peak_memory = 0
        self.start_time = time.time()
        
        # Start the monitor in a daemon thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True  # Daemon threads are stopped when the main program exits
        )
        self._monitor_thread.start()
        
        logger.info(f"Memory monitoring started in background (PID: {self.process.pid})")
    
    def stop(self) -> None:
        """Stop monitoring memory usage and clean up the thread."""
        if not hasattr(self, '_monitor_thread') or not self._monitor_thread.is_alive():
            return
            
        self.running = False
        
        # Wait for the thread to finish (with a timeout to prevent hanging)
        if hasattr(self, '_monitor_thread') and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
            if self._monitor_thread.is_alive():
                logger.warning("Memory monitor thread did not stop gracefully")
        
        logger.info(f"Memory monitoring stopped. Peak memory usage: {self.peak_memory:.1f} MB")
