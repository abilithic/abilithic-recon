"""Cooperative cancellation token, propagated to every network task."""
from __future__ import annotations

import threading


class CancelToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        if self._event.is_set():
            raise CancelledError()

    def wait(self, timeout: float) -> bool:
        """Sleep up to timeout but wake immediately on cancel. Returns cancelled."""
        return self._event.wait(timeout)


class CancelledError(Exception):
    """Raised internally to unwind a cancelled scan."""
