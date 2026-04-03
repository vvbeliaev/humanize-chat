from __future__ import annotations

import hashlib
import math
import random
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .persona import PersonaConfig
from .state import PersonaState


def _parse_time(s: str) -> time:
    h, m = map(int, s.split(":"))
    return time(h, m)


def _deterministic_jitter(day_key: str, slot_id: str, max_minutes: int) -> int:
    """Stable jitter for a given persona + day + schedule slot.

    Same persona sees the same jittered transitions for the whole day,
    preventing the clock from flickering on repeated calls.
    """
    seed = int(hashlib.md5(f"{day_key}:{slot_id}".encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    return rng.randint(-max_minutes, max_minutes)


def _shift_time(t: time, minutes: int) -> time:
    dt = datetime.combine(date.today(), t) + timedelta(minutes=minutes)
    return dt.time()


def _in_range(t: time, start: time, end: time) -> bool:
    """Check if t falls in [start, end), handling overnight ranges."""
    if start <= end:
        return start <= t < end
    # Overnight: e.g. 23:30 → 08:00
    return t >= start or t < end


class CircadianClock:
    """Maps current wall-clock time to a PersonaState based on schedule config."""

    def __init__(self, config: PersonaConfig) -> None:
        self._config = config
        self._tz = ZoneInfo(config.timezone)

    def current_state(self, now: datetime | None = None) -> PersonaState:
        if now is None:
            now = datetime.now(self._tz)
        else:
            now = now.astimezone(self._tz)

        current_time = now.time()
        day_key = now.strftime("%Y-%m-%d") + self._config.name

        for idx, entry in enumerate(self._config.schedule):
            from_t = _parse_time(entry.from_time)
            to_t = _parse_time(entry.to_time)

            from_t = _shift_time(
                from_t,
                _deterministic_jitter(day_key, f"{idx}:from", self._config.jitter_minutes),
            )
            to_t = _shift_time(
                to_t,
                _deterministic_jitter(day_key, f"{idx}:to", self._config.jitter_minutes),
            )

            if _in_range(current_time, from_t, to_t):
                return PersonaState[entry.state]

        return PersonaState.AVAILABLE

    def next_wake_time(self, now: datetime | None = None) -> datetime:
        """Return the nearest future moment when the persona is not ASLEEP."""
        if now is None:
            now = datetime.now(self._tz)
        else:
            now = now.astimezone(self._tz)

        check = now
        for _ in range(24 * 60):
            check += timedelta(minutes=1)
            if self.current_state(check) != PersonaState.ASLEEP:
                return check

        return now + timedelta(hours=8)  # unreachable fallback
