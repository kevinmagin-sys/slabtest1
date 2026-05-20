import threading
import time
from typing import Any, Optional

class SharedStore:
    def __init__(self):
        self._data = {}
        self._expires = {}
        self._lock = threading.Lock()

    def _is_expired(self, key: str) -> bool:
        if key in self._expires:
            if time.time() > self._expires[key]:
                self._data.pop(key, None)
                self._expires.pop(key, None)
                return True
        return False

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if self._is_expired(key):
                return None
            return self._data.get(key)

    def set(self, key: str, value: Any):
        with self._lock:
            self._data[key] = value
            self._expires.pop(key, None)

    def delete(self, key: str) -> bool:
        with self._lock:
            existed = key in self._data
            self._data.pop(key, None)
            self._expires.pop(key, None)
            return existed

    def exists(self, key: str) -> bool:
        with self._lock:
            if self._is_expired(key):
                return False
            return key in self._data

    def incr(self, key: str) -> int:
        with self._lock:
            if self._is_expired(key):
                self._data[key] = 0
            
            val = self._data.get(key, 0)
            if not isinstance(val, int):
                raise TypeError("Value is not an integer")
            
            new_val = val + 1
            self._data[key] = new_val
            return new_val

    def expire(self, key: str, ttl: int) -> bool:
        with self._lock:
            if self._is_expired(key) or key not in self._data:
                return False
            self._expires[key] = time.time() + ttl
            return True
