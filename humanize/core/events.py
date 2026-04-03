from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TypingStartEvent:
    duration: float  # seconds to show "typing..." indicator


@dataclass(frozen=True)
class MessageEvent:
    text: str
    delay_before: float  # pause before sending this chunk (seconds)


@dataclass(frozen=True)
class DeferredEvent:
    respond_at: datetime  # when the persona will wake up and answer


Event = TypingStartEvent | MessageEvent | DeferredEvent
