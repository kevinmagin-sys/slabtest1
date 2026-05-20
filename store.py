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

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        with self._lock:
            self._data[key] = value
            if ttl:
                self._expires[key] = time.time() + ttl

class MockQueue:
    def __init__(self):
        self._queue = {}
        self._index = 0
        self._lock = threading.Lock()

    def enqueue(self, item):
        with self._lock:
            self._queue[self._index] = item
            self._index += 1

    def dequeue(self):
        with self._lock:
            if not self._queue:
                return None
            first_key = min(self._queue.keys())
            return self._queue.pop(first_key)
