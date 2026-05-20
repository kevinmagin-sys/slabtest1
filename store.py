import threading
import time

class SharedStore:
    def __init__(self):
        self._data = {}
        self._expires = {}
        self._lock = threading.Lock()

    def _is_expired(self, key):
        if key in self._expires:
            if time.time() > self._expires[key]:
                self._data.pop(key, None)
                self._expires.pop(key, None)
                return True
        return False

    def get(self, key):
        with self._lock:
            if self._is_expired(key):
                return None
            return self._data.get(key)

    def set(self, key, value):
        with self._lock:
            self._data[key] = value
            self._expires.pop(key, None)

    def delete(self, key):
        with self._lock:
            self._data.pop(key, None)
            self._expires.pop(key, None)

    def exists(self, key):
        with self._lock:
            if self._is_expired(key):
                return False
            return key in self._data

    def incr(self, key):
        with self._lock:
            if self._is_expired(key):
                self._data[key] = 0
            val = self._data.get(key, 0)
            if not isinstance(val, int):
                val = 0
            new_val = val + 1
            self._data[key] = new_val
            return new_val

    def expire(self, key, seconds):
        with self._lock:
            if key in self._data:
                self._expires[key] = time.time() + seconds
                return True
            return False
