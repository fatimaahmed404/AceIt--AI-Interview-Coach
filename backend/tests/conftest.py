"""Pytest path setup so tests import backend modules (and sibling helpers)."""
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_TESTS_DIR = os.path.dirname(__file__)
for p in (_BACKEND_ROOT, _TESTS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """
    The in-process rate limiter persists across requests. Tests create many
    accounts, so clear it before each test to avoid cross-test 429s.
    """
    try:
        from auth import ratelimit
        ratelimit.clear_all()
    except Exception:  # noqa: BLE001
        pass
    yield
