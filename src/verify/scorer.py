"""T-2.6 - score computation (ABI-13-1..13-6).

THREE INVARIANTS, each paid for by someone's mistake:

1. **The verdict is computed by DETERMINISTIC code.** An LLM may gather and reason, but PASS/FAIL
   and the number are taken by code from a measured quantity. A failed LLM is a red result, never
   a skip.
2. **The score is a VECTOR over operations, not a scalar per company** (ABI-2-3).
3. **`not_measured` is not a zero** (ABI-13-6).

This module deliberately knows nothing about transport - enforced by an AST-based test.

-- WEAK-SIGNAL LIMITERS (Fable ruling, 2026-08-19) ------------------------------------------------
The signal "share of signed commits + number of authors" MIXES evidence classes: "this KEY signed"
is cryptographically bound, but "the key belongs to an agent rather than a human" is the subject's
self-report, and forging it is cheap - the subject owns all of its own keys. So the limiters live
HERE, in code, not in a docstring: a rule written only in a comment is not enforced.

  O1. A mixed signal yields confidence=INFERRED, never MEASURED, and the class mix is disclosed.
  O2. The signal ALONE cannot justify L3 or above: that needs a runtime trace of initiation.
      Without one, the level is capped at L2.
  O3. The signal is stronger at REFUTING than at confirming: a contradiction legitimately lowers
      a claimed level, while agreement only weakly supports it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.abs_profile.evidence import SCORABLE, EvidenceClass
from src.abs_profile.ladder import L
from src.abs_profile.measured import Measurement, NotMeasured


class Confidence(str, Enum):
    """The three registers from brief section 0.2. The third must never wear the first's clothes."""
    MEASURED = "measured"
    INFERRED = "inferred"
    ASSUMED = "assumed"


WEAK_SIGNAL_CEILING = L.L2
"""O2: the ceiling for an operation justified ONLY by a weak mixed signal."""


@dataclass(frozen=True)
class OperationScore:
    operation: str
    level: L | NotMeasured
    evidence_classes: tuple[EvidenceClass, ...]
    confidence: Confidence = Confidence.MEASURED
    limiters_applied: tuple[str, ...] = ()

    @property
    def is_measured(self) -> bool:
        return isinstance(self.level, L)


def score_operation(operation: str,
                    observed_level: L | None,
                    evidence: tuple[EvidenceClass, ...],
                    control_map_cap: int | None = None,
                    *,
                    weak_mixed_signal: bool = False,
                    runtime_trace: bool = False,
                    claimed_level: L | None = None,
                    absent_reason: NotMeasured | None = None) -> OperationScore:
    """Score ONE operation. Absent usable evidence yields not_measured, never L0.

    L0 means "a human does this" - a claim about the world. Absence of data is not that claim, and
    conflating them slanders the subject.

    `absent_reason` (Fable, 2026-09-01) lets a caller that HOLDS a more specific finding than this
    function can see - `NO_EVIDENCE_IN_WINDOW`, `APPARATUS_ABSENT`, or a collector's `UNREADABLE` -
    pass it through instead of being overwritten by this function's generic guess. It is consulted
    only in the one branch below where the scorer cannot tell the reason itself: scorable evidence
    was genuinely offered and the underlying measurement still came back absent. Defaults to the
    prior guess (`NOTHING_QUALIFIED`) so every existing caller that does not pass it is unaffected.
    """
    scorable = tuple(e for e in evidence if e in SCORABLE)
    if observed_level is None or not scorable:
        # THREE absences, and until 2026-08-20 this returned the wrong one (Fable, R1). An empty
        # evidence tuple means the caller attempted nothing - `cohort.py` passes `()` for the two
        # runtime operations - and the code stamped UNREADABLE, which asserts that a source was
        # approached and refused. Every published passport told a machine reader "the source could
        # not be read" about sources nobody had tried to read, while the same passport's page said
        # in prose that runtime evidence is not collected at this stage. Two artefacts, one subject,
        # contradictory claims.
        #
        # UNREADABLE is a fact only a collector can establish, because only a collector talks to a
        # source. The scorer can never produce it, so it no longer does.
        #
        # A THIRD absence within this branch (Fable, 2026-09-01): evidence was offered AND it was
        # scorable, and the level still came back None. That is neither "nobody looked" nor "only
        # an unscorable claim was offered" - it is the collector's own measurement running dry, and
        # only the caller that built that measurement knows why. Guessing NOTHING_QUALIFIED here
        # regardless is exactly how AIpush and mcp-protocol-tester's `development_initiation` -
        # genuinely read, with an empty evidence window - lost its real reason on the way to the
        # registry.
        if not evidence:
            absent = NotMeasured.CHECK_DID_NOT_RUN     # nobody looked
        elif not scorable:
            absent = NotMeasured.NOTHING_QUALIFIED     # only unscorable evidence was ever offered
        else:
            absent = absent_reason or NotMeasured.NOTHING_QUALIFIED
        return OperationScore(operation, absent, evidence, Confidence.MEASURED)

    level = observed_level
    limiters: list[str] = []
    confidence = Confidence.MEASURED

    if weak_mixed_signal:
        confidence = Confidence.INFERRED                       # O1
        limiters.append("O1:mixed_classes->inferred")
        if not runtime_trace and level > WEAK_SIGNAL_CEILING:  # O2
            level = WEAK_SIGNAL_CEILING
            limiters.append("O2:no_runtime_trace->capped_L2")

    if claimed_level is not None and level < claimed_level:     # O3
        limiters.append("O3:contradicts_claim->claim_rejected")

    if control_map_cap is not None and int(level) > control_map_cap:
        level = L(control_map_cap)
        limiters.append("control_map_cap")

    return OperationScore(operation, level, scorable, confidence, tuple(limiters))


def projection(scores: list[OperationScore]) -> Measurement:
    """The 0..100 projection for the Validation Registry - exactly the shape ERC-8004 defines.

    If nothing was measured, the projection is ABSENT. A zero would mean "measured and fully
    non-autonomous" - an entirely different claim about the world.
    """
    measured = [s for s in scores if s.is_measured]
    if not measured:
        # DERIVE the reason, never assume it. This returned NOTHING_QUALIFIED unconditionally -
        # "we looked at what was there and none of it counted" - even when every operation had said
        # the source refused to answer. The aggregate contradicted the rows it aggregates.
        #
        # Precedence when the operations disagree: unreadable beats apparatus-absent beats
        # no-evidence-in-window beats check-did-not-run beats nothing-qualified.
        #
        # A source that refused is the strongest fact available about why no number exists, and it
        # is the one a reader most needs - that ordering is unchanged. The two reasons inserted
        # above `check_did_not_run` (Fable, 2026-09-01) both assert that a check RAN and read the
        # subject; `check_did_not_run` asserts the opposite. Every subject in this registry carries
        # two operations (`deployment`, `treasury_control`) that are ALWAYS check-did-not-run - no
        # collector for either exists yet - so before this fix that boilerplate, scope-wide fact
        # outranked a genuine, subject-specific reading every time the two disagreed: AIpush and
        # mcp-protocol-tester's registry rows said "the check did not run" about a subject whose
        # `development_initiation` check ran and read an empty window. A reading of the subject
        # must outrank a fact about what this codebase has not built yet.
        reasons = {s.level for s in scores if isinstance(s.level, NotMeasured)}
        for candidate in (NotMeasured.UNREADABLE,
                          NotMeasured.APPARATUS_ABSENT,
                          NotMeasured.NO_EVIDENCE_IN_WINDOW,
                          NotMeasured.CHECK_DID_NOT_RUN,
                          NotMeasured.NOTHING_QUALIFIED):
            if candidate in reasons:
                return Measurement(absent=candidate)
        return Measurement(absent=NotMeasured.CHECK_DID_NOT_RUN)
    return Measurement(value=round(sum(int(s.level) for s in measured) / (5 * len(measured)) * 100))
