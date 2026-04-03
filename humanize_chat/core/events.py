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
class ReactionEvent:
    """Add an emoji reaction to the incoming message before (or instead of) replying."""

    emoji: str    # e.g. "👀", "❤️", "😂"
    delay: float  # seconds after receiving message before reacting


@dataclass(frozen=True)
class ReadAckEvent:
    """Simulate the moment the persona 'reads' the message (triggers seen indicator)."""

    delay: float  # seconds before marking as read


@dataclass(frozen=True)
class EditMessageEvent:
    """Edit a previously sent message — models self-correction behaviour."""

    message_ref: str  # correlates to a prior MessageEvent (set by transport)
    new_text: str
    delay: float      # seconds after original send before editing


@dataclass(frozen=True)
class DeferredEvent:
    respond_at: datetime  # when the persona will answer
    intentional: bool = False  # True = chose not to reply now; False = unavailable


Event = (
    TypingStartEvent
    | MessageEvent
    | ReactionEvent
    | ReadAckEvent
    | EditMessageEvent
    | DeferredEvent
)
