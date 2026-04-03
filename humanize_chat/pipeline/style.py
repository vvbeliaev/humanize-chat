import random

from ..core.persona import StyleConfig
from ..core.state import STATE_PARAMS, PersonaState

# QWERTY adjacency map — only lowercase keys that have obvious neighbors
_ADJACENT: dict[str, str] = {
    "q": "wa", "w": "qeasd", "e": "wrsd", "r": "etdf", "t": "ryfg",
    "y": "tugh", "u": "yihj", "i": "uojk", "o": "ipkl", "p": "ol",
    "a": "qwsz", "s": "awedxz", "d": "serfxc", "f": "drtgvc",
    "g": "ftyhbv", "h": "gyujnb", "j": "huikmn", "k": "jiiolm",
    "l": "kop", "z": "asx", "x": "zsdc", "c": "xdfv", "v": "cfgb",
    "b": "vghn", "n": "bhjm", "m": "njk",
}


def _mistype(ch: str, rng: random.Random) -> str:
    neighbors = _ADJACENT.get(ch.lower())
    if not neighbors:
        return ch
    replacement = rng.choice(neighbors)
    return replacement.upper() if ch.isupper() else replacement


class StyleTransformer:
    """Apply human-like mutations to a text chunk based on persona state."""

    def __init__(self, config: StyleConfig, seed: int | None = None) -> None:
        self._config = config
        self._rng = random.Random(seed)

    def transform(self, text: str, state: PersonaState) -> str:
        params = STATE_PARAMS[state]
        effective_rate = self._config.typo_rate * params.typo_rate_mul

        # Keyboard typos
        chars = list(text)
        for i, ch in enumerate(chars):
            if ch.isalpha() and self._rng.random() < effective_rate:
                chars[i] = _mistype(ch, self._rng)
        result = "".join(chars)

        # Casually drop trailing period ~40% of the time
        if result.endswith(".") and self._rng.random() < 0.4:
            result = result[:-1]

        return result
