from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

from ..core.clock import CircadianClock
from ..core.events import (
    DeferredEvent,
    Event,
    MessageEvent,
    ReadAckEvent,
    ReactionEvent,
    TypingStartEvent,
)
from ..core.intent import ConversationIntent
from ..core.persona import PersonaConfig
from ..core.state import PersonaState
from .splitter import MessageSplitter
from .style import StyleTransformer
from .timing import TimingCalculator

class ResponsePipeline:
    """
    Transform an LLM response into a stream of timed delivery events.

    Takes two independent inputs:
    - ``PersonaState``       — availability / energy (clock-driven)
    - ``ConversationIntent`` — willingness to engage (conversation-driven)

    Transport is responsible for acting on each event type:

    ===================  ================================================
    TypingStartEvent     show typing indicator, sleep ``duration`` seconds
    MessageEvent         sleep ``delay_before``, send message
    ReactionEvent        sleep ``delay``, react to incoming message
    ReadAckEvent         sleep ``delay``, mark incoming message as read
    EditMessageEvent     sleep ``delay``, edit a previously sent message
    DeferredEvent        queue; re-deliver at ``respond_at``
    ===================  ================================================
    """

    def __init__(self, config: PersonaConfig) -> None:
        self._clock = CircadianClock(config)
        self._splitter = MessageSplitter(
            config.style.max_chunk_length,
            config.style.split_mode,
            config.style.max_messages,
        )
        self._style = StyleTransformer(config.style)
        self._timing = TimingCalculator(config.timing)
        self._rng = self._style._rng  # share seed for consistent behaviour
        self._reaction_pool = list(config.style.reaction_pool)

    def process(
        self,
        text: str,
        state: PersonaState | None = None,
        intent: ConversationIntent = ConversationIntent.NORMAL,
        now: datetime | None = None,
    ) -> Iterator[Event]:
        """Yield events for the transport layer to consume."""
        if state is None:
            state = self._clock.current_state(now)

        # --- DEFERRING: saw it, not replying now ---
        if intent == ConversationIntent.DEFERRING:
            yield ReadAckEvent(delay=self._timing.read_delay(state))
            yield DeferredEvent(
                respond_at=self._clock.next_wake_time(now),
                intentional=True,
            )
            return

        # --- AVOIDING: doesn't want to engage ---
        if intent == ConversationIntent.AVOIDING:
            reaction = self._rng.choice(self._reaction_pool)
            yield ReactionEvent(emoji=reaction, delay=self._timing.read_delay(state))
            # Optionally yield a very short message — runtime passes "" to suppress
            if text:
                styled = self._style.transform(text, state)
                yield TypingStartEvent(duration=self._timing.typing_duration(styled, state))
                yield MessageEvent(text=styled, delay_before=0.0)
            return

        # --- ASLEEP: unavailable ---
        if state == PersonaState.ASLEEP:
            yield DeferredEvent(
                respond_at=self._clock.next_wake_time(now),
                intentional=False,
            )
            return

        # --- CATCHING_UP: burst after silence ---
        if intent == ConversationIntent.CATCHING_UP:
            yield ReadAckEvent(delay=1.0)
            chunks = self._splitter.split(text, PersonaState.ENGAGED)
            for i, chunk in enumerate(chunks):
                styled = self._style.transform(chunk, state)
                yield TypingStartEvent(duration=self._timing.typing_duration(styled, state))
                # Shorter pauses — catching up feels rushed
                pause = self._timing.inter_chunk_pause(PersonaState.ENGAGED) if i > 0 else 0.0
                yield MessageEvent(text=styled, delay_before=pause)
            return

        # --- NORMAL ---
        chunks = self._splitter.split(text, state)
        for i, chunk in enumerate(chunks):
            styled = self._style.transform(chunk, state)
            typing_dur = self._timing.typing_duration(styled, state)
            pause = self._timing.inter_chunk_pause(state) if i > 0 else 0.0
            yield TypingStartEvent(duration=typing_dur)
            yield MessageEvent(text=styled, delay_before=pause)
