#!/usr/bin/env python3

import sys
import logging
import json
import threading
import time
import gc
import weakref
from datetime import datetime
from typing import Optional, List, Dict, Set, Any, Callable

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Pango', '1.0')
from gi.repository import GLib, Gtk, Gio, Adw, Gdk, GdkPixbuf, Pango

from wselector.models import WallpaperInfo, WallpaperGObject
from wselector.api import WSelectorScraper
from wselector.memory_manager import ResourceTracker, MemoryMonitor, memory_aware

# Setup logging
def setup_logging():
    """Configure logging with both file and console handlers"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(GLib.get_user_cache_dir(), "wselector", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Create handlers
    log_file = os.path.join(log_dir, "wselector.log")
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatters and add it to handlers
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logging
logger = setup_logging()

# Configuration paths
CONFIG_PATH = os.path.join(GLib.get_user_config_dir(), "wselector", "config.json")
CACHE_DIR = os.path.join(GLib.get_user_cache_dir(), "wselector")
CACHE_INDEX = os.path.join(CACHE_DIR, "cache_index.json")

# Default configuration
DEFAULT_CONFIG = {
    "categories": "111",
    "purity": "100",
    "selected_categories": ["General"],
    "selected_purity": ["SFW"],
    "sort_mode": "latest"
}

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

class WSelectorApp(Adw.Application):
    """Main application class with memory management."""
    
    def __init__(self, application_id, flags):
        """Initialize the application."""
        super().__init__(application_id=application_id, flags=flags)
        GLib.set_application_name("WSelector")
        GLib.set_prgname(application_id)

        # Initialize configuration
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()  # This will update self.config with saved values
        
        # Initialize memory management
        self.memory_tracker = ResourceTracker(max_memory_mb=200)
        self.memory_tracker.register_cleanup_handler(self.cleanup_resources)
        
        # Initialize instance variables
        self.current_page = 1
        self.loading = False
        self.current_query: Optional[str] = None
        self.min_column_width = 200
        self.column_spacing = 10
        self.row_spacing = 10
        self.margin = 10
        self.scroll_position = 0.0
        self.is_dark_theme = self.config.get("theme", "light") == "dark"
        
        # Track active operations
        self._active_threads: Set[threading.Thread] = set()
        self._active_requests: Set[Any] = set()
        self._wallpaper_widgets: List[Gtk.Widget] = []
        
        # Initialize UI components
        self._init_ui()
        
        # Setup memory monitoring
        self._setup_memory_monitoring()
    
    def _init_ui(self):
        """Initialize UI components."""
        # Create main window
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_default_size(1200, 800)
        self.window.set_title("WSelector")
        
        # Create main box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.window.set_child(self.main_box)
        
        # Create header bar
        self.header = Gtk.HeaderBar()
        self.window.set_titlebar(self.header)
        
        # Add search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search wallpapers...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.header.set_title_widget(self.search_entry)
        
        # Create scrolled window for wallpapers
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)
        self.main_box.append(self.scrolled_window)
        
        # Create flow box for wallpapers
        self.flow_box = Gtk.FlowBox()
        self.flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow_box.set_homogeneous(False)
        self.flow_box.set_min_children_per_line(1)
        self.flow_box.set_max_children_per_line(10)
        self.flow_box.set_column_spacing(self.column_spacing)
        self.flow_box.set_row_spacing(self.row_spacing)
        self.flow_box.set_margin_top(self.margin)
        self.flow_box.set_margin_bottom(self.margin)
        self.flow_box.set_margin_start(self.margin)
        self.flow_box.set_margin_end(self.margin)
        
        self.scrolled_window.set_child(self.flow_box)
        
        # Add scroll event controller
        self.scroll_controller = Gtk.EventControllerScroll.new(
            Gtk.EventControllerScrollFlags.VERTICAL
        )
        self.scroll_controller.connect("scroll", self.on_scroll)
        self.scrolled_window.add_controller(self.scroll_controller)
        
        # Add loading spinner
        self.spinner = Gtk.Spinner()
        self.spinner.hide()
        self.header.pack_start(self.spinner)
    
    def _setup_memory_monitoring(self) -> None:
        """Setup memory monitoring and cleanup handlers."""
        # Register periodic memory checks
        GLib.timeout_add_seconds(
            30,  # Check every 30 seconds
            self._check_memory_usage
        )
        
        # Register cleanup on low memory warning
        self.window.connect("notify::allocated-size", self._on_memory_warning)
    
    def _check_memory_usage(self) -> bool:
        """Check memory usage and perform cleanup if needed."""
        try:
            # Log memory usage
            self.memory_tracker.log_memory_usage("Memory check: ")
            
            # Perform cleanup if needed
            if self.memory_tracker.should_cleanup():
                self.cleanup_resources()
            
            return GLib.SOURCE_CONTINUE
        except Exception as e:
            logger.error(f"Error in memory check: {e}")
            return GLib.SOURCE_CONTINUE
    
    def _on_memory_warning(self, *args) -> None:
        """Handle low memory warning from GTK."""
        logger.warning("Low memory warning received, performing cleanup...")
        self.cleanup_resources()
    
    def cleanup_resources(self) -> None:
        """Clean up resources to free memory."""
        logger.info("Performing resource cleanup...")
        
        # Clean up completed threads
        self._cleanup_threads()
        
        # Clean up completed requests
        self._cleanup_requests()
        
        # Clean up old wallpaper widgets
        self._cleanup_wallpaper_widgets()
        
        # Force garbage collection
        gc.collect()
        
        # Log memory usage after cleanup
        self.memory_tracker.log_memory_usage("After cleanup: ")
    
    def _cleanup_threads(self) -> None:
        """Clean up completed threads."""
        remaining_threads = set()
        for thread in self._active_threads:
            if thread.is_alive():
                remaining_threads.add(thread)
            else:
                try:
                    thread.join(timeout=0.1)
                except Exception as e:
                    logger.debug(f"Error joining thread: {e}")
        self._active_threads = remaining_threads
    
    def _cleanup_requests(self) -> None:
        """Clean up completed requests."""
        remaining_requests = set()
        for future in self._active_requests:
            if hasattr(future, 'done') and not future.done():
                remaining_requests.add(future)
            else:
                try:
                    # Check for exceptions to prevent unhandled exceptions in futures
                    if hasattr(future, 'exception'):
                        future.exception()
                except Exception as e:
                    logger.debug(f"Future exception: {e}")
        self._active_requests = remaining_requests
    
    def _cleanup_wallpaper_widgets(self) -> None:
        """Clean up wallpaper widgets that are no longer visible."""
        if not hasattr(self, 'flow_box') or not self.flow_box:
            return
            
        try:
            # Get the visible area
            vadj = self.scrolled_window.get_vadjustment()
            visible_top = vadj.get_value()
            visible_bottom = visible_top + vadj.get_page_size()
            
            # Keep track of widgets to remove
            to_remove = []
            
            for widget in self._wallpaper_widgets:
                if not widget.get_parent():
                    # Widget is no longer in the container
                    to_remove.append(widget)
                    continue
                    
                # Check if widget is outside visible area
                _, y = widget.translate_coordinates(self.scrolled_window, 0, 0) or (0, 0)
                widget_height = widget.get_allocated_height()
                
                if y + widget_height < visible_top or y > visible_bottom:
                    # Widget is outside visible area, remove it
                    widget.get_parent().remove(widget)
                    to_remove.append(widget)
            
            # Remove collected widgets from tracking
            for widget in to_remove:
                if widget in self._wallpaper_widgets:
                    self._wallpaper_widgets.remove(widget)
            
            # Log cleanup
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} wallpaper widgets")
                
        except Exception as e:
            logger.error(f"Error cleaning up wallpaper widgets: {e}", exc_info=True)
    
    def clear_wallpapers(self) -> None:
        """Clear all wallpapers from the grid with proper cleanup."""
        if not hasattr(self, 'flow_box') or not self.flow_box:
            return
            
        # Remove all children from the grid
        while (child := self.flow_box.get_first_child()) is not None:
            # Disconnect any signals first
            if hasattr(child, 'disconnect_signals'):
                child.disconnect_signals()
            # Remove from grid
            self.flow_box.remove(child)
            # Schedule widget for destruction
            GLib.idle_add(child.destroy)
        
        # Clear the wallpaper list and widgets
        self.wallpapers = []
        self._wallpaper_widgets = []
        self.current_page = 1
        
        # Force garbage collection
        gc.collect()
    
    def load_wallpapers(self, query: Optional[str] = None, page: int = 1, 
                       sort_mode: Optional[str] = None, refresh: bool = False) -> None:
        """Load wallpapers from the API with memory management.
        
        Args:
            query: Search query string
            page: Page number to load
            sort_mode: Sorting mode ('latest', 'popular', 'random', 'views', 'favorites')
            refresh: Whether this is a refresh operation
        """
        if self.loading:
            return
            
        self.loading = True
        self.current_query = query or self.current_query
        
        # Clean up old resources before starting new load
        self.cleanup_resources()
        
        # Update sort mode if provided
        if sort_mode:
            self.config["sort_mode"] = sort_mode
            self.save_config()
        else:
            sort_mode = self.config.get("sort_mode", "latest")
        
        # Show loading spinner
        self.spinner.start()
        self.spinner.show()
        
        # Save scroll position before refresh
        if refresh and hasattr(self, 'scrolled_window'):
            self.scroll_position = self.scrolled_window.get_vadjustment().get_value()
        
        # Clear existing wallpapers if it's a new search or refresh
        if page == 1 or refresh:
            self.clear_wallpapers()
        
        # Get categories and purity from config
        categories = self.config.get("categories", "111")
        purity = self.config.get("purity", "100")
        
        # Start loading in a separate thread
        thread = threading.Thread(
            target=self._load_wallpapers_thread,
            args=(self.current_query, page, sort_mode, categories, purity, refresh),
            daemon=True
        )
        
        self._active_threads.add(thread)
        thread.start()
    
    def _load_wallpapers_thread(self, query: str, page: int, sort_mode: str, 
                              categories: str, purity: str, refresh: bool = False) -> None:
        """Thread function to load wallpapers with memory management."""
        # Register this thread for cleanup
        current_thread = threading.current_thread()
        
        try:
            # Log memory usage at start
            self.memory_tracker.log_memory_usage("Before loading wallpapers: ")
            
            # Create a new scraper instance for this thread
            scraper = WSelectorScraper()
            
            # Track this request
            future = object()  # Placeholder for request tracking
            self._active_requests.add(future)
            
            try:
                # Get wallpapers from the API with timeout
                wallpapers = scraper.search_wallpapers(
                    query=query,
                    categories=categories,
                    purity=purity,
                    page=page,
                    sort=sort_mode
                )
                
                # Update UI in the main thread
                GLib.idle_add(self._on_wallpapers_loaded, wallpapers, refresh)
                
            except Exception as e:
                logger.error(f"Error in wallpaper search: {e}", exc_info=True)
                GLib.idle_add(self._on_load_error, str(e))
                
        except Exception as e:
            logger.error(f"Error setting up wallpaper load: {e}", exc_info=True)
            GLib.idle_add(self._on_load_error, str(e))
            
        finally:
            # Clean up in the main thread
            def cleanup():
                try:
                    self.loading = False
                    if hasattr(self, 'spinner'):
                        self.spinner.stop()
                        self.spinner.hide()
                    
                    # Remove this thread from active threads
                    if current_thread in self._active_threads:
                        self._active_threads.remove(current_thread)
                    
                    # Remove this request
                    if future in self._active_requests:
                        self._active_requests.remove(future)
                    
                    # Schedule memory cleanup
                    self.memory_tracker.cleanup()
                    
                except Exception as e:
                    logger.error(f"Error in cleanup: {e}", exc_info=True)
            
            # Run cleanup in the main thread
            GLib.idle_add(cleanup)
    
    def _on_wallpapers_loaded(self, wallpapers: List[WallpaperInfo], refresh: bool) -> None:
        """Handle loaded wallpapers in the main thread."""
        try:
            # Add wallpapers to the grid
            for wallpaper in wallpapers:
                self._add_wallpaper_widget(wallpaper)
            
            # Restore scroll position if refreshing
            if refresh and hasattr(self, 'scrolled_window'):
                vadj = self.scrolled_window.get_vadjustment()
                vadj.set_value(self.scroll_position)
            
            # Track memory usage after loading
            self.memory_tracker.log_memory_usage("After loading wallpapers: ")
            
        except Exception as e:
            logger.error(f"Error in _on_wallpapers_loaded: {e}", exc_info=True)
    
    def _add_wallpaper_widget(self, wallpaper: WallpaperInfo) -> None:
        """Add a wallpaper widget to the grid."""
        try:
            # Create wallpaper widget (simplified for example)
            image = Gtk.Picture()
            image.set_size_request(200, 150)
            
            # Create a container for the wallpaper
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.append(image)
            
            # Add to flow box
            self.flow_box.append(box)
            
            # Track the widget for cleanup
            self._wallpaper_widgets.append(box)
            
            # Load thumbnail in a background thread
            self._load_thumbnail(wallpaper, image)
            
        except Exception as e:
            logger.error(f"Error adding wallpaper widget: {e}", exc_info=True)
    
    def _load_thumbnail(self, wallpaper: WallpaperInfo, image_widget: Gtk.Picture) -> None:
        """Load thumbnail in a background thread."""
        def load():
            try:
                # This would be replaced with actual thumbnail loading logic
                # For now, we'll just use a placeholder
                GLib.idle_add(
                    lambda: self._set_thumbnail(image_widget, None)
                )
            except Exception as e:
                logger.error(f"Error loading thumbnail: {e}", exc_info=True)
        
        # Start loading in a separate thread
        thread = threading.Thread(target=load, daemon=True)
        self._active_threads.add(thread)
        thread.start()
    
    def _set_thumbnail(self, image_widget: Gtk.Picture, pixbuf: Optional[GdkPixbuf.Pixbuf]) -> None:
        """Set thumbnail on the image widget in the main thread."""
        try:
            if pixbuf:
                image_widget.set_pixbuf(pixbuf)
            else:
                # Set a placeholder if no pixbuf is provided
                image_widget.set_from_icon_name("image-missing")
        except Exception as e:
            logger.error(f"Error setting thumbnail: {e}", exc_info=True)
    
    def _on_load_error(self, error: str) -> None:
        """Handle load errors."""
        logger.error(f"Load error: {error}")
        # Show error to user (simplified for example)
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error loading wallpapers",
            secondary_text=str(error)
        )
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.show()
    
    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        """Handle search entry changes."""
        query = entry.get_text().strip()
        if query != self.current_query:
            self.load_wallpapers(query=query, page=1)
    
    def on_scroll(self, controller, dx, dy) -> bool:
        """Handle scroll events for infinite scrolling."""
        if not self.loading and dy < 0:  # Only on scroll down
            adj = self.scrolled_window.get_vadjustment()
            if adj.get_upper() - (adj.get_value() + adj.get_page_size()) < adj.get_page_size() / 2:
                # Near the bottom, load more
                self.load_wallpapers(page=self.current_page + 1)
        return False
    
    def load_config(self) -> None:
        """Load application configuration."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r') as f:
                    self.config.update(json.load(f))
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def save_config(self) -> None:
        """Save application configuration."""
        try:
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def do_activate(self) -> None:
        """Handle application activation."""
        try:
            # Show the main window
            self.window.present()
            
            # Load initial wallpapers
            self.load_wallpapers()
            
        except Exception as e:
            logger.error(f"Error activating application: {e}", exc_info=True)
            self.quit()
    
    def do_shutdown(self) -> None:
        """Handle application shutdown with cleanup."""
        try:
            # Perform final cleanup
            logger.info("Shutting down application...")
            
            # Clear all wallpapers
            self.clear_wallpapers()
            
            # Clean up any remaining threads and requests
            self.cleanup_resources()
            
            # Save configuration
            self.save_config()
            
            # Log final memory usage
            self.memory_tracker.log_memory_usage("Final memory usage: ")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
        finally:
            # Call parent's shutdown
            super().do_shutdown()

def main():
    """Main entry point for the application."""
    # Create and run the application
    app = WSelectorApp("org.example.WSelector", Gio.ApplicationFlags.FLAGS_NONE)
    return app.run(None)

if __name__ == "__main__":
    sys.exit(main())
