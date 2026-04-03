import re

from ..core.state import STATE_PARAMS, PersonaState

_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
_CLAUSE_BREAK = re.compile(r"(?<=[,—])\s+")
_MIN_FRAGMENT = 15  # chars; shorter fragments merge with the previous chunk


class MessageSplitter:
    """Split LLM text into human-sized message chunks."""

    def __init__(self, max_chunk_length: int = 120) -> None:
        self._max_chunk = max_chunk_length

    def split(self, text: str, state: PersonaState) -> list[str]:
        # 1. Split on sentence boundaries
        chunks = [c.strip() for c in _SENTENCE_END.split(text) if c.strip()]

        # 2. Further split long chunks on clause boundaries
        refined: list[str] = []
        for chunk in chunks:
            if len(chunk) > self._max_chunk:
                sub = [c.strip() for c in _CLAUSE_BREAK.split(chunk) if c.strip()]
                refined.extend(sub)
            else:
                refined.append(chunk)

        # 3. Merge short trailing fragments into the previous chunk
        merged: list[str] = []
        for chunk in refined:
            if merged and len(chunk) < _MIN_FRAGMENT:
                merged[-1] = merged[-1] + " " + chunk
            else:
                merged.append(chunk)

        # 4. Respect per-state chunk limit (BUSY/DROWSY: 1–2 msgs)
        max_chunks = STATE_PARAMS[state].max_chunks
        if max_chunks and len(merged) > max_chunks:
            # Collapse excess into the last allowed chunk
            merged = merged[:max_chunks - 1] + [" ".join(merged[max_chunks - 1:])]

        return merged or [text]
