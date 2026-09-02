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

from src.abs_profile.identity import Binding
from src.abs_profile.measured import Measurement, NotMeasured
from src.registry.lifecycle import Status
from src.verify.control_map import ControlMap
from src.verify.scorer import OperationScore

SCHEMA_VERSION = "2.0.0"

PROTOCOL_VERSION = "1.0.0"
PROFILE_VERSION = "1.1.0"
"""LAW #ONE-PLACE (Fable, 2026-09-01). Until this fix the profile version was THREE literals with
THREE different values: `"1.0.0"` in `src/pipeline.py`, `"1.1.0"` in `scripts/cohort.py`'s
`Provenance(...)` call, and `"1.0.0"` again in `scripts/measure_qm2.py` - one fact about which
methodology read a passport, disagreeing with itself depending on which emitter you asked.

`1.1.0` is canonical because it is what is actually published: the time-windowed (not count-
windowed) evidence read and the platform-closure rule for author counts, both ratified 2026-08-25.
Every emitter constructs its `Provenance` from these two names, never from its own string, so the
three copies cannot drift again - enforced by an AST test (`tests/test_profile_version_one_place.py`)
that fails if a second literal profile-version string reappears at a `Provenance(...)` call site.

A corrected PROFILE_VERSION does not retroactively change a passport already issued (module
docstring, requirement 3): `Provenance` is stamped onto each passport at issue time and travels
with it, so historical passports keep reading whichever version actually measured them.
"""

# Status is imported, not redefined. Until 2026-08-20 this module declared its OWN `Status` enum
# with identical members - so `passport.Status.VERIFIED is lifecycle.Status.VERIFIED` was FALSE
# while `==` was true, because both subclass `str`. Every comparison across the boundary between
# the passport and the registry was therefore correct by accident and would have stopped being so
# the moment either enum gained a member the other lacked. One rule written in two places survives
# its own repeal; this one had not been repealed yet, which is the only reason it had not bitten.




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
    confidence: str | None = None
    """WHICH REGISTER a measured value belongs to (Fable, V4).

    The master specification's `OperationScore` carries three registers - measured, inferred,
    assumed - and every downstream paraphrase in this project narrowed it to two. `assumed` is not
    an empty slot: it is the register for a value taken from the SUBJECT'S OWN DECLARATION,
    participating in the record without independent verification and without contradiction.

    Accountability is exactly that population. Who answers a claim, whether insurance exists, where
    a dispute goes - none of it is observable from outside; §2.6 makes them self-declared by
    construction. Publishing them as `measured` would say we checked, and we did not. If a future
    pipeline ever verifies one against observed behaviour, that entry graduates.

    None when nothing was measured: a register is a property of a value, and there is no value."""

    def __post_init__(self) -> None:
        if self.measured == (self.reason is not None):
            raise ValueError(
                "A Fact carries EXACTLY ONE of: a completed measurement, or the reason none was "
                "taken. Both and neither are the same defect wearing different clothes")
        if self.value is not None and not self.measured:
            raise ValueError("A value that nobody measured is not a fact about the subject")
        if self.measured and self.confidence not in ("measured", "inferred", "assumed"):
            raise ValueError(
                "A measured accountability field must name its register: measured, inferred or "
                "assumed. Omitting it publishes a self-declaration with the authority of a check")
        if not self.measured and self.confidence is not None:
            raise ValueError("A register is a property of a value, and there is no value here")
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
    def none_found(confidence: str = "assumed") -> "Fact":
        """The check RAN and established that there is none. The honest `none`, now earned."""
        return Fact(value=None, measured=True, reason=None, confidence=confidence)

    @staticmethod
    def of(value: object, confidence: str = "assumed") -> "Fact":
        """`assumed` by default because this block is self-declared by construction (§2.6).

        A caller that genuinely verified something against observed behaviour passes "measured"
        deliberately. Making the weaker register the default means the cheapest call makes the
        weakest claim - the rule D-13 was written for."""
        if value is None:
            raise ValueError("Use Fact.none_found() to state a measured absence")
        return Fact(value=value, measured=True, reason=None, confidence=confidence)

    def to_machine(self) -> dict:
        return {"value": self.value, "measured": self.measured,
                "reason": self.reason.value if self.reason else None,
                "confidence": self.confidence}


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
class Service:
    """Phase 2 - the subject's OWN order-intake channel (spec 4.2-bis point 1), ratified design.

    SAME GUARANTEE AS `Accountability`, by the same construction: entirely self-declared, every
    field carries `confidence="assumed"` and NEVER `"measured"`, and this block sits OUTSIDE
    `operations` and the projection - it cannot raise a ladder level and does not enter the score
    (Fable's ruling on phase 2: reachability and declaration never move the score or the
    projection, on pain of reopening the exact overstatement `Accountability` was built to close).

    `order_url` is the only field a subject is required to declare for this block to exist at all;
    `offering`, `pricing_url` and `terms_url` are optional. All four default to `not_checked`
    for a subject this collector never asked (no GitHub remote, or a declaration that could not be
    read at all) - the same "weakest claim by default" rule `Accountability` documents.
    """
    order_url: Fact = field(default_factory=Fact)
    offering: Fact = field(default_factory=Fact)
    pricing_url: Fact = field(default_factory=Fact)
    terms_url: Fact = field(default_factory=Fact)

    def to_machine(self) -> dict:
        return {k: getattr(self, k).to_machine()
                for k in ("order_url", "offering", "pricing_url", "terms_url")}


@dataclass(frozen=True)
class ServiceEndpoint:
    """Phase 2 - PLATFORM_OBSERVED reachability of the declared `order_url` (spec 4.2-bis point 2).

    NOT a fourth Fact wrapped the same way as `Service`'s fields: `declared` is a plain bool because
    it answers "did this collector even attempt the read", which stays `False` for a subject with no
    declared `order_url` at all, and `checked_at` is a plain timestamp rather than a value carried
    inside `reachable` because a timestamp is a property of the ATTEMPT, not of what the attempt
    found. `reachable` reuses `Fact` for exactly the same four-world discipline `Accountability` and
    `Service` already carry: `not_checked` (no attempt), `Fact.of(True/False, confidence="measured")`
    (the GET ran and returned an answer - "measured" because this collector performed the
    observation itself, unlike every self-declared field above), or `Fact.unreadable()` (the attempt
    itself failed for a reason other than a plain non-2xx or refused connection).

    OUTSIDE THE SCORE, same guarantee as `Service` and `Accountability` - see both docstrings.
    """
    declared: bool = False
    reachable: Fact = field(default_factory=lambda: Fact(measured=False,
                                                          reason=NotMeasured.NOT_DECLARED))
    checked_at: str | None = None

    def to_machine(self) -> dict:
        d = self.reachable.to_machine()
        d["declared"] = self.declared
        d["checked_at"] = self.checked_at
        return d


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
    service: Service = field(default_factory=Service)
    """Self-declared order-intake channel (spec 4.2-bis). OUTSIDE `verified`, exactly like
    `accountability` - see `Service`'s own docstring for why it cannot move the score."""
    service_endpoint: ServiceEndpoint = field(default_factory=ServiceEndpoint)
    """PLATFORM_OBSERVED reachability of `service.order_url` (spec 4.2-bis point 2). Also OUTSIDE
    `verified` - see `ServiceEndpoint`'s own docstring."""
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
            "service": self.service.to_machine(),
            "service_endpoint": self.service_endpoint.to_machine(),
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
    # THREE OUTCOMES, and the middle one is the subtle one.
    #
    # Nothing measured at all -> UNVERIFIED. Not "in progress": for a subject whose source refused
    # to answer, nothing is running and nothing will run until the subject changes something. Saying
    # "verification in progress" would promise activity that does not exist, which is a false claim
    # about US rather than about them - and the least excusable kind.
    #
    # Something measured but the map cannot carry it -> IN_PROGRESS. There the word is true: we hold
    # partial evidence and the missing piece is ours to obtain.
    if not projection_value.is_measured:
        return Status.UNVERIFIED
    if not control_map_valid:
        return Status.IN_PROGRESS
    return Status.VERIFIED


def build(binding: Binding, scores: list[OperationScore], control_map: ControlMap,
          projection_value: Measurement, provenance: Provenance,
          accountability: Accountability, *, now: datetime | None = None,
          validity_days: int = 30, claims: dict | None = None,
          observations: dict | None = None,
          mandate_ref: str | None = None,
          verifier_affiliation: str = "independent",
          access_channel: str = "anonymous",
          service: Service | None = None,
          service_endpoint: ServiceEndpoint | None = None) -> Passport:
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
        # THE MEASURED QUANTITIES A LEVEL WAS BUILT FROM. Without these the passport publishes a
        # conclusion and its caveats but not its inputs, so "publishes the evidence behind every
        # number" was a sentence the artefact did not support.
        "observations": observations or {},
        "control_map_valid": ok,
        "control_map_cap": control_map.implied_level_cap() if ok else None,
        # AN INVALID MAP IS NOT AN EMPTY ONE. This used to blank `out_of_reach` and `unknown_shape`
        # whenever the map could not support a verdict - suppressing the reasons a source was
        # unreachable at exactly the moment they are the only thing worth reading. Invalidity means
        # "this map cannot carry a level", not "we know nothing"; the reasons stay true either way,
        # and hiding them turns an honest limitation into an empty block.
        # THREE STATES, not two. A map may carry coverage that lists nothing inspected - we looked
        # and reached nothing - or carry no coverage object at all, which means the map was never
        # given one. Those are different facts and the artefact says which, because collapsing them
        # is the founding defect at yet another altitude.
        "coverage": ({
            "inspected": [s.value for s in control_map.coverage.inspected],
            "out_of_reach": control_map.coverage.out_of_reach,
            "unknown_shape": control_map.coverage.unknown_shape,
            "valid": ok,
        } if control_map.coverage is not None else {
            "inspected": [],
            "out_of_reach": {},
            "unknown_shape": "",
            "valid": False,
            "absent_reason": "check_did_not_run",
        }),
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
        service=service if service is not None else Service(),
        service_endpoint=service_endpoint if service_endpoint is not None else ServiceEndpoint(),
        access_channel=access_channel,
        mandate_ref=mandate_ref,
        verifier_affiliation=verifier_affiliation,
    )
