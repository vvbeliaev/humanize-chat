from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StyleConfig:
    typo_rate: float = 0.03
    max_chunk_length: int = 120
    emoji_frequency: float = 0.15
    abbreviations: bool = True


@dataclass(frozen=True)
class TimingConfig:
    typing_speed_cps: float = 4.5  # chars/second base rate
    typing_jitter: float = 0.25  # ± fraction
    inter_chunk_pause_min: float = 0.8
    inter_chunk_pause_max: float = 3.5


@dataclass(frozen=True)
class ScheduleEntry:
    from_time: str  # "HH:MM"
    to_time: str  # "HH:MM"
    state: str  # PersonaState name (uppercase)


@dataclass(frozen=True)
class PersonaConfig:
    name: str
    timezone: str
    schedule: tuple[ScheduleEntry, ...]
    jitter_minutes: int = 20
    style: StyleConfig = field(default_factory=StyleConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PersonaConfig:
        p = data.get("persona", data)
        raw_schedule = p.get("schedule", {})

        _section_to_state = {
            "sleep": "ASLEEP",
            "morning": "DROWSY",
            "work": "BUSY",
            "evening": "AVAILABLE",
        }

        from .state import PersonaState  # local import avoids circular at module level

        valid_states = {s.name for s in PersonaState}

        entries: list[ScheduleEntry] = []
        for key, val in raw_schedule.items():
            if isinstance(val, dict) and "from" in val and "to" in val:
                state_name = str(
                    val.get("state", _section_to_state.get(key, "AVAILABLE"))
                ).upper()
                if state_name not in valid_states:
                    raise ValueError(
                        f"Unknown state {state_name!r} in schedule key {key!r}. "
                        f"Valid states: {sorted(valid_states)}"
                    )
                entries.append(
                    ScheduleEntry(from_time=val["from"], to_time=val["to"], state=state_name)
                )

        raw_style = p.get("style", {})
        raw_pause = p.get("timing", {}).get("inter_chunk_pause", {})
        raw_timing = p.get("timing", {})

        return cls(
            name=p.get("name", "Bot"),
            timezone=p.get("timezone", "UTC"),
            schedule=tuple(entries),
            jitter_minutes=p.get("jitter_minutes", 20),
            style=StyleConfig(
                typo_rate=raw_style.get("typo_rate", 0.03),
                max_chunk_length=raw_style.get("max_chunk_length", 120),
                emoji_frequency=raw_style.get("emoji_frequency", 0.15),
                abbreviations=raw_style.get("abbreviations", True),
            ),
            timing=TimingConfig(
                typing_speed_cps=raw_timing.get("typing_speed_cps", 4.5),
                typing_jitter=raw_timing.get("typing_jitter", 0.25),
                inter_chunk_pause_min=raw_pause.get("min", 0.8)
                if isinstance(raw_pause, dict)
                else 0.8,
                inter_chunk_pause_max=raw_pause.get("max", 3.5)
                if isinstance(raw_pause, dict)
                else 3.5,
            ),
        )

    @classmethod
    def from_yaml(cls, path: str) -> PersonaConfig:
        import yaml  # optional dep

        with open(path) as f:
            return cls.from_dict(yaml.safe_load(f))

    @classmethod
    def default(cls) -> PersonaConfig:
        return cls.from_dict(
            {
                "persona": {
                    "name": "Bot",
                    "timezone": "UTC",
                    "schedule": {
                        "sleep": {"from": "23:30", "to": "08:00"},
                        "morning": {"from": "08:00", "to": "09:30", "state": "DROWSY"},
                        "work": {"from": "09:30", "to": "18:00", "state": "BUSY"},
                        "evening": {"from": "18:00", "to": "23:30", "state": "AVAILABLE"},
                    },
                }
            }
        )
