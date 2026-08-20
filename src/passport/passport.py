"""T-2.7 - AI Business Passport (ABI-14-1..14-3, spec 2.6, 6.1, 6.4).

THREE REQUIREMENTS, each easy to violate invisibly:

1. **`verified` and `self_reported` are SEPARATE BRANCHES OF A TREE, not two fields of one object**
   (ABI-14-2). The distinction must survive copying and quotation: copy any subtree and the reader
   still sees which branch it came from. Two adjacent fields do not give that - copy a fragment
   and its provenance is gone.

2. **The accountability block is NOT part of the score and does not affect it** (spec 2.6, debt 3).
   The operator rejected a second axis on the ladder, so "who answers and who can stop it" is
   handled by a separate block. The symmetry to preserve: an empty control map yields maximum
   autonomy AND an honest `claims_addressee: none` - the buyer sees both truths side by side.

3. **Provenance is mandatory** (ABI-4-7, ABI-13-5): protocol version, profile version, evidence
   window. A verdict without its protocol version cannot be interpreted a year later. Historical
   passports are NEVER silently recomputed under a new methodology.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

from src.abs_profile.identity import Binding
from src.abs_profile.measured import Measurement, NotMeasured
from src.verify.control_map import ControlMap
from src.verify.scorer import OperationScore

SCHEMA_VERSION = "2.0.0"


class Status(str, Enum):
    UNVERIFIED = "unverified"
    IN_PROGRESS = "verification_in_progress"
    VERIFIED = "verified"
    STALE = "stale"
    SUSPENDED = "suspended"
    FAILED = "failed_or_rejected"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True)
class Fact:
    """One accountability field: a value, or the reason it was never established.

    SCHEMA 2.0.0 (Fable ruling, 2026-08-20). Version 1.0.0 declared these fields `T | None` and
    documented the null as "there is no addressee, and that is an HONEST answer". Every emitter
    then constructed the block from defaults without inspecting anything, so the artefact SAID
    "we checked and found none" while MEANING "nobody looked". That is not an ambiguity, it is a
    false claim, shipped by the product whose thesis is that undistinguished absence is the defect
    worth paying to detect.

    The wrapper is per field rather than a sibling coverage list because the distinction must
    survive quotation (requirement 1 above): copy this field out of the document and it still
    carries whether anyone looked. A coverage list two keys away does not travel with the quote.

    THE DEFAULT IS THE WEAKEST CLAIM. The least-effort construction must assert the least. A
    default that emits "we checked and found none" is a loaded gun in every future emitter - it is
    exactly how 1.0.0 shipped three false blocks without a single author intending one.
    """
    value: object | None = None
    measured: bool = False
    reason: NotMeasured | None = NotMeasured.CHECK_DID_NOT_RUN

    def __post_init__(self) -> None:
        if self.measured == (self.reason is not None):
            raise ValueError(
                "A Fact carries EXACTLY ONE of: a completed measurement, or the reason none was "
                "taken. Both and neither are the same defect wearing different clothes")
        if self.value is not None and not self.measured:
            raise ValueError("A value that nobody measured is not a fact about the subject")
        if self.reason is NotMeasured.NOTHING_QUALIFIED:
            # Fable barred this reason for presence fields and asked for a test. The guard is here
            # as well, because the invariant that slipped in 1.0.0 was the one no machine proved:
            # for a presence question "the check ran and nothing qualified" IS the measurement
            # `measured=True, value=None`, so admitting it as an ABSENCE reason would rebuild the
            # two-encodings-of-one-world defect this schema exists to remove. Raised for his
            # review as a strengthening of the ruling, not a departure from it.
            raise ValueError(
                "nothing_qualified is not an absence reason for a presence field: a completed "
                "check that found nothing is measured=True with value=None")

    @staticmethod
    def not_checked() -> "Fact":
        return Fact()

    @staticmethod
    def unreadable() -> "Fact":
        return Fact(measured=False, reason=NotMeasured.UNREADABLE)

    @staticmethod
    def none_found() -> "Fact":
        """The check RAN and established that there is none. The honest `none`, now earned."""
        return Fact(value=None, measured=True, reason=None)

    @staticmethod
    def of(value: object) -> "Fact":
        if value is None:
            raise ValueError("Use Fact.none_found() to state a measured absence")
        return Fact(value=value, measured=True, reason=None)

    def to_machine(self) -> dict:
        return {"value": self.value, "measured": self.measured,
                "reason": self.reason.value if self.reason else None}


@dataclass(frozen=True)
class Accountability:
    """Does NOT affect the score. Answers a question the ladder does not ask.

    Every field defaults to `not_checked`: outside the score is not outside measurement discipline.
    In 1.0.0 the exemption from scoring silently became an exemption from the law, because the only
    path through the law ran through the scorer.
    """
    emergency_stop: Fact = field(default_factory=Fact)
    claims_addressee: Fact = field(default_factory=Fact)
    insurance: Fact = field(default_factory=Fact)
    dispute_path: Fact = field(default_factory=Fact)

    def to_machine(self) -> dict:
        return {k: getattr(self, k).to_machine()
                for k in ("emergency_stop", "claims_addressee", "insurance", "dispute_path")}


@dataclass(frozen=True)
class Provenance:
    protocol_version: str
    profile_version: str
    evidence_window_days: int


@dataclass(frozen=True)
class Passport:
    subject_binding: Binding
    issued_at: datetime
    valid_until: datetime
    status: Status
    provenance: Provenance
    verified: dict = field(default_factory=dict)        # the MEASURED branch
    self_reported: dict = field(default_factory=dict)   # the SUBJECT-CLAIMED branch
    accountability: Accountability = field(default_factory=Accountability)
    access_channel: str = "anonymous"
    """WHICH CHANNEL the evidence came through, published rather than assumed (Fable, NEW-3).

    `optional_token()` already claimed in its docstring that the passport records this. It did not.
    A claim about an artefact that the artefact does not carry is the defect class this product
    exists to detect, so the fix is to emit it rather than to withdraw the sentence.

    "Reproducible by anyone" and "reproducible by someone holding a credential" are different
    offers, and a reader is not asked to guess which one they have been given.
    """
    mandate_ref: str | None = None                      # None = no active probing was performed
    verifier_affiliation: str = "independent"
    """MANDATORY DISCLOSURE (Fable ruling, 2026-08-19).

    Value `same_owner` means the subject and the verifier's owner are the same person. Without
    this field the first registry entries - the operator's own systems - would read as INDEPENDENT
    verifications, which is a quiet conflict of interest displayed on the shop window (the spirit
    of ABI-29-4). With it, they are an honest rehearsal of the protocol.
    """

    def effective_status(self, now: datetime) -> Status:
        """Status BY TIME: verified lapses to stale on its own, with no event (ABI-15-5).

        A fact needs a place to expire. A fact with no expiry cannot go stale - it can only
        become wrong.
        """
        if self.status is Status.VERIFIED and now >= self.valid_until:
            return Status.STALE
        return self.status

    def to_machine(self) -> dict:
        """Machine representation. The branches are NOT merged - their separation is load-bearing."""
        return {
            "schema_version": SCHEMA_VERSION,
            "subject_id": self.subject_binding.as_subject_id(),
            "binding_strength": self.subject_binding.strength.value,
            "binding_flags": self.subject_binding.flags,
            "issued_at": self.issued_at.isoformat(),
            "valid_until": self.valid_until.isoformat(),
            "status": self.status.value,
            "provenance": asdict(self.provenance),
            "verified": self.verified,
            "self_reported": self.self_reported,
            "accountability": self.accountability.to_machine(),
            "mandate_ref": self.mandate_ref,
            "verifier_affiliation": self.verifier_affiliation,
            "access_channel": self.access_channel,
            "disclaimer": ("The score measures AUTONOMY. It does not measure reliability, "
                           "decision quality, profitability, or the presence of an accountable "
                           "party - see accountability."),
        }


def _status(control_map_valid: bool, projection_value: Measurement) -> Status:
    """A passport that measured nothing is NOT verified (Fable, NEW-1).

    The registry row learned this and the passport did not, so one subject had two published
    artefacts contradicting each other about its own status - `unverified` in the registry,
    `verified` in the document the registry links to. That is R2's shape, in the commit that
    closed R2, and the emitted-artefact gate missed it because the gate only read rows.

    One rule, one place, both artefacts derived from it.
    """
    if not control_map_valid:
        return Status.IN_PROGRESS
    return Status.VERIFIED if projection_value.is_measured else Status.UNVERIFIED


def build(binding: Binding, scores: list[OperationScore], control_map: ControlMap,
          projection_value: Measurement, provenance: Provenance,
          accountability: Accountability, *, now: datetime | None = None,
          validity_days: int = 30, claims: dict | None = None,
          mandate_ref: str | None = None,
          verifier_affiliation: str = "independent",
          access_channel: str = "anonymous") -> Passport:
    """Assemble a passport. An invalid control map CANNOT yield `verified`.

    A map without coverage claims more than it knows (ABI-7-5), and a passport cannot stand on it.
    """
    now = now or datetime.now(timezone.utc)
    ok = control_map.is_valid()
    verified = {
        # Confidence and limiters were computed by the scorer, armed by LAW-WEAK-SIGNAL-LIMITERS,
        # and then DROPPED here (Fable, R3). Every level in the registry is O1-limited `inferred`,
        # and the surface rendered each one indistinguishably from a measured L4 - the published
        # number was stronger than the measured one, which is the overstatement this product
        # exists to prevent. Same shape as D-13: a value protected inside a class, lost at the
        # boundary, with no gate on the emitted document.
        "operations": [{"operation": s.operation,
                        "level": (s.level.name if s.is_measured else s.level.value),
                        "measured": s.is_measured,
                        "confidence": (s.confidence.value if s.is_measured else None),
                        "limiters_applied": list(s.limiters_applied)} for s in scores],
        "projection": projection_value.value if projection_value.is_measured else None,
        "projection_absent_reason": (None if projection_value.is_measured
                                     else projection_value.absent.value),
        "control_map_valid": ok,
        "control_map_cap": control_map.implied_level_cap() if ok else None,
        "coverage": {
            "inspected": [s.value for s in control_map.coverage.inspected] if ok else [],
            "out_of_reach": control_map.coverage.out_of_reach if ok else {},
            "unknown_shape": control_map.coverage.unknown_shape if ok else "",
        },
    }
    # KEYWORDS, not positions. Inserting `access_channel` above shifted every argument after it,
    # so the field silently took `mandate_ref`'s value and published a null where a channel name
    # belongs. The bare-null gate caught it, which is the whole reason that gate reads the emitted
    # document; a positional constructor with ten arguments is a defect waiting for its next field.
    return Passport(
        subject_binding=binding,
        issued_at=now,
        valid_until=now + timedelta(days=validity_days),
        status=_status(ok, projection_value),
        provenance=provenance,
        verified=verified,
        self_reported=dict(claims or {}),
        accountability=accountability,
        access_channel=access_channel,
        mandate_ref=mandate_ref,
        verifier_affiliation=verifier_affiliation,
    )
