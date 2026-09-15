from dataclasses import dataclass
from .settings import PLC_MODE, PLC_WRITE_ENABLED


@dataclass(slots=True)
class StopResult:
    accepted: bool
    executed: bool
    mode: str
    detail: str


def request_controlled_stop(conveyor_id: str, reason: str, armed: bool) -> StopResult:
    if not armed:
        return StopResult(False, False, PLC_MODE, "Request rejected: caller did not arm the stop request")

    if not PLC_WRITE_ENABLED:
        return StopResult(
            True,
            False,
            PLC_MODE,
            f"SIMULATED controlled stop for {conveyor_id}: {reason}. PLC writes are disabled.",
        )

    # Real PLC writes are intentionally not implemented in v0.1.
    # A production adapter must enforce PLC permissives, interlocks, acknowledgements,
    # connection health, write verification and site-specific safety review.
    return StopResult(
        False,
        False,
        PLC_MODE,
        "PLC_WRITE_ENABLED is true but no production PLC adapter is installed; fail-safe refusal.",
    )
