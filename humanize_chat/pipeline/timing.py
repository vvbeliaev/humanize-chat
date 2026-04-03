import math
import random

from ..core.persona import TimingConfig
from ..core.state import STATE_PARAMS, PersonaState


class TimingCalculator:
    """Compute typing indicator duration and inter-message pauses."""

    def __init__(self, config: TimingConfig, seed: int | None = None) -> None:
        self._config = config
        self._rng = random.Random(seed)

    def typing_duration(self, text: str, state: PersonaState) -> float:
        """Seconds to show the typing indicator before sending this chunk."""
        params = STATE_PARAMS[state]
        speed = self._config.typing_speed_cps * params.typing_speed_mul
        jitter = 1.0 + self._rng.uniform(
            -self._config.typing_jitter, self._config.typing_jitter
        )
        return max(0.5, len(text) / (speed * jitter))

    def inter_chunk_pause(self, state: PersonaState) -> float:  # noqa: ARG002
        """Short pause between consecutive message chunks."""
        return self._rng.uniform(
            self._config.inter_chunk_pause_min,
            self._config.inter_chunk_pause_max,
        )

    def read_delay(self, state: PersonaState) -> float:
        """Delay before the persona starts responding at all."""
        params = STATE_PARAMS[state]
        if math.isinf(params.read_delay_min):
            return float("inf")
        return self._rng.uniform(params.read_delay_min, params.read_delay_max)
