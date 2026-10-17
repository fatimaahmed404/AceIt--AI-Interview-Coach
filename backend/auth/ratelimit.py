"""
Lightweight fixed-window rate limiter.

In-process and dependency-free (suitable for a single-process dev/FYP backend).
For a multi-process production deployment this should be backed by Redis, which
is noted as a limitation in the docs. Keys are hashed identifiers (e.g. route +
client ip + email) so no raw secrets are stored.
"""
import time
import threading

_lock = threading.Lock()
_buckets = {}  # key -> (window_start_epoch, count)


def check(key, max_requests, window_seconds):
    """
    Register one hit for `key`. Returns (allowed: bool, retry_after: int).
    """
    now = time.time()
    with _lock:
        start, count = _buckets.get(key, (now, 0))
        if now - start >= window_seconds:
            start, count = now, 0
        count += 1
        _buckets[key] = (start, count)
        if count > max_requests:
            retry_after = int(window_seconds - (now - start)) + 1
            return False, max(1, retry_after)
        return True, 0


def reset(key):
    with _lock:
        _buckets.pop(key, None)


def clear_all():
    with _lock:
        _buckets.clear()
