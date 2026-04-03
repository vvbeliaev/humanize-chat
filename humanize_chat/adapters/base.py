from __future__ import annotations

import asyncio
import math
from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..core.events import (
    DeferredEvent,
    EditMessageEvent,
    Event,
    MessageEvent,
    ReadAckEvent,
    ReactionEvent,
    TypingStartEvent,
)


class Transport(ABC):
    """Protocol a channel adapter must implement."""

    @abstractmethod
    async def send_typing(self) -> None: ...

    @abstractmethod
    async def send_message(self, text: str) -> str:
        """Send message; return a message_ref for potential future edits."""
        ...

    @abstractmethod
    async def send_reaction(self, emoji: str) -> None:
        """React to the most recently received message."""
        ...

    @abstractmethod
    async def edit_message(self, message_ref: str, new_text: str) -> None: ...

    @abstractmethod
    async def mark_read(self) -> None:
        """Mark the incoming message(s) as read."""
        ...

    @abstractmethod
    async def defer(self, event: DeferredEvent) -> None: ...


class BaseAdapter:
    """Drive a ResponsePipeline event stream through a Transport."""

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def deliver(self, events: Iterable[Event]) -> None:
        for event in events:
            await self._dispatch(event)

    async def _dispatch(self, event: Event) -> None:
        if isinstance(event, TypingStartEvent):
            await self._transport.send_typing()
            if not math.isinf(event.duration):
                await asyncio.sleep(event.duration)

        elif isinstance(event, MessageEvent):
            if event.delay_before > 0:
                await asyncio.sleep(event.delay_before)
            await self._transport.send_message(event.text)

        elif isinstance(event, ReactionEvent):
            if event.delay > 0:
                await asyncio.sleep(event.delay)
            await self._transport.send_reaction(event.emoji)

        elif isinstance(event, ReadAckEvent):
            if event.delay > 0:
                await asyncio.sleep(event.delay)
            await self._transport.mark_read()

        elif isinstance(event, EditMessageEvent):
            if event.delay > 0:
                await asyncio.sleep(event.delay)
            await self._transport.edit_message(event.message_ref, event.new_text)

        elif isinstance(event, DeferredEvent):
            await self._transport.defer(event)
