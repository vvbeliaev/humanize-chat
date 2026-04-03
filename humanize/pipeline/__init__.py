from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

from ..core.clock import CircadianClock
from ..core.events import DeferredEvent, Event, MessageEvent, TypingStartEvent
from ..core.persona import PersonaConfig
from ..core.state import PersonaState
from .splitter import MessageSplitter
from .style import StyleTransformer
from .timing import TimingCalculator


class ResponsePipeline:
    """
    Transform an LLM response into a stream of timed delivery events.

    Usage::

        pipeline = ResponsePipeline(config)
        for event in pipeline.process(llm_text):
            transport.handle(event)

    The caller (transport adapter) is responsible for acting on events:
    - ``TypingStartEvent`` → show typing indicator, sleep ``duration`` seconds
    - ``MessageEvent``     → sleep ``delay_before`` seconds, send message
    - ``DeferredEvent``    → queue message; deliver at ``respond_at``
    """

    def __init__(self, config: PersonaConfig) -> None:
        self._clock = CircadianClock(config)
        self._splitter = MessageSplitter(config.style.max_chunk_length)
        self._style = StyleTransformer(config.style)
        self._timing = TimingCalculator(config.timing)

    def process(
        self,
        text: str,
        state: PersonaState | None = None,
        now: datetime | None = None,
    ) -> Iterator[Event]:
        """Yield events for the transport layer to consume."""
        if state is None:
            state = self._clock.current_state(now)

        if state == PersonaState.ASLEEP:
            yield DeferredEvent(respond_at=self._clock.next_wake_time(now))
            return

        chunks = self._splitter.split(text, state)

        for i, chunk in enumerate(chunks):
            styled = self._style.transform(chunk, state)
            typing_dur = self._timing.typing_duration(styled, state)
            pause = self._timing.inter_chunk_pause(state) if i > 0 else 0.0

            yield TypingStartEvent(duration=typing_dur)
            yield MessageEvent(text=styled, delay_before=pause)
