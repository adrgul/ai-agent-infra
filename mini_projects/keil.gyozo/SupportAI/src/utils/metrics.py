"""Metrics collection for monitoring."""

import logging
import time
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Simple in-memory metrics collector.

    In production, this should be replaced with Prometheus metrics.
    """

    def __init__(self) -> None:
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, list[float]] = defaultdict(list)
        self.gauges: Dict[str, float] = {}

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self.counters[name] += value
        logger.debug(f"Counter '{name}' incremented to {self.counters[name]}")

    def record_time(self, name: str, duration: float) -> None:
        """Record a timing metric in seconds."""
        self.timers[name].append(duration)
        logger.debug(f"Timer '{name}' recorded: {duration:.3f}s")

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric."""
        self.gauges[name] = value
        logger.debug(f"Gauge '{name}' set to {value}")

    def get_stats(self) -> dict:
        """Get current metrics statistics."""
        stats = {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "timers": {}
        }

        # Calculate timer statistics
        for name, times in self.timers.items():
            if times:
                stats["timers"][name] = {
                    "count": len(times),
                    "avg": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "total": sum(times)
                }

        return stats

    def reset(self) -> None:
        """Reset all metrics."""
        self.counters.clear()
        self.timers.clear()
        self.gauges.clear()
        logger.info("Metrics reset")


# Global metrics instance
metrics = MetricsCollector()


class Timer:
    """Context manager for timing operations."""

    def __init__(self, name: str, metrics_collector: Optional[MetricsCollector] = None):
        self.name = name
        self.metrics = metrics_collector or metrics
        self.start_time: Optional[float] = None
        self.duration: Optional[float] = None

    def __enter__(self) -> "Timer":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.start_time:
            self.duration = time.time() - self.start_time
            self.metrics.record_time(self.name, self.duration)
