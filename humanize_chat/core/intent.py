from enum import Enum


class ConversationIntent(Enum):
    """
    Orthogonal to PersonaState — models *why* the persona responds the way it does.

    PersonaState answers: "am I available right now?" (clock-driven)
    ConversationIntent answers: "do I want to engage with this?" (conversation-driven)

    Both are needed simultaneously. BUSY + DEFERRING differs from BUSY + NORMAL.
    """

    NORMAL = "normal"
    """Default: will respond when able."""

    DEFERRING = "deferring"
    """Saw the message, consciously postponing reply.
    Pipeline: ReadAckEvent → DeferredEvent(intentional=True)."""

    AVOIDING = "avoiding"
    """Doesn't want to engage with this topic/thread.
    Pipeline: optional ReactionEvent → minimal or no MessageEvent."""

    CATCHING_UP = "catching_up"
    """Returning after silence, responding to a backlog.
    Pipeline: burst of messages, short pauses, may open with an acknowledgement."""
