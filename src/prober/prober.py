"""T-2.12 - the prober. One active probe, executed only under a mandate (ABI-6-4, ABI-16-5,
ABI-33-4, operator ruling A-9).

WHAT AN ACTIVE PROBE IS HERE, AND WHY IT IS NOT MERELY AN HTTP CALL. Reading a page a subject
publishes is passive: `scripts/measure_qm1_step2.py` fetches declared endpoints all day and asks
nobody's permission, because a public document read by a public reader is what the subject put
there to be read. The one operation implemented here is different in kind - it is an ATTEMPT TO USE
A PATH THE SUBJECT SAYS IS CLOSED. Attempting access you are not entitled to is the act that needs
written authorisation even when it fails, and it is the smallest such act we could build. Calling a
public GET an "active probe" in order to have one would have been the measurement fitted to the
verdict (L-13), and this docstring exists to make that boundary checkable by the next reader.

WHAT IT MEASURES. A subject's material claims that some path refuses some method. The repository
can only show that the claim is WRITTEN; whether the RUNNING system enforces it is a different fact
and the one a reader of a passport actually cares about (L-3, and the repository-versus-runtime
divergence `src/collector/divergence.py` calls the one attack the MVP detects with confidence).

FAIL-CLOSED, STRUCTURALLY. `probe()` receives its transport as an argument and is the only caller of
it. Every denial returns BEFORE the transport is touched, so "the mandate said no" and "no request
was made" are the same event rather than two things kept in step by care. The tests assert the
second, not the first: a recording transport must hold zero calls under every denial reason.

THE ORDER OF THE THREE REQUESTS IS THE POINT OF THE DESIGN, and two of them are controls. A refusal
is not a measurement until the client has been ruled out as its cause (L-11, learned when
provek.dev answered 403 to Python's default user agent and 200 to a browser's), and an absence is
not a refusal until the origin's answer for "never existed" is known.

  * the POSITIVE control asks a path the subject declares public. If it does not succeed, this
    origin is not answering US and no reading below is a verdict about the subject;
  * the NEGATIVE control asks a path that cannot exist. If the probed path answers the same way,
    the reading says only that the path is not served - which is what a host that deployed nothing
    would also produce - and no control has been shown to refuse anything.

Both vetoes are checked in both directions, because the one that flatters the subject is the one
nobody checks. The probe therefore costs three calls, and it asks the mandate about all three
before it spends any.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.abs_profile.measured import NotMeasured
from src.mandate.mandate import Denial, Mandate, may_probe

HTTP_OK, HTTP_REDIRECT, HTTP_CLIENT_ERROR = 200, 300, 400
"""Band edges, named at module scope because two different rules need them: 2xx is what counts as
a successful reading, and nothing below 4xx may be named as a refusal."""

ACTION = "unauthenticated_access_attempt"
"""The ONE action this prober implements.

It is a string rather than an enum member because `Mandate.permitted_actions` is a set of strings
that a subject's signed document populates, and a mandate naming an action we have not built must
stay expressible - otherwise a subject could not grant more than we can do, and the gap between
what was granted and what was performed would stop being visible."""

CALLS_PER_PROBE = 3
"""A positive control, a negative control, and the subject request. All three are spent on the
subject's origin and all three count against the ceiling their mandate set.

It was two until Fable found that a probe with only a positive control cannot tell a withheld path
from one that was never there. The third call is what makes the reading mean anything, so it is
part of the probe's price rather than an optional extra - which is also why the mandate is asked
about all three at once."""

DECLINES_TO_SAY = frozenset({403, 429}) | frozenset(range(500, 600))
"""Statuses that encode the ASKER rather than the resource (L-11, verbatim: "404 is absence; 403,
429 and 5xx are the server declining to say, and must land in a state named for not knowing").

401 is deliberately absent. It is an authentication challenge - a control answering exactly as a
control should - and folding it in here would file the clearest possible evidence that a path is
protected under "we could not tell"."""


class ProbeState(str, Enum):
    """Every outcome of an attempted probe. Disjoint, and not one of them is a zero.

    Three are measurements of the subject and five are statements about our own reach. Keeping the
    second group out of the first is invariant 1: a probe that could not run and a probe that ran
    and found the control missing are opposite findings, and a caller handed a bare boolean cannot
    tell them apart.
    """

    ENFORCED = "enforced"
    """Measured: the running system refused the attempt in one of the ways the claim named."""

    NOT_ENFORCED = "not_enforced"
    """Measured: the running system ANSWERED the attempt successfully. The claimed control is not
    enforced, and this is a finding about the subject."""

    DIVERGED = "diverged"
    """Measured: the path refused, but not in any way the claim named. The deployed system and the
    material describing it are not the same system - `Divergence.DIVERGED`, reached at runtime."""

    REFUSED_BY_MANDATE = "refused_by_mandate"
    """No request was made. Carries the `Denial` that caused it, because "never granted" and
    "revoked" demand different things of the operator."""

    ORIGIN_UNREADABLE = "origin_unreadable"
    """The CONTROL request did not succeed, so this origin is not answering us at all. Nothing was
    established about the subject, and the remedy is to ask again as a different client."""

    SUBJECT_DECLINED = "subject_declined"
    """The origin IS readable - the control succeeded - and the protected path answered with a
    status that encodes the asker rather than the resource, which the claim did not name.

    SPLIT OUT OF `ORIGIN_UNREADABLE` AFTER FABLE FOUND THE COLLAPSE. Both are "we could not tell",
    and they are not the same fact: one says the origin refuses this client, the other says the
    origin serves us everywhere except here. They lead to different next actions - ask again as a
    different client, versus ask the subject whether a rate limiter or a WAF sits in front of this
    path - and a caller handed one name for both would have had to guess which. Invariant 1, inside
    a state that was itself created to honour invariant 1."""

    INDISTINGUISHABLE_FROM_ABSENT = "indistinguishable_from_absent"
    """The origin answers the probed path exactly as it answers a path that does not exist.

    Nothing about a CONTROL was established. The path is not served - which may be because the
    subject withholds it or because it was never there - and those are the two states this probe
    exists to tell apart. Reporting ENFORCED here would credit the subject with a refusal never
    performed, and a host that deployed nothing at all would earn the same verdict.

    This is L-10's third sibling, the one the lesson adds beside `nothing_qualified` and
    `unreadable`: THE INSTRUMENT CANNOT SEE THE QUANTITY. The reading is complete, the origin is
    healthy, and the question asked cannot be answered by the answer received."""

    TRANSPORT_FAILED = "transport_failed"
    """No HTTP answer at all. Our instrument, not their system."""


_ABSENCE = {
    # The coarse class the rest of the methodology speaks (`NotMeasured`), beside the fine state
    # that names WHICH absence it was. The fine state is not discarded when the coarse one is
    # attached: four of these share `UNREADABLE`, and a caller that needed to tell an origin
    # refusing our client from a path refusing us on an origin that answers from a transport that
    # never connected still can. The coarse class exists because passports speak `NotMeasured` and
    # a third vocabulary at that boundary would be one more thing to keep in step; it is a
    # projection of these states and never a replacement for them.
    ProbeState.REFUSED_BY_MANDATE: NotMeasured.CHECK_DID_NOT_RUN,
    ProbeState.ORIGIN_UNREADABLE: NotMeasured.UNREADABLE,
    ProbeState.SUBJECT_DECLINED: NotMeasured.UNREADABLE,
    # `UNREADABLE` is the least wrong of the three and it is not a comfortable fit, so the reason
    # is written here rather than left to look obvious. L-10 names this state as a THIRD sibling
    # beside `nothing_qualified` and `unreadable` - the wrong source was asked - and `NotMeasured`
    # has only the two. Widening that enum is a change to the vocabulary every passport speaks and
    # is not this task's to make; collapsing to `nothing_qualified` would be worse, because that
    # one means the check ran and the subject matched nothing, which is a statement about them.
    ProbeState.INDISTINGUISHABLE_FROM_ABSENT: NotMeasured.UNREADABLE,
    ProbeState.TRANSPORT_FAILED: NotMeasured.UNREADABLE,
}


@dataclass(frozen=True)
class Response:
    """One HTTP answer, or a NAMED reason there was none.

    `status is None` means no answer was obtained, and `reason` must then carry a name rather than a
    number. `curl rc=35` was once recorded as a reason in this repository and it took a separate
    investigation to establish that it meant the host offers no certificate at all - a fact about
    the subject, where a timeout would have been a fact about us (L-23). A transport that cannot
    name its failure fails loudly here instead of handing the prober a blank.
    """

    status: int | None
    reason: str = ""

    def __post_init__(self) -> None:
        if self.status is None and not self.reason.strip():
            raise ValueError(
                "a Response with no status must carry the NAMED reason there was none. An unnamed "
                "failure reaches the report as a number or as a blank, and both of those cost this "
                "project a separate investigation once already (L-23)")

    @property
    def answered(self) -> bool:
        return self.status is not None

    @property
    def succeeded(self) -> bool:
        return self.status is not None and HTTP_OK <= self.status < HTTP_REDIRECT


@dataclass(frozen=True)
class ControlClaim:
    """A claim by the subject that some path refuses some method, and the address of that claim.

    `claimed_by` is not documentation. A verifier that reports "the control is not enforced" without
    being able to say where the subject claimed it has produced an accusation rather than a
    measurement, and the whole method of this project is that a verdict cites what it was computed
    from.
    """

    subject_id: str
    origin: str
    control_path: str
    """A path the subject declares PUBLIC on the same origin. The instrument control: if this does
    not answer 2xx, the origin is not answering us and nothing below is a reading (L-11)."""
    absent_path: str
    """A path on the same origin that CERTAINLY does not exist. The negative control.

    THE POSITIVE CONTROL ALONE LETS AN ORIGIN PASS FOR FREE, and Fable found the hole in the first
    shipped claim. Most static hosts answer 404 to everything unknown, so `/.git/config` answering
    404 is the same reading as `/typo-nobody-serves` answering 404: it says the path is not served
    and says NOTHING about a control refusing it. Publishing that as ENFORCED would credit a
    subject for a mechanism never exercised - and a host that deploys nothing at all would earn the
    same verdict, as would a claim with a misspelt path.

    L-11 says 404 IS absence, and absence reads as a finding. This field is what stops it becoming
    one: when the protected path and this path answer identically, the probe reports that it cannot
    tell the two apart rather than choosing the flattering reading.

    It earns its call twice. It also catches the soft 404 - an origin answering 200 to paths that do
    not exist, which four ERC-8004 identities did in Q-M1 (L-23). Against such an origin a 200 on
    the protected path is not evidence of exposure either, and NOT_ENFORCED must not be published.
    """
    protected_path: str
    method: str
    expected_refusal: frozenset[int]
    """The statuses the claim says this path answers with. Empty is refused at construction: a
    claim that does not say what refusal looks like cannot be tested, and accepting one would let
    every reading fall through to DIVERGED."""
    claimed_by: str
    """Where the subject makes the claim - a file, a document, a section."""

    def __post_init__(self) -> None:
        if not self.expected_refusal:
            raise ValueError(
                "a ControlClaim with no expected refusal is untestable: every possible reading "
                "would be classified DIVERGED, which is a verdict manufactured by the absence of "
                "the claim rather than measured against it")
        if not self.claimed_by.strip():
            raise ValueError(
                "a ControlClaim must name where the subject makes it. A finding that cannot cite "
                "the claim it refutes is an accusation, not a verification")
        successes = {s for s in self.expected_refusal if HTTP_OK <= s < HTTP_CLIENT_ERROR}
        if successes:
            # A CLAIM WRITTEN BACKWARDS TURNS AN OPEN PATH INTO A PASS with one field, and until
            # Fable asked, the only thing standing against it was a test pinning the single shipped
            # instance. A 2xx is a subject ANSWERING the request; naming one as the refusal the
            # claim expects would make `classify` return ENFORCED for the exposure it exists to
            # find. 3xx is refused with it: a redirect is not a refusal either, and an origin whose
            # catch-all redirects is precisely the case that reaches this class of mistake.
            raise ValueError(
                f"expected_refusal names {sorted(successes)}, and a 2xx or 3xx is the subject "
                "answering rather than refusing. A claim whose expected refusal is a success has "
                "been written backwards, and it would turn an open path into a PASS")
        if self.absent_path == self.protected_path:
            raise ValueError(
                "the negative control and the probed path are the same path, so the comparison "
                "that separates 'withheld' from 'never existed' would compare a reading with "
                "itself and always agree")

    def control_url(self) -> str:
        return self.origin.rstrip("/") + self.control_path

    def absent_url(self) -> str:
        return self.origin.rstrip("/") + self.absent_path

    def protected_url(self) -> str:
        return self.origin.rstrip("/") + self.protected_path


@dataclass(frozen=True)
class ProbeResult:
    """What one probe established, and by what authority.

    `mandate_ref` travels with the reading for the reason `access_channel` does on a passport: a
    verdict that does not carry the instrument beside it cannot be audited afterwards, and an
    active probe's "instrument" includes the document that permitted it.
    """

    state: ProbeState
    claim: ControlClaim
    mandate_ref: str | None
    """None only when the probe was refused for want of any mandate at all - there was no document
    to name. Every other state carries the reference of the mandate the probe ran under."""
    denial: Denial | None = None
    control: Response | None = None
    absent: Response | None = None
    subject: Response | None = None
    calls_made: int = 0

    @property
    def not_measured(self) -> NotMeasured | None:
        """The coarse absence class, or None when a measurement was actually taken."""
        return _ABSENCE.get(self.state)

    def verdict(self) -> str:
        """PASS / FAIL / NOT_MEASURED, computed by code from the measured status (invariant 2).

        NOT_MEASURED is never a FAIL. A subject is not marked down because our client was refused,
        because their origin was down, or because nobody signed a mandate - that is a verifier
        punishing someone for its own blindness (`src/collector/divergence.py`).
        """
        if self.not_measured is not None:
            return "NOT_MEASURED"
        return "PASS" if self.state is ProbeState.ENFORCED else "FAIL"


def classify(claim: ControlClaim, control: Response, absent: Response,
             subject: Response) -> ProbeState:
    """The verdict function: three readings in, one state out, no clock and no network.

    Separated from `probe()` so that every branch is reachable from a test without a transport at
    all - a classifier that can only be exercised through the thing that makes requests is a
    classifier whose edges get asserted about rather than run.

    The two controls answer two different questions and both are asked before the subject's reading
    is allowed to mean anything. The POSITIVE control asks whether this origin talks to us at all.
    The NEGATIVE control asks whether this origin's answer to the probed path differs from its
    answer to a path that was never there - because if it does not, the reading contains no
    information about a control, however much it looks like a refusal.
    """
    if not control.succeeded:
        # L-11 ARMED. Checked before anything else and against the CONTROL, not the subject path:
        # the question this answers is "would the instrument have been able to see presence", and
        # it has to be answered before any reading is allowed to mean something about the subject.
        return ProbeState.ORIGIN_UNREADABLE
    if not subject.answered:
        return ProbeState.TRANSPORT_FAILED

    # IS THIS ORIGIN'S ANSWER FOR ABSENCE KNOWN? Everything below that compares the subject's
    # reading against a catch-all depends on this being true, and it is NOT the same question as
    # "did the negative control answer".
    #
    # FABLE FOUND THIS ON THE SECOND REPAIR, WHICH IS WHY IT IS A NAMED QUANTITY NOW. The condition
    # was `not absent.answered or absent.status == subject.status` - so a negative control that
    # came back 403 counted as an answer, its status differed from the subject's, and the reading
    # was promoted to ENFORCED. That is exactly the L-11 defect this classifier arms against, moved
    # one control to the left: 403, 429 and 5xx are the server declining to say, and a decline
    # establishes no catch-all. On an origin that answers 403 to clients at its own discretion -
    # which is this subject, measured - one unlucky call out of three would have credited the
    # subject with a control never exercised.
    catch_all_known = absent.answered and absent.status not in DECLINES_TO_SAY

    # THE VETO ITSELF, DEFINED ONCE AND CONSULTED BY EVERY MEASURED VERDICT BELOW.
    #
    # It was written inline at two of the three, and the third - the fall-through to DIVERGED - had
    # none, which Fable found on the round after the round that introduced it. An origin that
    # redirects every unknown path (301 is the commonest catch-all after 404) answered the probed
    # path exactly as it answered a path that never existed, and that was published as a measured
    # FAIL: a host which had deployed nothing would be accused of divergence. Two copies of a rule
    # and a third place that needed it is L-2 in one function, so there is one copy now.
    reading_matches_absence = not catch_all_known or absent.status == subject.status

    if absent.succeeded:
        # THE SOFT 404. This origin answers 2xx for paths that do not exist, so a 2xx on the probed
        # path is not evidence that anything is served there and a refusal cannot be recognised at
        # all. Four ERC-8004 identities answered exactly this way in Q-M1 and were on their way to
        # a human as businesses (L-23). Checked before the refusal test below, because on such an
        # origin every reading is uninformative rather than only the successful ones.
        return ProbeState.INDISTINGUISHABLE_FROM_ABSENT
    if subject.status in claim.expected_refusal:
        if reading_matches_absence:
            # THE HOLE FABLE FOUND IN THE FIRST SHIPPED CLAIM. `/.git/config` answering 404 on a
            # host whose catch-all is 404 is the same reading as a misspelt path answering 404: it
            # says the path is not served and nothing whatever about a control refusing it. A host
            # that deployed nothing at all would pass here.
            return ProbeState.INDISTINGUISHABLE_FROM_ABSENT
        # BEFORE the `DECLINES_TO_SAY` test below, and the order is the interesting part. A subject
        # whose claim is "this path answers 403" and which answers 403 has demonstrated its control
        # exactly; filing that under "the server declined to say" would discard the clearest
        # possible measurement because its status code also appears in a list of ambiguous ones.
        # The control request is what makes this safe - the origin has already been shown to serve
        # this client.
        return ProbeState.ENFORCED
    if subject.succeeded:
        if reading_matches_absence:
            # AND THE SAME VETO IN THE ACCUSING DIRECTION. A 200 here says the path is served only
            # if this origin does not answer 200 to everything - and with the catch-all
            # unestablished, a soft 404 has not been ruled out. Publishing NOT_ENFORCED would be an
            # accusation computed from an instrument reading we failed to take.
            return ProbeState.INDISTINGUISHABLE_FROM_ABSENT
        return ProbeState.NOT_ENFORCED
    if subject.status in DECLINES_TO_SAY:
        # NOT `ORIGIN_UNREADABLE`. The control succeeded, so the origin is demonstrably answering
        # this client; what declined to say is this PATH. Returning the origin-level state here
        # would have put two different facts - "they will not talk to us" and "they talk to us
        # everywhere but here" - behind one name, in the classifier written to stop exactly that.
        return ProbeState.SUBJECT_DECLINED
    if reading_matches_absence:
        # THE THIRD DOOR, AND IT WAS OPEN. Divergence means the path refused in a way the claim did
        # not name - a statement that the path EXISTS and behaves unexpectedly. When the origin
        # answers it exactly as it answers nothing at all, the honest reading is that we cannot see
        # the path, not that we caught it misbehaving. `SUBJECT_DECLINED` above is deliberately
        # left in front of this: a path that declines to say has told us something about itself
        # that the catch-all comparison cannot take away.
        return ProbeState.INDISTINGUISHABLE_FROM_ABSENT
    return ProbeState.DIVERGED


def probe(claim: ControlClaim, mandate: Mandate | None, now: datetime,
          fetch: Callable[[str, str], Response], calls_last_hour: int = 0) -> ProbeResult:
    """Attempt one probe. Returns what was established, or the named reason nothing was.

    `fetch(method, url)` is the transport, and it is passed in rather than imported so that the
    only path from this function to the network runs through an argument the caller supplies. Every
    refusal below returns before `fetch` is named.
    """
    # THE MANDATE IS ASKED ABOUT THE LAST CALL THE PROBE WOULD MAKE, NOT THE FIRST.
    #
    # `may_probe` answers about one call: it denies when `calls_last_hour` has already reached the
    # ceiling. A probe that spends three calls and asks about one buys the right to make a single
    # request and then makes three, which overruns a ceiling that exists as the subject's protection -
    # the one number in the mandate that bounds what we cost them. Asking about the last call means
    # a probe that cannot afford its own control does not run at all, rather than running half of
    # itself and reporting the half as a reading.
    ok, why = may_probe(mandate, ACTION, now, calls_last_hour + CALLS_PER_PROBE - 1)
    if mandate is None or not ok:
        # `mandate is None` is tested first for the type checker's benefit and not the reader's:
        # `may_probe(None, ...)` already returned NO_MANDATE, so the two conditions cannot disagree.
        return ProbeResult(state=ProbeState.REFUSED_BY_MANDATE, claim=claim,
                           mandate_ref=mandate.ref if mandate is not None else None,
                           denial=why, calls_made=0)

    # BOTH CONTROLS ARE TAKEN WITH THE SAME METHOD THE CLAIM USES, and the negative one is asked
    # that way for a reason: an origin can route GET and POST to different handlers, so a catch-all
    # established with the wrong verb is a catch-all for a question nobody asked.
    control = fetch("GET", claim.control_url())
    absent = fetch(claim.method, claim.absent_url())
    subject = fetch(claim.method, claim.protected_url())
    return ProbeResult(state=classify(claim, control, absent, subject), claim=claim,
                       mandate_ref=mandate.ref, control=control, absent=absent, subject=subject,
                       calls_made=CALLS_PER_PROBE)
