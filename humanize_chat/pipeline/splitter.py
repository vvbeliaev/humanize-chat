import re
from typing import Literal

from ..core.state import STATE_PARAMS, PersonaState

_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")
_CLAUSE_BREAK = re.compile(r"(?<=[,—])\s+")

# Emotional mode: split on any punctuation pause + ellipsis
_EMOTIONAL_BREAK = re.compile(r"(?<=[,;—…])\s+|(?:\.{2,})\s*")

# Only clause-split a sentence if it's very long relative to the max chunk size.
# Multiplier of 2.5 means: for max_chunk=120 → only split sentences >300 chars.
_CLAUSE_SPLIT_MULTIPLIER = 2.5

# Merge fragments shorter than this into the previous chunk — within the same
# newline-block only. Avoids orphan clause tails like "зависит от проекта."
_MIN_FRAGMENT_SENTENCE = 40

_EMOTIONAL_WORDS_PER_THOUGHT = 5  # target words per chunk in emotional mode


def _by_newlines(text: str) -> list[str]:
    """Split on explicit newlines — LLM line breaks become separate messages."""
    return [p.strip() for p in re.split(r"\n+", text) if p.strip()]


def _emotional_split(text: str, max_length: int) -> list[str]:
    """Split by thought rhythm rather than sentence boundaries.

    Splits on commas, dashes, ellipsis, and long word runs. Keeps fragments
    short so each message feels like an unfinished thought.
    """
    parts = [p.strip() for p in _EMOTIONAL_BREAK.split(text) if p.strip()]

    result: list[str] = []
    for part in parts:
        words = part.split()
        if len(words) <= _EMOTIONAL_WORDS_PER_THOUGHT or len(part) <= max_length:
            result.append(part)
        else:
            mid = len(words) // 2
            result.append(" ".join(words[:mid]))
            result.append(" ".join(words[mid:]))

    return result or [text]


def _sentence_split_line(line: str, clause_threshold: int) -> list[str]:
    """Split one newline-block into sentence-level chunks, with merge within the block."""
    # 1. Split on sentence boundaries
    parts = [c.strip() for c in _SENTENCE_END.split(line) if c.strip()]

    # 2. Clause-split only very long sentences
    refined: list[str] = []
    for chunk in parts:
        if len(chunk) > clause_threshold:
            sub = [c.strip() for c in _CLAUSE_BREAK.split(chunk) if c.strip()]
            refined.extend(sub)
        else:
            refined.append(chunk)

    # 3. Strip trailing commas/semicolons left by clause splits
    refined = [c.rstrip(",;") for c in refined if c.rstrip(",;")]

    # 4. Merge short fragments — only within this newline-block, not across \n boundaries
    merged: list[str] = []
    for chunk in refined:
        if merged and len(chunk) < _MIN_FRAGMENT_SENTENCE:
            merged[-1] = merged[-1] + " " + chunk
        else:
            merged.append(chunk)

    return merged or [line]


class MessageSplitter:
    """Split LLM text into human-sized message chunks."""

    def __init__(
        self,
        max_chunk_length: int = 120,
        split_mode: Literal["sentence", "emotional"] = "sentence",
        max_messages: int = 0,
    ) -> None:
        self._max_chunk = max_chunk_length
        self._emotional = split_mode == "emotional"
        self._max_messages = max_messages

    def split(self, text: str, state: PersonaState) -> list[str]:
        # 0. Explicit newlines always become separate messages in both modes.
        lines = _by_newlines(text)

        if self._emotional:
            # Emotional mode: keep short fragments, no merging — that's the point
            chunks: list[str] = []
            for line in lines:
                chunks.extend(_emotional_split(line, self._max_chunk))
        else:
            clause_threshold = int(self._max_chunk * _CLAUSE_SPLIT_MULTIPLIER)
            chunks = []
            for line in lines:
                # Merge runs within each line, but never across \n boundaries
                chunks.extend(_sentence_split_line(line, clause_threshold))

        # Respect per-state chunk limit (BUSY/DROWSY: 1–2 msgs)
        max_chunks = STATE_PARAMS[state].max_chunks
        if max_chunks and len(chunks) > max_chunks:
            chunks = chunks[: max_chunks - 1] + [" ".join(chunks[max_chunks - 1 :])]

        # Respect persona-level max_messages cap
        if self._max_messages and len(chunks) > self._max_messages:
            chunks = chunks[: self._max_messages - 1] + [
                " ".join(chunks[self._max_messages - 1 :])
            ]

        return chunks or [text]
