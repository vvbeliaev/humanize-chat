"""Minimal reference transport that prints to stdout — useful for local testing."""

import logging

from .base import Transport
from ..core.events import DeferredEvent

logger = logging.getLogger(__name__)


class PrintTransport(Transport):
    async def send_typing(self) -> None:
        print("[typing...]")

    async def send_message(self, text: str) -> None:
        print(f"[msg] {text}")

    async def defer(self, event: DeferredEvent) -> None:
        print(f"[deferred until {event.respond_at.isoformat()}]")
