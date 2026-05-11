import asyncio
import time
from enum import Enum
from typing import Callable, Any
from config import CB_FAILURE_THRESHOLD, CB_RESET_TIMEOUT_SECONDS


class CBState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = CB_FAILURE_THRESHOLD,
                 reset_timeout: int = CB_RESET_TIMEOUT_SECONDS):
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._state = CBState.CLOSED
        self._failures = 0
        self._opened_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CBState:
        return self._state

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            if self._state == CBState.OPEN:
                if time.monotonic() - self._opened_at >= self.reset_timeout:
                    self._state = CBState.HALF_OPEN
                else:
                    raise RuntimeError(f"Circuit '{self.name}' is OPEN — agent unavailable")

        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                self._failures = 0
                self._state = CBState.CLOSED
            return result
        except Exception as exc:
            async with self._lock:
                self._failures += 1
                if self._failures >= self.failure_threshold:
                    self._state = CBState.OPEN
                    self._opened_at = time.monotonic()
            raise exc


_breakers: dict[str, CircuitBreaker] = {}


def get_breaker(name: str) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name)
    return _breakers[name]
