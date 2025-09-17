"""
Redis cache utilities for caching and session management.
"""
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import timedelta
import redis
from app.config import settings


class RedisCache:
    """Redis cache manager."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            password=settings.REDIS_PASSWORD,
            decode_responses=False,  # We'll handle encoding ourselves
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_value = self._serialize(value)
            result = self.redis_client.set(key, serialized_value, ex=expire)
            return result is True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def get(self, key: str) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        try:
            cached_value = self.redis_client.get(key)
            if cached_value is None:
                return None
            return self._deserialize(cached_value)
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key to delete
        
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            result = self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key to check
        
        Returns:
            True if key exists, False otherwise
        """
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            seconds: Expiration time in seconds
        
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.redis_client.expire(key, seconds) > 0
        except Exception as e:
            print(f"Cache expire error: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Get time to live for a key.
        
        Args:
            key: Cache key
        
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            print(f"Cache TTL error: {e}")
            return -2
    
    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a numeric value.
        
        Args:
            key: Cache key
            amount: Amount to increment
        
        Returns:
            New value after increment, or None if error
        """
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            print(f"Cache incr error: {e}")
            return None
    
    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Decrement a numeric value.
        
        Args:
            key: Cache key
            amount: Amount to decrement
        
        Returns:
            New value after decrement, or None if error
        """
        try:
            return self.redis_client.decr(key, amount)
        except Exception as e:
            print(f"Cache decr error: {e}")
            return None
    
    def hset(self, name: str, mapping: Dict[str, Any]) -> bool:
        """
        Set hash fields.
        
        Args:
            name: Hash name
            mapping: Field-value mapping
        
        Returns:
            True if successful, False otherwise
        """
        try:
            serialized_mapping = {k: self._serialize(v) for k, v in mapping.items()}
            result = self.redis_client.hset(name, mapping=serialized_mapping)
            return result >= 0
        except Exception as e:
            print(f"Cache hset error: {e}")
            return False
    
    def hget(self, name: str, key: str) -> Any:
        """
        Get hash field value.
        
        Args:
            name: Hash name
            key: Field key
        
        Returns:
            Field value or None if not found
        """
        try:
            value = self.redis_client.hget(name, key)
            if value is None:
                return None
            return self._deserialize(value)
        except Exception as e:
            print(f"Cache hget error: {e}")
            return None
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """
        Get all hash fields and values.
        
        Args:
            name: Hash name
        
        Returns:
            Dictionary of all fields and values
        """
        try:
            hash_data = self.redis_client.hgetall(name)
            return {k.decode(): self._deserialize(v) for k, v in hash_data.items()}
        except Exception as e:
            print(f"Cache hgetall error: {e}")
            return {}
    
    def hdel(self, name: str, *keys: str) -> int:
        """
        Delete hash fields.
        
        Args:
            name: Hash name
            keys: Field keys to delete
        
        Returns:
            Number of fields deleted
        """
        try:
            return self.redis_client.hdel(name, *keys)
        except Exception as e:
            print(f"Cache hdel error: {e}")
            return 0
    
    def flush_all(self) -> bool:
        """
        Clear all cache data.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.redis_client.flushall()
            return True
        except Exception as e:
            print(f"Cache flush_all error: {e}")
            return False
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if isinstance(value, (str, int, float, bool)):
            return json.dumps(value).encode()
        else:
            return pickle.dumps(value)
    
    def _deserialize(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first (for simple types)
            return json.loads(value.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fall back to pickle for complex types
            return pickle.loads(value)


# Global cache instance
cache = RedisCache()


class CacheKeys:
    """Cache key patterns."""
    
    # User caches
    USER_BY_ID = "user:id:{user_id}"
    USER_BY_EMAIL = "user:email:{email}"
    USER_PERMISSIONS = "user:permissions:{user_id}"
    
    # Hotel caches
    HOTEL_BY_ID = "hotel:id:{hotel_id}"
    HOTEL_SEARCH = "hotel:search:{search_hash}"
    HOTEL_AVAILABILITY = "hotel:availability:{hotel_id}:{date}"
    
    # Room caches
    ROOM_BY_ID = "room:id:{room_id}"
    ROOM_AVAILABILITY = "room:availability:{room_id}:{date}"
    
    # Booking caches
    BOOKING_BY_ID = "booking:id:{booking_id}"
    BOOKING_BY_REFERENCE = "booking:ref:{reference}"
    
    # Session caches
    USER_SESSION = "session:user:{user_id}"
    REFRESH_TOKEN = "refresh_token:{token_hash}"
    
    # Rate limiting
    RATE_LIMIT = "rate_limit:{identifier}:{window}"
    
    # Search results
    SEARCH_RESULTS = "search:{search_type}:{search_hash}"


class CacheManager:
    """High-level cache operations."""
    
    @staticmethod
    def cache_user(user_data: Dict[str, Any], expire: int = 3600) -> bool:
        """Cache user data."""
        user_id = user_data.get('id')
        email = user_data.get('email')
        
        if not user_id or not email:
            return False
        
        # Cache by ID and email
        cache.set(CacheKeys.USER_BY_ID.format(user_id=user_id), user_data, expire)
        cache.set(CacheKeys.USER_BY_EMAIL.format(email=email), user_data, expire)
        return True
    
    @staticmethod
    def get_cached_user(user_id: Optional[int] = None, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached user data."""
        if user_id:
            return cache.get(CacheKeys.USER_BY_ID.format(user_id=user_id))
        elif email:
            return cache.get(CacheKeys.USER_BY_EMAIL.format(email=email))
        return None
    
    @staticmethod
    def invalidate_user_cache(user_id: int, email: str) -> None:
        """Invalidate user cache."""
        cache.delete(CacheKeys.USER_BY_ID.format(user_id=user_id))
        cache.delete(CacheKeys.USER_BY_EMAIL.format(email=email))
        cache.delete(CacheKeys.USER_PERMISSIONS.format(user_id=user_id))
        cache.delete(CacheKeys.USER_SESSION.format(user_id=user_id))
    
    @staticmethod
    def cache_search_results(search_hash: str, results: Any, expire: int = 300) -> bool:
        """Cache search results."""
        return cache.set(CacheKeys.SEARCH_RESULTS.format(search_type="hotel", search_hash=search_hash), results, expire)
    
    @staticmethod
    def get_cached_search_results(search_hash: str) -> Any:
        """Get cached search results."""
        return cache.get(CacheKeys.SEARCH_RESULTS.format(search_type="hotel", search_hash=search_hash))
    
    @staticmethod
    def is_rate_limited(identifier: str, limit: int, window: int = 60) -> bool:
        """Check and apply rate limiting."""
        key = CacheKeys.RATE_LIMIT.format(identifier=identifier, window=window)
        current = cache.get(key) or 0
        
        if current >= limit:
            return True
        
        # Increment counter
        if current == 0:
            cache.set(key, 1, window)
        else:
            cache.incr(key)
        
        return False
