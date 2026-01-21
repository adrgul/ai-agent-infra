"""
Timing utilities for clean latency tracking.
"""
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Optional, Callable


@contextmanager
def timer(callback: Optional[Callable[[float], None]] = None):
    """
    Synchronous timing context manager.
    
    Usage:
        with timer(lambda t: print(f"Took {t}s")):
            # do work
            pass
    
    Args:
        callback: Optional callback receiving elapsed time in seconds
        
    Yields:
        Elapsed time (can be captured via 'as' clause)
    """
    start = time.time()
    elapsed_container = {"elapsed": 0.0}
    
    try:
        yield elapsed_container
    finally:
        elapsed = time.time() - start
        elapsed_container["elapsed"] = elapsed
        if callback:
            callback(elapsed)


@asynccontextmanager
async def async_timer(callback: Optional[Callable[[float], None]] = None):
    """
    Asynchronous timing context manager.
    
    Usage:
        async with async_timer(lambda t: print(f"Took {t}s")):
            # do async work
            await something()
    
    Args:
        callback: Optional callback receiving elapsed time in seconds
        
    Yields:
        Elapsed time container dict
    """
    start = time.time()
    elapsed_container = {"elapsed": 0.0}
    
    try:
        yield elapsed_container
    finally:
        elapsed = time.time() - start
        elapsed_container["elapsed"] = elapsed
        if callback:
            callback(elapsed)
