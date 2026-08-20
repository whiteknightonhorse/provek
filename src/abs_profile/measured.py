"""LAW-NOT-MEASURED - "not measured" is a STATE OF ITS OWN, never a zero (ABI-13-6, ABI-16-11, ABI-33-4).

This is the most frequent defect class in the operator's production systems - seven instances.
A twelve-week source outage hid in exactly this shape: "no news" and "the source is dead"
returned the same value.

Three absences that MUST NOT collapse into a zero:
  NOTHING_QUALIFIED - the check ran, nothing matched;
  CHECK_DID_NOT_RUN - the check never ran;
  UNREADABLE        - the check ran, the source refused to answer.

Consequence for gates (ABI-33-4): a missing measurement is NOT a violation. "The subject failed"
and "we could not measure the subject" demand different responses.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NotMeasured(str, Enum):
    NOTHING_QUALIFIED = "nothing_qualified"
    CHECK_DID_NOT_RUN = "check_did_not_run"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class Measurement:
    """A value OR the reason it is absent. Never both, never neither."""
    value: float | int | None = None
    absent: NotMeasured | None = None

    def __post_init__(self) -> None:
        if (self.value is None) == (self.absent is None):
            raise ValueError(
                "Measurement must carry EXACTLY ONE of: a value, or the reason it is absent. "
                "Empty and doubled are equally forbidden - that is the 'one return value, two "
                "states of the world' defect this class exists to prevent")

    @property
    def is_measured(self) -> bool:
        return self.value is not None

    def gate_verdict(self, floor: float) -> str:
        """PASS / FAIL / NOT_MEASURED. An absent measurement is NEVER treated as a failure."""
        if not self.is_measured:
            return "NOT_MEASURED"
        return "PASS" if self.value >= floor else "FAIL"
