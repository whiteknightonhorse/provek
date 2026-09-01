"""LAW-NOT-MEASURED - "not measured" is a STATE OF ITS OWN, never a zero (ABI-13-6, ABI-16-11, ABI-33-4).

This is the most frequent defect class in the operator's production systems - seven instances.
A twelve-week source outage hid in exactly this shape: "no news" and "the source is dead"
returned the same value.

Five absences that MUST NOT collapse into a zero:
  NOTHING_QUALIFIED    - the check ran, nothing matched;
  CHECK_DID_NOT_RUN    - the check never ran;
  UNREADABLE           - the check ran, the source refused to answer;
  NO_EVIDENCE_IN_WINDOW - the check ran, the apparatus exists, but the evidence window held no
                          evidence of this class (Fable, 2026-09-01);
  APPARATUS_ABSENT     - the check ran and successfully read an empty result: the subject has no
                          apparatus of this platform AT ALL (Fable, 2026-09-01).

THE LAST TWO WERE ADDED BECAUSE THE FIRST THREE WERE MADE TO LIE. The live registry stated
`check_did_not_run` for two subjects (AIpush, mcp-protocol-tester) whose GitHub history WAS read -
the collector ran, answered 200, and paged the full evidence window - and simply found no commits
inside it. `check_did_not_run` asserts nobody looked; that assertion was false, published on the
site whose whole thesis is that undistinguished absence is the defect worth paying to detect.

NO_EVIDENCE_IN_WINDOW is temporal: the apparatus that could carry this evidence exists, and a later
window may not be empty. APPARATUS_ABSENT is structural: the subject was read and shown to have no
such apparatus at all (a repository with zero total workflow runs, ever, from an UNWINDOWED count) -
a permanent fact about the subject, not a gap that time could close. Neither may be confused with
NOTHING_QUALIFIED, which stays reserved for "the check ran across candidates and none qualified" -
a different shape again, and the one Fable already barred from presence fields (see `Fact` in
`src/passport/passport.py`) because for a presence question that shape IS the measurement, not its
absence.

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
    NO_EVIDENCE_IN_WINDOW = "no_evidence_in_window"
    APPARATUS_ABSENT = "apparatus_absent"


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
