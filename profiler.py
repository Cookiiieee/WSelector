#!/usr/bin/env python3
"""Memory profiler for WSelector application."""
import os
import sys
import time
import gc
import psutil
import tracemalloc
from memory_profiler import profile
from wselector.app import WSelectorApp
from gi.repository import Gio, GLib

class MemoryMonitor:
    """Monitor memory usage of the application."""
    
    def __init__(self, interval=1.0):
        """Initialize memory monitor."""
        self.interval = interval
        self.process = psutil.Process()
        self.running = False
        self.peak_memory = 0
        
    def get_memory_mb(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def start(self):
        """Start monitoring memory usage."""
        self.running = True
        self.peak_memory = 0
        print("\n=== Memory Monitoring Started ===")
        print(f"PID: {self.process.pid}")
        print("Time (s) | Memory (MB) | Peak (MB)")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            while self.running:
                current_mem = self.get_memory_mb()
                self.peak_memory = max(self.peak_memory, current_mem)
                
                print(f"{time.time() - start_time:7.1f} | "
                      f"{current_mem:10.1f} | "
                      f"{self.peak_memory:9.1f}", 
                      flush=True)
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print("\n=== Memory Monitoring Stopped ===")
            print(f"Peak memory usage: {self.peak_memory:.1f} MB")
            self.stop()
    
    def stop(self):
        """Stop monitoring memory usage."""
        self.running = False

def run_app_with_profiling():
    """Run the application with memory profiling."""
    # Start memory monitoring in a separate thread
    monitor = MemoryMonitor(interval=1.0)
    import threading
    monitor_thread = threading.Thread(target=monitor.start)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try:
        # Run the application
        app = WSelectorApp("org.example.WSelector", Gio.ApplicationFlags.FLAGS_NONE)
        exit_status = app.run(None)
        return exit_status
    except Exception as e:
        print(f"Error running application: {e}", file=sys.stderr)
        return 1
    finally:
        # Stop monitoring
        monitor.stop()
        if monitor_thread.is_alive():
            monitor_thread.join(timeout=2.0)

if __name__ == "__main__":
    # Enable tracemalloc for tracking memory allocations
    tracemalloc.start()
    
    try:
        # Run the application with memory monitoring
        sys.exit(run_app_with_profiling())
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
        sys.exit(0)
