from dataclasses import dataclass
from enum import Enum


class PersonaState(Enum):
    ASLEEP = "asleep"
    DROWSY = "drowsy"
    BUSY = "busy"
    AVAILABLE = "available"
    ENGAGED = "engaged"
    DISTRACTED = "distracted"


@dataclass(frozen=True)
class StateParams:
    """Behavior parameters derived from persona state."""

    read_delay_min: float  # seconds (math.inf for ASLEEP)
    read_delay_max: float
    typing_speed_mul: float  # multiplier on base typing speed
    typo_rate_mul: float  # multiplier on base typo rate
    max_chunks: int  # 0 = no limit; otherwise collapse to N chunks


STATE_PARAMS: dict[PersonaState, StateParams] = {
    PersonaState.ASLEEP: StateParams(float("inf"), float("inf"), 1.0, 0.0, 0),
    PersonaState.DROWSY: StateParams(30, 120, 0.6, 2.0, 2),
    PersonaState.BUSY: StateParams(300, 1800, 1.2, 0.5, 2),
    PersonaState.AVAILABLE: StateParams(10, 60, 1.0, 1.0, 0),
    PersonaState.ENGAGED: StateParams(2, 10, 1.2, 0.5, 0),
    PersonaState.DISTRACTED: StateParams(120, 1200, 1.0, 1.5, 1),
}
