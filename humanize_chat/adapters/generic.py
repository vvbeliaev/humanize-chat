"""Minimal reference transport that prints to stdout — useful for local testing."""

import logging

from .base import Transport
from ..core.events import DeferredEvent

logger = logging.getLogger(__name__)

_msg_counter = 0


class PrintTransport(Transport):
    async def send_typing(self) -> None:
        print("[typing...]")

    async def send_message(self, text: str) -> str:
        global _msg_counter
        _msg_counter += 1
        ref = f"msg_{_msg_counter}"
        print(f"[{ref}] {text}")
        return ref

    async def send_reaction(self, emoji: str) -> None:
        print(f"[reaction] {emoji}")

    async def edit_message(self, message_ref: str, new_text: str) -> None:
        print(f"[edit {message_ref}] {new_text}")

    async def mark_read(self) -> None:
        print("[read]")

    async def defer(self, event: DeferredEvent) -> None:
        kind = "intentional" if event.intentional else "unavailable"
        print(f"[deferred/{kind}] until {event.respond_at.isoformat()}")
