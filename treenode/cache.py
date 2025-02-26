# -*- coding: utf-8 -*-
"""
TreeNode Cache Module

This module provides a singleton-based caching system for TreeNode models.
It includes optimized key generation, cache size tracking,
and an eviction mechanism to ensure efficient memory usage.

Features:
- Singleton cache instance to prevent redundant allocations.
- Custom cache key generation using function parameters.
- Automatic cache eviction when memory limits are exceeded.
- Decorator `@cached_method` for caching method results.

Version: 2.0.0
Author: Timur Kady
Email: timurkady@yandex.com
"""


from django.core.cache import caches
from django.conf import settings
import threading
import hashlib
import json
import logging
from pympler import asizeof

from .utils.base36 import to_base36

logger = logging.getLogger(__name__)


# ---------------------------------------------------
# Caching
# ---------------------------------------------------

class TreeNodeCache:
    """Singleton-класс для управления кэшем TreeNode."""

    _instance = None
    _lock = threading.Lock()
    _keys = dict()
    _total_size = 0
    _cache_limit = 0

    def __new__(cls):
        """Create only one instance of the class (Singleton)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TreeNodeCache, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache."""
        self.cache_timeout = None
        limit = getattr(settings, 'TREENODE_CACHE_LIMIT', 100)*1024*1024
        self._cache_limit = limit
        self.cache_timeout = None
        cache_name = 'treenode' if 'treenode' in settings.CACHES else 'default'
        self.cache = caches[cache_name]
        self._total_size = 0
        self.cache.clear()

    def generate_cache_key(self, label, func_name, unique_id, *args, **kwargs):
        """
        Generate Cache Key.

        Generates a cache key of the form:
            <model_name>_<func_name>_<id>_<hash>,
        where <hash> is calculated from the function parameters
        (args and kwargs).
        If the parameters can be serialized via JSON, use this, otherwise we
        use repr to generate the string.
        """
        try:
            # Sort dictionary keys to ensure determinism.
            params_repr = json.dumps(
                (args, kwargs),
                sort_keys=True,
                default=str
            )
        except (TypeError, ValueError) as e:
            # If JSON serialization fails, use repr.
            params_repr = repr((args, kwargs))
            logger.warning(f"Failed to serialize cache key params: {e}")

        # Calculate the MD5 hash from the received string.
        hash_value = hashlib.sha256(params_repr.encode("utf-8")).hexdigest()

        # Forming the final key.
        cache_key = f"{label}_{func_name}_{unique_id}_{hash_value}"

        return cache_key

    def get_obj_size(self, value):
        """Determine the size of the object in bytes."""
        try:
            return len(json.dumps(value).encode("utf-8"))
        except (TypeError, ValueError):
            return asizeof.asizeof(value)

    def cache_size(self):
        """Return the total size of the cache in bytes."""
        return self._total_size

    def set(self, cache_key, value):
        """Push to cache."""
        size = self.get_obj_size(value)
        self.cache.set(cache_key, value, timeout=self.cache_timeout)

        # Update cache size
        if cache_key in self._keys:
            self._total_size -= self._keys[cache_key]
        self._keys[cache_key] = size
        self._total_size += size

        # Check if the limit has been exceeded
        self._evict_cache()

    def get(self, cache_key):
        """Get from cache."""
        return self.cache.get(cache_key)

    def invalidate(self, label):
        """Clear cache for a specific model only."""
        prefix = f"{label}_"
        keys_to_remove = [key for key in self._keys if key.startswith(prefix)]
        for key in keys_to_remove:
            self.cache.delete(key)
            self._total_size -= self._keys.pop(key, 0)
            if self._total_size < 0:
                self._total_size = 0

    def clear(self):
        """Full cache clearing."""
        self.cache.clear()
        self._keys.clear()
        self._total_size = 0

    def _evict_cache(self):
        """Delete old entries if the cache has exceeded the limit."""
        if self._total_size <= self._cache_limit:
            # If the size is within the limit, do nothing
            return

        if not self._keys:
            self.clear()

        logger.warning(f"Cache limit exceeded! Current size: \
{self._total_size}, Limit: {self._cache_limit}")

        # Sort keys by insertion order (FIFO)
        keys_sorted = list(self._keys.keys())

        keys_to_delete = []
        freed_size = 0

        # Delete old keys until we reach the limit
        for key in keys_sorted:
            freed_size += self._keys[key]
            keys_to_delete.append(key)
            if self._total_size - freed_size <= self._cache_limit:
                break

        # Delete keys in batches (delete_many)
        self.cache.delete_many(keys_to_delete)

        # Update data in `_keys` and `_total_size`
        for key in keys_to_delete:
            self._total_size -= self._keys.pop(key, 0)

        logger.info(f"Evicted {len(keys_to_delete)} keys from cache, \
freed {freed_size} bytes.")


# Create a global cache object (there is only one for the entire system)
treenode_cache = TreeNodeCache()


# ---------------------------------------------------
# Decorator
# ---------------------------------------------------


def cached_method(func):
    """
    Decorate instance methods for caching.

    The decorator caches the results of the decorated class or instance method.
    If the cache is cleared or invalidated, the cached results will be
    recalculated.

    Usage:
        @cached_tree_method
        def model_method(self):
            # Tree method logic
    """

    def wrapper(self, *args, **kwargs):
        # Generate a cache key.
        if isinstance(self, type):
            # Если self — класс, используем его имя
            unique_id = to_base36(id(self))
            label = getattr(self._meta, 'label', self.__name__)
        else:
            unique_id = getattr(self, "pk", id(self))
            label = self._meta.label

        cache_key = treenode_cache.generate_cache_key(
            label,
            func.__name__,
            unique_id,
            *args,
            **kwargs
        )

        # Retrieving from cache
        value = treenode_cache.get(cache_key)

        if value is None:
            value = func(self, *args, **kwargs)

            # Push to cache
            treenode_cache.set(cache_key, value)
        return value
    return wrapper


# The End
