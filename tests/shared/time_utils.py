"""Вспомогательные утилиты для детерминированных меток времени в симуляциях."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

__all__ = ["TimeSequencer", "now_iso", "now_datetime", "make_sequencer"]


def _parse_base(value: str) -> datetime:
    candidate = value.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"
    dt = datetime.fromisoformat(candidate)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _determine_base() -> datetime:
    env_value = os.environ.get("HARDENING_FIXED_TIMESTAMP")
    if env_value:
        try:
            return _parse_base(env_value)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


class TimeSequencer:
    """Генератор последовательных временных меток."""

    def __init__(self, *, base: Optional[datetime] = None, step_seconds: float = 1.0) -> None:
        self._base = (base or _determine_base()).astimezone(timezone.utc)
        self._step = timedelta(seconds=step_seconds)
        self._index = 0

    def next_datetime(self) -> datetime:
        value = self._base + self._step * self._index
        self._index += 1
        return value

    def next_iso(self) -> str:
        return self.next_datetime().isoformat()


_global_sequencer: TimeSequencer | None = None


def _global() -> TimeSequencer:
    global _global_sequencer
    if _global_sequencer is None:
        _global_sequencer = TimeSequencer()
    return _global_sequencer


def now_datetime() -> datetime:
    return _global().next_datetime()


def now_iso() -> str:
    return _global().next_iso()


def make_sequencer(*, step_seconds: float = 1.0) -> TimeSequencer:
    return TimeSequencer(step_seconds=step_seconds)
