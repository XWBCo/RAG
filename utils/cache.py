"""TTL-based response caching for RAG queries.

Caches common queries to reduce latency from ~5s to <500ms.
Skips caching when app_context is provided (dynamic results).
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cached response entry with TTL."""

    response: dict
    created_at: float
    ttl_seconds: int
    query_hash: str

    def is_expired(self) -> bool:
        """Check if entry has exceeded its TTL."""
        return time.time() - self.created_at > self.ttl_seconds

    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at


class ResponseCache:
    """
    TTL-based cache for RAG query responses.

    Cache key: hash of (query, domain, prompt_name)
    Does not cache when app_context is provided (dynamic results).

    Thread-safety: This implementation uses a simple dict and is suitable
    for single-process deployments. For multi-process, use Redis instead.
    """

    def __init__(self, default_ttl: int = 3600, max_size: int = 1000):
        """
        Initialize response cache.

        Args:
            default_ttl: Default time-to-live in seconds (1 hour)
            max_size: Maximum cache entries before eviction
        """
        self._cache: dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _make_key(
        self, query: str, domain: str, prompt_name: Optional[str] = None
    ) -> str:
        """Generate deterministic cache key from query parameters."""
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()
        key_data = f"{normalized_query}|{domain}|{prompt_name or 'default'}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def get(
        self,
        query: str,
        domain: str,
        prompt_name: Optional[str] = None,
        app_context: Optional[dict] = None,
    ) -> Optional[dict]:
        """
        Get cached response if available and not expired.

        Args:
            query: The user's query text
            domain: The collection domain
            prompt_name: Optional prompt template name
            app_context: Optional dynamic context (bypasses cache)

        Returns:
            Cached response dict, or None if not cached/expired
        """
        # Never use cache when app_context is provided (dynamic results)
        if app_context:
            logger.debug("Cache bypass: app_context provided")
            return None

        key = self._make_key(query, domain, prompt_name)
        entry = self._cache.get(key)

        if entry is None:
            self.misses += 1
            return None

        if entry.is_expired():
            del self._cache[key]
            self.misses += 1
            logger.debug(f"Cache miss (expired after {entry.age_seconds():.1f}s): {key[:8]}...")
            return None

        self.hits += 1
        logger.debug(f"Cache hit (age {entry.age_seconds():.1f}s): {key[:8]}...")
        return entry.response

    def set(
        self,
        query: str,
        domain: str,
        response: dict,
        prompt_name: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> None:
        """
        Store response in cache.

        Args:
            query: The user's query text
            domain: The collection domain
            response: The response dict to cache
            prompt_name: Optional prompt template name
            ttl: Optional TTL override (seconds)
        """
        # Evict oldest entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest()

        key = self._make_key(query, domain, prompt_name)
        self._cache[key] = CacheEntry(
            response=response,
            created_at=time.time(),
            ttl_seconds=ttl or self.default_ttl,
            query_hash=key,
        )
        logger.debug(f"Cache set: {key[:8]}... (TTL={ttl or self.default_ttl}s)")

    def _evict_oldest(self, count: int = 100) -> None:
        """Evict oldest cache entries to make room."""
        if not self._cache:
            return

        # Sort by creation time, oldest first
        sorted_keys = sorted(
            self._cache.keys(), key=lambda k: self._cache[k].created_at
        )

        # Evict oldest entries
        evict_count = min(count, len(sorted_keys))
        for key in sorted_keys[:evict_count]:
            del self._cache[key]

        self.evictions += evict_count
        logger.info(f"Evicted {evict_count} oldest cache entries")

    def invalidate(self, domain: Optional[str] = None) -> int:
        """
        Invalidate cache entries.

        Args:
            domain: If provided, only invalidate entries for this domain
                   (requires storing domain in entry, currently clears all)

        Returns:
            Number of entries invalidated
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache invalidated: {count} entries cleared")
        return count

    def stats(self) -> dict:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hits / total_requests, 3) if total_requests > 0 else 0,
            "size": len(self._cache),
            "max_size": self.max_size,
            "evictions": self.evictions,
            "default_ttl_seconds": self.default_ttl,
        }


# Global cache instance (singleton)
_response_cache: Optional[ResponseCache] = None


def get_response_cache(
    default_ttl: int = 3600, max_size: int = 1000
) -> ResponseCache:
    """
    Get or create the global response cache.

    Args:
        default_ttl: Default TTL in seconds (only used on first call)
        max_size: Maximum cache size (only used on first call)

    Returns:
        Global ResponseCache instance
    """
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache(default_ttl=default_ttl, max_size=max_size)
        logger.info(f"Initialized response cache (TTL={default_ttl}s, max={max_size})")
    return _response_cache


def invalidate_cache() -> int:
    """Invalidate the global cache. Returns count of entries cleared."""
    global _response_cache
    if _response_cache:
        return _response_cache.invalidate()
    return 0


def get_cache_stats() -> dict:
    """Get global cache statistics."""
    global _response_cache
    if _response_cache:
        return _response_cache.stats()
    return {"status": "not_initialized"}
