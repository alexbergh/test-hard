"""Utilities for deterministic timestamps across simulations."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

__all__ = ["TimeSequencer", "resolve_base_timestamp"]


def _parse_timestamp(raw: str) -> datetime:
    """Parse a timestamp from an ISO string or Unix epoch seconds."""
    text = raw.strip()
    # Try epoch seconds first
    if text.isdigit():
        return datetime.fromtimestamp(int(text), tz=timezone.utc)
    # Try ISO-8601 formats, accepting strings without timezone
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:  # pragma: no cover - defensive branch
        raise ValueError(f"Unsupported timestamp format: {raw!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed


def resolve_base_timestamp() -> datetime:
    """Resolve the baseline timestamp for deterministic simulations."""
    env_value = os.environ.get("HARDENING_FIXED_TIMESTAMP")
    if env_value:
        try:
            base = _parse_timestamp(env_value)
        except ValueError:
            base = datetime.now(timezone.utc)
    else:
        base = datetime.now(timezone.utc)
    return base.replace(microsecond=0)


class TimeSequencer:
    """Deterministic time generator that advances in fixed steps."""

    def __init__(self, start: Optional[datetime] = None, *, step_seconds: int = 60):
        if step_seconds <= 0:
            raise ValueError("step_seconds must be positive")
        base = start or resolve_base_timestamp()
        if base.tzinfo is None:
            base = base.replace(tzinfo=timezone.utc)
        else:
            base = base.astimezone(timezone.utc)
        self._start = base.replace(microsecond=0)
        self._step = timedelta(seconds=step_seconds)
        self._index = -1

    def next_datetime(self) -> datetime:
        """Return the next datetime in the sequence and advance the cursor."""
        self._index += 1
        return self._start + self._step * self._index

    def next_iso(self) -> str:
        """Return the next timestamp as an ISO string."""
        return self.next_datetime().isoformat()

    def peek_datetime(self) -> datetime:
        """Return the upcoming datetime without advancing the cursor."""
        return self._start + self._step * (self._index + 1)

    def last_datetime(self) -> Optional[datetime]:
        """Return the last emitted datetime if available."""
        if self._index < 0:
            return None
        return self._start + self._step * self._index

    def clone(self, *, offset_steps: int = 0) -> "TimeSequencer":
        """Create a new sequencer with the same step and adjusted start."""
        start = self._start + self._step * offset_steps
        clone = TimeSequencer(start=start, step_seconds=int(self._step.total_seconds()))
        return clone

    def reset(self) -> None:
        """Reset the cursor to the initial position."""
        self._index = -1


