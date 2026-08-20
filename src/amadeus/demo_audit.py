"""T-2.16 - classify what the Amadeus auditor agent gathered, and take the verdict (ABI-16-11).

WHAT THIS MODULE IS FOR. `demo/amadeus/auditor.mjs` runs a Provek Auditor agent on the Amadeus
Protocol SDK and writes down what it saw. It takes no verdict. This module reads that artefact,
decides what each reading actually IS, and returns a judgement - deterministically, from the
recorded quantities, with no network of its own. That separation is invariant 2, and it is also
what makes the demo testable: every branch below is reachable from an injected artefact, so the
tests never need a socket and never skip (L-16).

THE READING THAT MOTIVATED THE WHOLE SHAPE OF THIS FILE. HTTP 200 is not a measurement. On
2026-08-20, ~23:07Z, three chain endpoints on `mainnet-rpc.ama.one` answered 200 with a CKAN
`package_search` document from `ckan.opendata.swiss`. The record of that reading, and an explicit
list of what it does NOT establish - full bodies and headers were never retained, and where on
the path the substitution happened was never determined - is `evidence/AMADEUS-RPC-ANOMALY-001.txt`.
Read that before repeating the claim anywhere.

The SDK applies no schema to a success body, so such a body reaches the caller as the chain tip
and `entry.header.height` reads `undefined` - which one step later is a zero. That part does not
rest on the incident: it is reproduced on demand by the instrument control in `auditor.mjs`. So
`answered` and `measured` are DIFFERENT STATES here, and the gap between them has a name of its
own - `SHAPE_UNRECOGNISED` - which resolves to `UNREADABLE` and never to a number.

WHY `SHAPE_UNRECOGNISED` AND NOT `FOREIGN_PAYLOAD`. This code can tell that a body is not the
chain's shape. It cannot tell whether that body belongs to somebody else, or is a truncated
answer, or is a version of the API it does not know. Naming the state after the strongest of
those readings would be a claim the instrument cannot support, which is the defect class the
product exists to expose - so the state is named after what was actually observed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.abs_profile.measured import Measurement, NotMeasured

REQUIRED_TOP_LEVEL = (
    "sdk", "network", "readings", "foreign_payload_control", "self_audit", "anchor",
    "payload", "onchain_write",
)
"""Structure the artefact MUST have. A missing key is our defect, not a finding about Amadeus -
the two get different verdicts below, because "the subject failed" and "our instrument is broken"
demand different responses (ABI-33-4)."""

SHAPE: dict[str, tuple[str, ...]] = {
    "chain.getTip": ("entry", "header", "height"),
    "chain.getStats": ("stats", "height"),
    "chain.getKpi": ("kpi", "block_time"),
}
"""The path that must hold an integer for a reading to count as measured. Chosen per endpoint
rather than "the body is a dict": every one of the three foreign 200s WAS a dict."""

ANCHOR_ENDPOINT = "chain.getTip"


class ReadingState(str, Enum):
    MEASURED = "measured"
    SHAPE_UNRECOGNISED = "shape_unrecognised"
    NO_DECLARED_SHAPE = "no_declared_shape"
    SOURCE_DECLINED = "source_declined"
    NO_ANSWER = "no_answer"
    CHECK_DID_NOT_RUN = "check_did_not_run"

    @property
    def is_measured(self) -> bool:
        return self is ReadingState.MEASURED


ABSENCE = {
    ReadingState.SHAPE_UNRECOGNISED: NotMeasured.UNREADABLE,
    ReadingState.NO_DECLARED_SHAPE: NotMeasured.UNREADABLE,
    ReadingState.SOURCE_DECLINED: NotMeasured.UNREADABLE,
    ReadingState.NO_ANSWER: NotMeasured.UNREADABLE,
    ReadingState.CHECK_DID_NOT_RUN: NotMeasured.CHECK_DID_NOT_RUN,
}
"""How a non-measurement maps onto the project's three absences. There is no entry for MEASURED
on purpose: asking this table for the absence of a measured reading is a programming error and
should raise, not return a default."""


class SdkFinding(str, Enum):
    """What the instrument control established about the SDK itself."""
    ACCEPTS_UNVALIDATED = "accepts_unvalidated_response"
    VALIDATES = "validates_response"
    CONTROL_DID_NOT_RUN = "control_did_not_run"


class DemoVerdict(str, Enum):
    DEMONSTRATED = "demonstrated"
    NOT_DEMONSTRATED = "not_demonstrated"
    DEFECT = "defect"


DEFECT_EXIT = 3
"""Distinct from `not_demonstrated`'s 1, and from the runner's 2 for "the demo never started".
Four states of the world, four codes - see `Judgement.exit_code`."""


@dataclass(frozen=True)
class Reading:
    endpoint: str
    state: ReadingState
    value: Measurement
    detail: str


@dataclass(frozen=True)
class Judgement:
    verdict: DemoVerdict
    readings: tuple[Reading, ...]
    sdk_finding: SdkFinding
    findings: tuple[str, ...]
    anchor_height: Measurement

    @property
    def exit_code(self) -> int:
        """0 ONLY for a demonstrated run, and DEFECT gets a code of its own.

        `not_demonstrated` is not a pass with an excuse: the demo exists to be shown to somebody,
        and a run that showed nothing must not be reported by a green code a script would trust.

        THE THIRD CODE WAS MISSING AND THE DOCUMENTS PROMISED IT. Both failing verdicts returned
        1 while the README and `judge()` both said in as many words that "their RPC was down" and
        "we shipped a broken demo" must not share an exit code - a rule contradicted two screens
        from where it was written, and blessed by two tests that asserted the wrong number. That
        is the same defect as a header outliving its list. Found by Fable.
        """
        if self.verdict is DemoVerdict.DEMONSTRATED:
            return 0
        return DEFECT_EXIT if self.verdict is DemoVerdict.DEFECT else 1


def _dig(body: object, path: tuple[str, ...]) -> object:
    for key in path:
        if not isinstance(body, dict) or key not in body:
            return None
        body = body[key]
    return body


def _absent(endpoint: str, state: ReadingState, detail: str) -> Reading:
    """Build a non-measurement, taking the absence FROM the `ABSENCE` table.

    The table used to be a decorative restatement: every branch below hardcoded its own
    `Measurement(absent=...)` and nothing read `ABSENCE` at all, so the two could drift with no
    test noticing - the same rule in two places, one of them unenforced (L-2), inside the module
    whose subject is that absences keep their names. Routing every absence through here makes the
    table the single definition it always claimed to be. Found by Fable.
    """
    return Reading(endpoint, state, Measurement(absent=ABSENCE[state]), detail)


def classify_reading(reading: dict) -> Reading:
    """One reading -> its state and its value. Never raises on a malformed reading: an artefact
    this code cannot parse is itself a fact the judgement has to carry."""
    raw_endpoint = reading.get("endpoint")
    # A READING WITH NO ENDPOINT IS A MALFORMED ARTEFACT, NOT A SHAPE WE HAPPEN TO LACK. Checked
    # before the transport, because `str(None)` is the string "None", which would sail past every
    # branch below and be reported as "answered, but no shape is declared for 'None'" - our
    # broken artefact wearing the description of somebody else's unfamiliar endpoint. That
    # regression was introduced by the fix that added NO_DECLARED_SHAPE.
    if not isinstance(raw_endpoint, str):
        return _absent("<no endpoint>", ReadingState.CHECK_DID_NOT_RUN,
                       f"the reading carries no endpoint name ({raw_endpoint!r}), so there is no "
                       "reading here to classify")
    endpoint = raw_endpoint

    transport = reading.get("transport")
    if transport == "no_answer":
        return _absent(endpoint, ReadingState.NO_ANSWER,
                       f"the request did not complete: {reading.get('error')}")
    if transport == "source_declined":
        return _absent(endpoint, ReadingState.SOURCE_DECLINED,
                       f"the source answered HTTP {reading.get('http_status')} and declined")
    if transport != "answered":
        return _absent(endpoint, ReadingState.CHECK_DID_NOT_RUN,
                       f"no recognised transport outcome ({transport!r})")

    # THE REQUEST RAN AND WAS ANSWERED; IT IS THIS CLASSIFIER THAT HAS NO SHAPE FOR IT. Filing
    # that as `check_did_not_run` would merge "never ran" with "ran, and we cannot read it" -
    # the collapse invariant 1 exists to prevent, committed inside the module enforcing it.
    # Found by Fable.
    if endpoint not in SHAPE:
        return _absent(endpoint, ReadingState.NO_DECLARED_SHAPE,
                       f"answered, but this classifier declares no shape for {endpoint!r}, so "
                       "nothing can be read out of the body")

    found = _dig(reading.get("body"), SHAPE[endpoint])
    # `bool` is an `int` in Python and `True` would sail through an isinstance check. A height of
    # True is not a height, and the whole point of this function is that near-misses do not pass.
    if isinstance(found, bool) or not isinstance(found, int):
        return _absent(
            endpoint, ReadingState.SHAPE_UNRECOGNISED,
            f"answered, but {'.'.join(SHAPE[endpoint])} is {type(found).__name__}, not an "
            f"integer - a 200 whose body is not this chain's shape is UNREADABLE, not a zero")
    return Reading(endpoint, ReadingState.MEASURED, Measurement(value=found),
                   f"{'.'.join(SHAPE[endpoint])} = {found}")


def classify_control(control: dict) -> tuple[SdkFinding, str]:
    """The instrument control: was the SDK handed a 200 that was not chain state, and did it
    notice? Returns the finding and the sentence that goes in the artefact."""
    if not isinstance(control, dict) or not control.get("performed"):
        return (SdkFinding.CONTROL_DID_NOT_RUN,
                "the control could not be set up, so nothing was established about the SDK's "
                "handling of an unexpected 200 - this is OUR gap, not a result")
    threw = control.get("sdk_threw")
    if threw is True:
        return (SdkFinding.VALIDATES,
                "the SDK rejected a 200 whose body was not chain state - the finding this demo "
                "was built to show no longer holds for this version")
    if threw is False:
        # EVERY WORD OF "IN THE INSTRUMENT CONTROL" IS LOad-BEARING. This sentence is copied into
        # `evidence/AMADEUS-DEMO-001.txt`, and its first draft said only "the SDK returned a 200
        # whose body was another portal's document as the chain tip" - which an Amadeus engineer
        # reading the artefact would take as a statement about their live RPC during THIS run,
        # in a file whose three readings are all `measured`. A true sentence about a local socket,
        # phrased so it reads as an outage, is still an overclaim. Found by Fable.
        return (SdkFinding.ACCEPTS_UNVALIDATED,
                "in the instrument control (a local socket serving a reconstructed CKAN envelope) "
                "the SDK accepted a 200 whose body was not chain state and returned it as the "
                "chain tip; the height a caller would read is `undefined` in JavaScript, recorded "
                f"here as {control.get('height_seen')!r}")
    return (SdkFinding.CONTROL_DID_NOT_RUN,
            f"the control reported neither outcome (sdk_threw={threw!r})")


def judge(artefact: dict) -> Judgement:
    """The verdict, from the recorded quantities only.

    THREE OUTCOMES, AND THE DISTINCTION BETWEEN THE LAST TWO IS THE POINT. `DEFECT` means the
    artefact is not what this repository promised to produce - our bug, and a red build.
    `NOT_DEMONSTRATED` means the run was honest and showed nothing, which is what an unreachable
    chain looks like and is not a failure of the subject either. They carry DIFFERENT exit codes
    (`Judgement.exit_code`), because collapsing them would put "their RPC was down" and "we
    shipped a broken demo" behind one number.
    """
    findings: list[str] = []

    missing = [k for k in REQUIRED_TOP_LEVEL if k not in artefact]
    if missing:
        return Judgement(DemoVerdict.DEFECT, (), SdkFinding.CONTROL_DID_NOT_RUN,
                         (f"the artefact is missing {', '.join(missing)} - it was not produced by "
                          "the auditor this classifier is paired with",),
                         Measurement(absent=NotMeasured.CHECK_DID_NOT_RUN))

    raw = artefact["readings"]
    readings = tuple(classify_reading(r) for r in raw) if isinstance(raw, list) else ()
    if not readings:
        findings.append("no readings were recorded at all")

    sdk_finding, control_sentence = classify_control(artefact["foreign_payload_control"])
    findings.append(control_sentence)

    tip = next((r for r in readings if r.endpoint == ANCHOR_ENDPOINT), None)
    anchor_height = tip.value if tip else Measurement(absent=NotMeasured.CHECK_DID_NOT_RUN)

    # THE CROSS-CHECK THAT GUARDS THE LANGUAGE BOUNDARY. The agent builds its own anchor from the
    # same tip; if its answer and this one disagree, one of the two invented a height, and which
    # one hardly matters - a demo that anchors an audit at a block nobody measured is worse than
    # one that anchors at nothing. Cheap to state, and it is the only thing standing between the
    # payload and a number with no provenance.
    claimed = artefact["anchor"] if isinstance(artefact["anchor"], dict) else {}
    if bool(claimed.get("present")) != anchor_height.is_measured:
        findings.append(
            f"the agent and the classifier disagree about the anchor: the agent says "
            f"present={claimed.get('present')!r}, the tip reading says "
            f"measured={anchor_height.is_measured}")
        return Judgement(DemoVerdict.DEFECT, readings, sdk_finding, tuple(findings), anchor_height)
    if anchor_height.is_measured and claimed.get("height") != anchor_height.value:
        findings.append(
            f"the agent anchored at height {claimed.get('height')!r} and the tip reading carries "
            f"{anchor_height.value!r}")
        return Judgement(DemoVerdict.DEFECT, readings, sdk_finding, tuple(findings), anchor_height)

    write = artefact["onchain_write"] if isinstance(artefact["onchain_write"], dict) else {}
    if write.get("attempted") is not False or not write.get("blockers"):
        findings.append(
            "the on-chain write is not recorded as a blocked step with named blockers - a step "
            "that leaves no sentinel is how 'cannot' becomes 'forgot'")
        return Judgement(DemoVerdict.DEFECT, readings, sdk_finding, tuple(findings), anchor_height)

    # From here the artefact is well formed, so anything below is a statement about the run.
    verdict = DemoVerdict.DEMONSTRATED

    if not any(r.state.is_measured for r in readings):
        findings.append(
            "not one reading was measured, so the SDK was never shown talking to the chain and "
            "the demo demonstrates nothing")
        verdict = DemoVerdict.NOT_DEMONSTRATED

    # THE HEADLINE FINDING MUST NOT BE ABLE TO GO OUT UNESTABLISHED BEHIND A GREEN CODE. The
    # control is the only thing that establishes the SDK's handling of an unexpected 200, and the
    # README leads with it. A draft of this put the `control_did_not_run` sentence into `findings`
    # and let the verdict stay `demonstrated`, so a run that could not bind a socket exited 0 with
    # its headline silently unproven - `check_did_not_run` wearing a pass. Found by Fable.
    if sdk_finding is SdkFinding.CONTROL_DID_NOT_RUN:
        verdict = DemoVerdict.NOT_DEMONSTRATED

    # OUR OWN TWO LISTS DRIFTING APART IS NOT A TRAILING REMARK. `READINGS` in `auditor.mjs` and
    # `SHAPE` here are hand-maintained copies of one list. When the agent requests an endpoint
    # this classifier has no shape for, the reading is an instrument gap of OURS - we asked for it
    # and then could not read it - and it used to reach the findings list while the run still
    # exited 0. Silence is the one response that is definitely wrong. Found by Fable.
    drifted = [r.endpoint for r in readings if r.state is ReadingState.NO_DECLARED_SHAPE]
    if drifted:
        findings.append(
            f"the agent took readings this classifier declares no shape for ({', '.join(drifted)})"
            " - demo/amadeus/auditor.mjs and src/amadeus/demo_audit.py have drifted apart, and an "
            "endpoint we requested and cannot read is our instrument gap, not a finding")
        verdict = DemoVerdict.DEFECT

    self_audit = artefact["self_audit"] if isinstance(artefact["self_audit"], dict) else {}
    if not self_audit.get("loaded"):
        findings.append(f"the self-audit passport was not read: {self_audit.get('error')}")
        verdict = DemoVerdict.NOT_DEMONSTRATED

    payload = artefact["payload"] if isinstance(artefact["payload"], dict) else {}
    if not payload.get("built"):
        findings.append(f"no validation payload was built: {payload.get('absent_reason')}")
        verdict = DemoVerdict.NOT_DEMONSTRATED
    elif not payload.get("base58"):
        findings.append("the payload claims to be built but carries no base58 serialisation")
        verdict = DemoVerdict.DEFECT
    else:
        # A null in the record is either a legitimately empty field or a passport that lost one,
        # and the two must not look alike. The agent names the second case instead of shipping a
        # bare null; this is where the name costs something.
        absent = (payload.get("record") or {}).get("missing_fields") or []
        if absent:
            findings.append(
                f"the validation record is missing {', '.join(absent)} - the passport it was "
                "built from is not the shape this repository publishes")
            verdict = DemoVerdict.DEFECT

    for r in readings:
        if not r.state.is_measured:
            findings.append(f"{r.endpoint}: {r.state.value} - {r.detail}")

    return Judgement(verdict, readings, sdk_finding, tuple(findings), anchor_height)
