"""Per-user token bucket rate limiter."""

import time


class TokenBucket:
    """
    Per-key token bucket rate limiter.

    Each key (user) gets a bucket with `capacity` tokens that refills
    at `capacity / window` tokens per second. Calling `consume()` attempts
    to take one token; returns True if allowed, False if denied.
    """

    def __init__(self, capacity: int, window: float):
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if window <= 0:
            raise ValueError("window must be positive")

        self.capacity = capacity
        self.window = window
        self.refill_rate = capacity / window

        # {key: (tokens_remaining, last_refill_time)}
        self._buckets: dict[str, tuple[float, float]] = {}
        self._last_cleanup: float = 0.0

    def consume(self, key: str) -> bool:
        """Try to consume one token for the given key."""
        now = time.monotonic()

        if now - self._last_cleanup > 60.0:
            self.cleanup()
            self._last_cleanup = now

        if key in self._buckets:
            tokens, last_time = self._buckets[key]
            elapsed = now - last_time
            tokens = min(self.capacity, tokens + elapsed * self.refill_rate)
        else:
            tokens = float(self.capacity)

        if tokens >= 1.0:
            self._buckets[key] = (tokens - 1.0, now)
            return True

        self._buckets[key] = (tokens, now)
        return False

    def cleanup(self, max_age: float | None = None) -> int:
        """Remove stale entries older than max_age seconds."""
        if max_age is None:
            max_age = self.window * 2

        now = time.monotonic()
        stale_keys = [
            key
            for key, (_, last_time) in self._buckets.items()
            if now - last_time > max_age
        ]
        for key in stale_keys:
            del self._buckets[key]
        return len(stale_keys)
