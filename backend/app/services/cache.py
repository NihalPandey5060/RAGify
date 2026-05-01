from hashlib import md5
from datetime import datetime, timedelta
from typing import Optional


cache_store = {}  # Format: {cache_key: {"data": any, "created_at": datetime, "ttl": int}}
CACHE_TTL_MINUTES = 60


def get_cache_key(query: str, user_id: str) -> str:
    """Generate a cache key for a query."""
    combined = f"{user_id}:{query}"
    return md5(combined.encode()).hexdigest()


def set_cache(cache_key: str, data: any, ttl_minutes: int = CACHE_TTL_MINUTES):
    """Store data in cache with TTL."""
    cache_store[cache_key] = {
        "data": data,
        "created_at": datetime.utcnow(),
        "ttl_minutes": ttl_minutes,
    }


def get_cache(cache_key: str) -> Optional[any]:
    """Retrieve data from cache if not expired."""
    if cache_key not in cache_store:
        return None
    
    cached = cache_store[cache_key]
    age_minutes = (datetime.utcnow() - cached["created_at"]).total_seconds() / 60
    
    if age_minutes > cached["ttl_minutes"]:
        del cache_store[cache_key]
        return None
    
    return cached["data"]


def clear_cache(cache_key: str = None):
    """Clear cache entry or entire cache."""
    if cache_key:
        cache_store.pop(cache_key, None)
    else:
        cache_store.clear()
