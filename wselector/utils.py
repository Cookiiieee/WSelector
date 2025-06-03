import os
import logging
import gc
import psutil
import time
import sys
import weakref
from urllib.parse import urlparse
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from functools import lru_cache
from wselector.models import WallpaperInfo

logger = logging.getLogger(__name__)

# Memory management configuration
MAX_CACHE_SIZE_MB = 800  # Start cleanup when reaching 800MB (80% of 1GB)
MEMORY_CHECK_INTERVAL = 30  # Check memory every 30 seconds
LAST_MEMORY_CHECK = 0
HIGH_MEMORY_USAGE = False
LAST_CLEANUP_TIME = 0
MIN_CLEANUP_INTERVAL = 10  # Minimum seconds between cleanups
MAX_MEMORY_USAGE_MB = 1000  # Hard cap at 1GB
FORCE_GC_THRESHOLD = 0.8  # Start cleanup at 80% of max (800MB)

# Track memory usage history for leak detection
MEMORY_HISTORY = []
MAX_HISTORY_LENGTH = 10

def get_memory_usage() -> Tuple[float, float]:
    """Get current memory usage in MB and percentage."""
    process = psutil.Process()
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024), process.memory_percent()

def log_memory_usage(prefix: str = ""):
    """Log current memory usage with an optional prefix."""
    mb_used, percent = get_memory_usage()
    logging.info(f"{prefix}Memory usage: {mb_used:.2f}MB ({percent:.1f}%)")
    return mb_used

def clear_function_caches():
    """Clear Python function caches."""
    # Clear lru_caches
    for obj in gc.get_objects():
        try:
            if callable(obj) and hasattr(obj, 'cache_info'):
                obj.cache_info()  # This will create the cache if it doesn't exist
                if hasattr(obj, 'cache_clear') and callable(getattr(obj, 'cache_clear', None)):
                    try:
                        obj.cache_clear()
                    except Exception as e:
                        logging.debug(f"Could not clear cache for {obj.__name__ if hasattr(obj, '__name__') else 'object'}: {e}")
        except Exception as e:
            logging.debug(f"Error clearing cache for object: {e}")

def clear_image_caches():
    """Clear all image-related caches."""
    try:
        from gi.repository import GdkPixbuf, Gio
        
        # Clear GdkPixbuf's internal cache
        if hasattr(GdkPixbuf.Pixbuf, 'clear_cache'):
            GdkPixbuf.Pixbuf.clear_cache()
            
        # Clear GIO's file info cache
        if hasattr(Gio, 'FileInfo'):
            Gio.FileInfo.clear_cache()
            
        # Clear any custom image caches
        for module in list(sys.modules.values()):
            if hasattr(module, '__file__') and 'PIL' in str(module.__file__):
                try:
                    if hasattr(module, 'Image'):
                        # Clear PIL image cache if it exists
                        if hasattr(module.Image, '_show'):
                            module.Image._show.cache_clear()
                except:
                    pass
    except Exception as e:
        logging.debug(f"Error clearing image caches: {e}")

def clear_gtk_caches():
    """Clear GTK's internal caches more aggressively."""
    try:
        # Clear style context cache
        if 'Gtk' in globals():
            style_context = Gtk.StyleContext()
            style_context.invalidate()
            
            # Clear style property cache
            Gtk.Widget.reset_style()
            
            # Clear icon theme cache
            icon_theme = Gtk.IconTheme.get_default()
            icon_theme.rescan_if_needed()
            
            # Clear Gdk caches
            if 'Gdk' in globals():
                display = Gdk.Display.get_default()
                if display:
                    display.sync()
                    display.flush()
                    
    except Exception as e:
        logger.warning(f"Error clearing GTK caches: {e}")

def clear_module_caches():
    """Clear module-level caches while preserving essential built-ins."""
    try:
        import sys
        import builtins
        
        # List of builtins we should never clear
        SAFE_BUILTINS = {
            'hasattr', 'getattr', 'setattr', 'delattr',
            'Exception', 'BaseException', 'TypeError', 'ValueError',
            'isinstance', 'issubclass', 'type', 'object',
            'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set',
            'len', 'next', 'iter', 'callable', 'property', 'staticmethod',
            'classmethod', 'super', 'enumerate', 'range', 'zip', 'map', 'filter',
            'any', 'all', 'sum', 'min', 'max', 'abs', 'round', 'divmod', 'pow',
            'sorted', 'reversed', 'slice', 'memoryview', 'bytearray', 'bytes',
            'chr', 'ord', 'bin', 'hex', 'oct', 'ascii', 'format', 'vars', 'dir',
            'globals', 'locals', 'hash', 'id', 'isinstance', 'issubclass',
            'issubclass', 'callable', 'classmethod', 'staticmethod', 'property',
            'object', 'type', 'super', 'int', 'float', 'bool', 'complex', 'str',
            'list', 'tuple', 'dict', 'set', 'frozenset', 'bytearray', 'bytes',
            'memoryview', 'slice', 'range', 'enumerate', 'zip', 'reversed',
            'sorted', 'filter', 'map', 'iter', 'next', 'callable', 'hash', 'id',
            'isinstance', 'issubclass', 'getattr', 'setattr', 'delattr',
            'hasattr', 'property', 'classmethod', 'staticmethod', 'super'
        }
        
        for module_name, module in list(sys.modules.items()):
            try:
                # Skip builtins and essential modules
                if module_name in ('builtins', 'sys', 'gc', 'logging'):
                    continue
                    
                if hasattr(module, '__dict__'):
                    for attr_name in dir(module):
                        try:
                            # Skip special attributes and safe builtins
                            if attr_name.startswith('__') and attr_name.endswith('__'):
                                continue
                                
                            if attr_name in SAFE_BUILTINS:
                                continue
                                
                            obj = getattr(module, attr_name, None)
                            if (hasattr(obj, 'cache_clear') and 
                                callable(obj.cache_clear) and 
                                not isinstance(obj, type)):  # Don't clear class methods
                                obj.cache_clear()
                        except Exception as e:
                            logging.debug(f"Error clearing {module_name}.{attr_name}: {e}")
            except Exception as e:
                logging.debug(f"Error processing module {module_name}: {e}")
    except Exception as e:
        logging.debug(f"Error in clear_module_caches: {e}")

def clear_network_caches():
    """Clear network-related caches."""
    try:
        import requests
        import http.client
        import urllib3
        
        # Clear requests session cache
        if hasattr(requests.Session, 'cache'):
            requests.Session.cache.clear()
            
        # Clear connection pools
        try:
            http.client.HTTPConnection._clear_cache()
        except:
            pass
            
        # Clear urllib3 connection pools
        try:
            urllib3.util.connection.HTTPConnection._clear_cache()
        except:
            pass
            
        # Clear DNS cache
        try:
            import socket
            socket.gethostbyname.cache_clear()
        except:
            pass
            
    except Exception as e:
        logging.debug(f"Error clearing network caches: {e}")

def clear_python_caches():
    """Clear Python's internal caches."""
    try:
        import sys
        import types
        
        # Clear function caches
        for module in list(sys.modules.values()):
            if not isinstance(module, types.ModuleType):
                continue
                
            for attr_name in dir(module):
                try:
                    attr = getattr(module, attr_name)
                    if hasattr(attr, 'cache_clear'):
                        attr.cache_clear()
                except:
                    pass
                    
        # Clear import caches
        sys.path_importer_cache.clear()
        if hasattr(sys, 'path_importer_cache'):
            sys.path_importer_cache.clear()
            
        # Clear type caches
        if hasattr(sys, '_clear_type_cache'):
            sys._clear_type_cache()
            
    except Exception as e:
        logging.debug(f"Error clearing Python caches: {e}")

def force_deep_gc():
    """Force deep garbage collection and clear cyclic references."""
    try:
        # Clear garbage collector's internal caches
        gc.set_debug(gc.DEBUG_SAVEALL)
        
        # Run multiple collection passes
        for gen in range(2, -1, -1):
            gc.collect(gen)
            time.sleep(0.1)
            
        # Clear any remaining garbage
        gc.collect()
        
        # Clear debug flags
        gc.set_debug(0)
        
    except Exception as e:
        logger.warning(f"Error in force_deep_gc: {e}")

def clear_all_caches():
    """Clear all possible caches."""
    clear_image_caches()
    clear_gtk_caches()
    clear_network_caches()
    clear_python_caches()
    
    # Force garbage collection
    import gc
    for gen in range(2, -1, -1):
        gc.collect(gen)

def clear_emergency():
    """Emergency memory cleanup - most aggressive measures."""
    try:
        logger.warning("Initiating emergency memory cleanup")
        
        # Clear all caches
        clear_image_caches()
        clear_gtk_caches()
        clear_network_caches()
        clear_module_caches()
        
        # Force deep garbage collection
        force_deep_gc()
        
        # Clear GTK caches more aggressively
        if 'Gdk' in globals():
            Gdk.ffi.gc()
            
        # Clear pixbuf loader caches
        if 'GdkPixbuf' in globals():
            GdkPixbuf.Pixbuf.get_formats()
            
        # Clear any remaining references
        import sys
        modules_to_clear = [
            'PIL', 'PIL.Image', 'PIL.ImageFile', 
            'urllib3', 'requests', 'http', 'urllib', 'urllib.parse',
            'gi.overrides', 'gi.repository', 'gi._gi', 'gi._error',
            'gi.module', 'gi.types', 'gi._constants', 'gi._gi_cairo',
            'gi._option', 'gi._propertyhelper', 'gi._signalhelper',
            'gi._gtktemplate', 'gi.docstring', 'gi.importer', 'gi.types'
        ]
        
        for mod in modules_to_clear:
            if mod in sys.modules:
                try:
                    del sys.modules[mod]
                except Exception as e:
                    logger.debug(f"Could not clear module {mod}: {e}")
        
        # Force another GC
        gc.collect()
        
        # Get final memory usage
        process = psutil.Process()
        mem_info = process.memory_info()
        mb_used = mem_info.rss / (1024 * 1024)
        logger.warning(f"After emergency cleanup: {mb_used:.2f}MB")
        
        return mb_used
        
    except Exception as e:
        logger.error(f"Error during emergency cleanup: {e}")
        return -1

def manual_cleanup():
    """
    Perform a thorough memory cleanup that can be triggered manually.
    More aggressive than regular cleanup but safer than emergency cleanup.
    """
    try:
        logger.info("Initiating manual memory cleanup...")
        
        # First, clear all caches
        clear_image_caches()
        clear_gtk_caches()
        clear_network_caches()
        clear_module_caches()
        
        # Force garbage collection multiple times to collect cyclic references
        for _ in range(3):
            gc.collect()
            time.sleep(0.1)  # Give GC time to work
            
        # Clear any remaining caches
        if 'gc' in globals():
            gc.collect()
            
        # Clear any remaining GTK caches
        if 'Gdk' in globals():
            Gdk.ffi.gc()
            
        # Clear pixbuf caches
        if 'GdkPixbuf' in globals():
            GdkPixbuf.Pixbuf.get_formats()  # This can help clear pixbuf cache
            
        # Clear any remaining references
        import sys
        if 'sys' in globals():
            # Clear modules that might be holding references
            modules_to_clear = ['PIL', 'PIL.Image', 'PIL.ImageFile', 'urllib3', 'requests']
            for mod in modules_to_clear:
                if mod in sys.modules:
                    try:
                        del sys.modules[mod]
                    except Exception as e:
                        logger.debug(f"Could not clear module {mod}: {e}")
        
        # Get final memory usage
        process = psutil.Process()
        mem_info = process.memory_info()
        mb_used = mem_info.rss / (1024 * 1024)
        logger.info(f"After manual cleanup: Memory usage: {mb_used:.2f}MB")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        return False

def get_cached_thumbnail_path(url: str, cache_dir: str) -> Optional[str]:
    """Get or download a thumbnail with caching."""
    try:
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Get filename from URL
        filename = os.path.basename(urlparse(url).path)
        if not filename:
            filename = f"thumbnail_{hash(url)}.jpg"
            
        cache_path = os.path.join(cache_dir, filename)
        if os.path.exists(cache_path):
            return cache_path
            
        # Download the image with timeout
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Save the image in chunks
        with open(cache_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:  # Filter out keep-alive chunks
                    continue
                f.write(chunk)
        
        # Check cache size and clean up if needed
        cleanup_cache(cache_dir, max_size_mb=MAX_CACHE_SIZE_MB)
        
        return cache_path
        
    except Exception as e:
        logging.error(f"Failed to download thumbnail {url}: {e}")
        return None

def cleanup_cache(cache_dir: str, max_size_mb: int):
    """Clean up cache directory if it exceeds max_size_mb."""
    try:
        if not os.path.exists(cache_dir):
            return
            
        # Get all files with their access times and sizes
        files = []
        total_size = 0
        
        for root, _, filenames in os.walk(cache_dir):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                try:
                    stat = os.stat(filepath)
                    files.append((filepath, stat.st_atime, stat.st_size))
                    total_size += stat.st_size
                except OSError:
                    continue
        
        # Convert to MB
        total_size_mb = total_size / (1024 * 1024)
        
        # If under limit, do nothing
        if total_size_mb <= max_size_mb:
            return
            
        # Sort files by access time (oldest first)
        files.sort(key=lambda x: x[1])
        
        # Remove oldest files until under limit
        for filepath, _, size in files:
            if total_size_mb <= max_size_mb * 0.9:  # Stop at 90% of max size
                break
                
            try:
                os.remove(filepath)
                total_size_mb -= size / (1024 * 1024)
            except OSError:
                continue
                
    except Exception as e:
        logging.error(f"Error cleaning up cache: {e}")

def download_thumbnail(wp: WallpaperInfo) -> str:
    """
    Download and cache a wallpaper thumbnail.
    
    Args:
        wp: WallpaperInfo object containing thumbnail URL and ID
        
    Returns:
        str: Path to the downloaded thumbnail file
    """
    try:
        check_memory_usage()
        cache_dir = os.path.dirname(wp.get_cached_path())
        return get_cached_thumbnail_path(wp.thumbnail_url, cache_dir)
        
    except Exception as e:
        logger.error(f"Failed to download thumbnail for {wp.id}: {e}")
        raise

def track_memory_usage():
    """Track memory usage history and detect potential leaks."""
    global MEMORY_HISTORY, LAST_MEMORY_CHECK, LAST_CLEANUP_TIME
    
    try:
        import time
        import psutil
        
        current_time = time.time()
        if current_time - LAST_MEMORY_CHECK < MEMORY_CHECK_INTERVAL:
            return
            
        # Get current memory usage
        process = psutil.Process()
        mem_info = process.memory_info()
        mb_used = mem_info.rss / (1024 * 1024)
        
        # Add to history
        MEMORY_HISTORY.append((current_time, mb_used))
        
        # Keep only the last MAX_HISTORY_LENGTH entries
        if len(MEMORY_HISTORY) > MAX_HISTORY_LENGTH:
            MEMORY_HISTORY = MEMORY_HISTORY[-MAX_HISTORY_LENGTH:]
            
        # Check for memory leaks (significant growth over time)
        if len(MEMORY_HISTORY) >= 10:  # Need at least 10 data points
            oldest = MEMORY_HISTORY[0][1]
            newest = MEMORY_HISTORY[-1][1]
            growth = newest - oldest
            
            if growth > 100:  # More than 100MB growth
                logging.warning(f"Possible memory leak detected: {growth:.2f}MB growth in last {len(MEMORY_HISTORY)} checks")
                
        # Update last check time
        LAST_MEMORY_CHECK = current_time
        
    except Exception as e:
        logging.debug(f"Error tracking memory usage: {e}")
    
    # Update last cleanup time if needed
    try:
        LAST_CLEANUP_TIME = current_time
    except NameError:
        pass  # current_time might not be defined if an error occurred earlier

def check_memory_usage():
    """Check if memory usage is too high and perform cleanup if needed."""
    global LAST_MEMORY_CHECK, HIGH_MEMORY_USAGE, LAST_CLEANUP_TIME
    
    try:
        current_time = time.time()
        if current_time - LAST_MEMORY_CHECK < MEMORY_CHECK_INTERVAL:
            return
            
        process = psutil.Process()
        mem_info = process.memory_info()
        mb_used = mem_info.rss / (1024 * 1024)
        
        # Update last check time
        LAST_MEMORY_CHECK = current_time
        
        if HIGH_MEMORY_USAGE or mb_used > MAX_CACHE_SIZE_MB:
            if current_time - LAST_CLEANUP_TIME < MIN_CLEANUP_INTERVAL:
                return
                
            if not HIGH_MEMORY_USAGE:
                try:
                    logging.warning(f"Memory usage high: {mb_used:.2f}MB, performing cleanup...")
                except:
                    pass
                HIGH_MEMORY_USAGE = True
            
            # Perform cleanup with error handling
            try:
                force_deep_gc()
                clear_image_caches()
                clear_gtk_caches()
                clear_module_caches()
                clear_network_caches()
            except Exception as e:
                try:
                    logging.debug(f"Error during cleanup: {e}")
                except:
                    pass
            
            # Get new memory usage
            new_mb = mb_used  # Default to old value if we can't get new one
            try:
                new_mb = process.memory_info().rss / (1024 * 1024)
                try:
                    logging.info(f"After cleanup: Memory usage: {new_mb:.2f}MB")
                except:
                    pass
                    
                # Emergency measures if still too high
                if new_mb > MAX_MEMORY_USAGE_MB:
                    try:
                        logging.warning("Memory critically high, performing emergency cleanup...")
                        clear_emergency()
                        new_mb = process.memory_info().rss / (1024 * 1024)
                        try:
                            logging.warning(f"After emergency cleanup: {new_mb:.2f}MB")
                        except:
                            pass
                    except Exception as e:
                        try:
                            logging.debug(f"Error during emergency cleanup: {e}")
                        except:
                            pass
            except Exception as e:
                try:
                    logging.debug(f"Error checking memory after cleanup: {e}")
                except:
                    pass
            
            # Update state
            try:
                HIGH_MEMORY_USAGE = new_mb > MAX_CACHE_SIZE_MB * 0.8
                if not HIGH_MEMORY_USAGE:
                    try:
                        logging.info("Memory usage normalized")
                    except:
                        pass
                elif new_mb > MAX_MEMORY_USAGE_MB * 1.1:  # 10% over absolute max
                    try:
                        logging.error("Memory critically high, consider restarting the application")
                    except:
                        pass
            except Exception as e:
                try:
                    logging.debug(f"Error updating memory state: {e}")
                except:
                    pass
            
            # Update last cleanup time
            LAST_CLEANUP_TIME = current_time
            
    except Exception as e:
        try:
            logging.debug(f"Error in check_memory_usage: {e}")
        except:
            pass