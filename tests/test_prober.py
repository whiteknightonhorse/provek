"""LAW-PROBE-NEEDS-MANDATE - a denied mandate makes ZERO requests, and the denial is the result.

WHAT IS ASSERTED, AND WHY IT IS NOT "the prober checks the mandate". Checking is what the code
looks like; making no request is what the subject experiences. Every assertion below is about the
transport: a recording `fetch` is handed to `probe()` and must hold nothing at all after each
denial. A refactor that moved the check after the first call, or that fetched the control request
"just to warm the connection", would leave the check visibly present and the property gone - which
is this repository's own subject defect, and the shape L-21 was written about after three repairs
in a gate turned out never to be called.

WHY THE DENIALS ARE ENUMERATED FROM THE ENUM. `test_every_denial_reason_is_covered` walks
`Denial` itself, so a sixth reason added to `src/mandate/mandate.py` fails this file until somebody
decides what the prober does about it. A hand-written list of five would have gone on passing while
the new reason went untested - a suite that is complete on the day it is written and silently
partial afterwards.

HOW TO MAKE IT FAIL: move the `may_probe` call in `src/prober/prober.py` below the two `fetch`
calls, or delete it. The red run is kept as `evidence/RED-013-prober-without-a-mandate.txt`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.abs_profile.measured import NotMeasured
from src.mandate.mandate import Denial, Mandate, may_probe
from src.prober.prober import (
    ACTION,
    CALLS_PER_PROBE,
    ControlClaim,
    ProbeState,
    Response,
    probe,
)
from src.prober.self_probe import SELF_MANDATE, SOURCE_EXPOSURE_CLAIM

NOW = datetime(2026, 8, 20, tzinfo=timezone.utc)

CLAIM = ControlClaim(
    subject_id="git:a/b", origin="https://example.test", control_path="/",
    absent_path="/no-such-path", protected_path="/api/private", method="GET",
    expected_refusal=frozenset({401}),
    claimed_by="README.md, 'the API refuses unauthenticated callers'",
)


class Recorder:
    """A transport that records instead of connecting.

    Answers 2xx to everything, so a probe that reached it would be classified NOT_ENFORCED rather
    than fail for want of a reply: the assertions below must fail because a CALL WAS MADE, not
    because the reply was awkward.
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def __call__(self, method: str, url: str) -> Response:
        self.calls.append((method, url))
        return Response(200, "recorded")


def _mandate(**kw) -> Mandate:
    base = dict(ref="m-0001", subject_id="git:a/b", permitted_actions=frozenset({ACTION}),
                max_calls_per_hour=10,
                blast_radius="no customer traffic is affected",
                liability="the incubator covers direct damage",
                abort_condition="any 5xx",
                valid_from=NOW - timedelta(days=1), valid_until=NOW + timedelta(days=30))
    base.update(kw)
    return Mandate(**base)


# Each entry: the denial the prober must report, and the (mandate, calls_last_hour) that causes it.
DENIALS: dict[Denial, tuple[Mandate | None, int]] = {
    Denial.NO_MANDATE: (None, 0),
    Denial.REVOKED: (_mandate(revoked_at=NOW - timedelta(hours=1)), 0),
    Denial.EXPIRED: (_mandate(valid_until=NOW - timedelta(days=1)), 0),
    Denial.ACTION_NOT_PERMITTED: (_mandate(permitted_actions=frozenset({"latency_probe"})), 0),
    Denial.RATE_EXCEEDED: (_mandate(max_calls_per_hour=10), 10),
}


def test_the_recorder_would_notice_a_call() -> None:
    """INSTRUMENT CONTROL, and without it every assertion in this file is vacuous.

    `assert recorder.calls == []` passes just as well when the recorder is broken as when the
    prober is fail-closed. Before absence is allowed to mean anything, the instrument has to be
    shown capable of seeing presence (L-11's general form, applied to a test double).
    """
    r = Recorder()
    r("GET", "https://example.test/")
    assert r.calls == [("GET", "https://example.test/")]


@pytest.mark.parametrize("reason", list(DENIALS))
def test_a_denied_mandate_makes_no_request(reason: Denial) -> None:
    mandate, spent = DENIALS[reason]
    r = Recorder()
    result = probe(CLAIM, mandate, NOW, r, calls_last_hour=spent)
    assert r.calls == [], (
        f"the prober contacted {r.calls} while the mandate said {reason.value}. Probing a live "
        "system without permission is an incident and not a verification: the request is the harm, "
        "and a check that runs after it has already gone out prevents nothing."
    )
    assert result.state is ProbeState.REFUSED_BY_MANDATE
    assert result.denial is reason
    assert result.calls_made == 0


def test_every_denial_reason_is_covered() -> None:
    """A new refusal reason must be given a decision here rather than inherit one silently."""
    assert set(DENIALS) == set(Denial), (
        f"untested denial reasons: {sorted(d.value for d in set(Denial) - set(DENIALS))}. Add the "
        "case above and decide what the prober does about it."
    )


def test_a_refusal_is_NOT_MEASURED_and_never_a_failure_of_the_subject() -> None:
    """Invariant 1 and ABI-33-4: "we could not measure" is not "the subject failed"."""
    result = probe(CLAIM, None, NOW, Recorder())
    assert result.not_measured is NotMeasured.CHECK_DID_NOT_RUN
    assert result.verdict() == "NOT_MEASURED"


def test_a_refusal_for_want_of_a_document_names_no_document() -> None:
    """`mandate_ref` is None only where there was no mandate; every other state carries one."""
    assert probe(CLAIM, None, NOW, Recorder()).mandate_ref is None
    revoked = probe(CLAIM, DENIALS[Denial.REVOKED][0], NOW, Recorder())
    assert revoked.mandate_ref == "m-0001"


def test_a_permitted_probe_spends_both_controls_before_the_subject() -> None:
    """The controls are not afterthoughts; they are the first things bought with the permission.

    Order is asserted, not just membership. A probe that read the subject's path first and its
    controls afterwards would produce the same three calls and the same verdict, and would have
    spent the subject's budget on a reading it might then have to discard.
    """
    r = Recorder()
    result = probe(CLAIM, _mandate(), NOW, r)
    assert r.calls == [("GET", "https://example.test/"),
                       ("GET", "https://example.test/no-such-path"),
                       ("GET", "https://example.test/api/private")]
    assert result.calls_made == CALLS_PER_PROBE


def test_the_negative_control_is_asked_with_the_claims_own_method() -> None:
    """An origin may route GET and POST to different handlers, so a catch-all established with the
    wrong verb is a catch-all for a question nobody asked."""
    claim = ControlClaim(
        subject_id="git:a/b", origin="https://example.test", control_path="/",
        absent_path="/no-such-path", protected_path="/api/private", method="DELETE",
        expected_refusal=frozenset({405}), claimed_by="README.md, 'DELETE is refused'",
    )
    r = Recorder()
    probe(claim, _mandate(), NOW, r)
    methods = dict((url, method) for method, url in r.calls)
    assert methods["https://example.test/no-such-path"] == "DELETE"
    assert methods["https://example.test/api/private"] == "DELETE"
    assert methods["https://example.test/"] == "GET", (
        "the positive control asks whether the origin serves this client at all, which is a GET on "
        "a public page regardless of what the claim is about"
    )


def test_a_probe_that_cannot_afford_its_own_control_does_not_run() -> None:
    """The ceiling in a mandate bounds what we cost the subject, and it is spent in whole probes.

    Two calls left of a ceiling of three is not enough for a probe that needs three, and the honest
    answer is to make none. `may_probe` answers about a single call, so a prober that asked about
    the FIRST of its three would buy the right to one request and then make three - overrunning the
    only number in the document that limits what the subject pays for being verified.
    """
    r = Recorder()
    result = probe(CLAIM, _mandate(max_calls_per_hour=3), NOW, r, calls_last_hour=1)
    assert r.calls == []
    assert result.denial is Denial.RATE_EXCEEDED


def test_a_full_probe_still_fits_exactly_at_the_ceiling() -> None:
    """The other edge of the same arithmetic: three calls left of three is enough, and must not be
    refused. A limiter that is safe by being wrong in the strict direction produces false reds, and
    a false red teaches walking past a gate exactly as a false green does (L-5)."""
    r = Recorder()
    result = probe(CLAIM, _mandate(max_calls_per_hour=3), NOW, r, calls_last_hour=0)
    assert len(r.calls) == CALLS_PER_PROBE
    assert result.denial is None


def test_the_incubators_own_mandate_permits_exactly_what_the_prober_implements() -> None:
    """The loaded mandate is not a wider grant than the code can spend (L-18: this one is real)."""
    assert SELF_MANDATE.permitted_actions == frozenset({ACTION})
    assert SELF_MANDATE.subject_id == SOURCE_EXPOSURE_CLAIM.subject_id


def test_the_loaded_claim_is_an_access_attempt_and_not_a_public_read() -> None:
    """THE ASSERTION FABLE'S REFUTATION EARNED, and it is about the shipped instance.

    The first version of this component named its action `unauthenticated_access_attempt` and wired
    up `GET /api/apply` expecting 405 - a method restriction on a PUBLIC intake endpoint, which any
    reader may request and which needs no mandate at all. The name was active and the instance was
    passive: L-13, the measurement fitted to the acceptance criterion, invisible afterwards because
    the surrounding code reads as principled.

    Nothing structural could have caught it, and this test is not structural either - it pins the
    three properties that made the old claim indefensible. A success status can never be a claimed
    REFUSAL, the path probed is not one the subject invites the public to call, and the claim
    carries a negative control so a reading can be told apart from a catch-all. All three are
    cheap; the point is that the next person to retarget this claim has to look at them.

    What this test does NOT do is decide whether the probed path is genuinely declared closed
    rather than merely absent. It cannot: that is a fact about the origin, established at runtime by
    comparing the reading against the negative control, and `classify` reports
    INDISTINGUISHABLE_FROM_ABSENT when the two agree. A structural test that claimed to settle it
    from the claim alone would be the stronger-than-the-artefact move one level up.
    """
    claim = SOURCE_EXPOSURE_CLAIM
    HTTP_OK, HTTP_REDIRECT = 200, 300
    assert not any(HTTP_OK <= s < HTTP_REDIRECT for s in claim.expected_refusal), (
        f"the claim expects {sorted(claim.expected_refusal)} as a REFUSAL, and a 2xx is a subject "
        "answering the request. A claim whose expected refusal is a success has been written "
        "backwards."
    )
    assert claim.protected_path not in ("/", "/api/apply"), (
        f"{claim.protected_path} is a path this subject publishes for the public to call. Probing "
        "it is a read, not an access attempt, and it needs no mandate - so a prober built around a "
        "mandate would be governing nothing (L-13)."
    )
    assert claim.absent_path and claim.absent_path != claim.protected_path, (
        "the claim carries no negative control, so a refusal could not be told apart from a "
        "catch-all answer to a path that was never there."
    )


def test_the_incubators_own_mandate_has_not_lapsed() -> None:
    """A DATED GATE, and its red is the correct behaviour rather than a defect to route around.

    A standing permission to send unauthenticated requests at a live system should expire, and
    somebody should have to renew it deliberately. When this goes red, the mandate has lapsed: the
    prober is already fail-closed against that, and what is owed is a decision, not a new date.

    Asked through `may_probe` against the real clock rather than through a helper of its own. The
    first version called an `is_live()` in `self_probe.py` whose docstring said the runner read it
    before spending a call - and the runner never called it, so the only caller was this line and
    the docstring was false. Fable found it. `may_probe` is what actually stops the probe when the
    mandate lapses, so it is what this asserts against; a second implementation of the same
    condition is a copy that can drift from the one that runs (L-2).
    """
    ok, why = may_probe(SELF_MANDATE, ACTION, datetime.now(timezone.utc))
    reason = why.value if why is not None else "no reason given"
    assert ok, (
        f"the self-mandate {SELF_MANDATE.ref} does not permit a probe today ({reason}); it runs to "
        f"{SELF_MANDATE.valid_until.date().isoformat()}. Renew it in src/prober/self_probe.py as an "
        "act somebody takes, with a decision entry - do not widen the window to make this green."
    )
