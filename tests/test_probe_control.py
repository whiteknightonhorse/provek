"""LAW-PROBE-CONTROL-BEFORE-ABSENCE - a status code is not a measurement until the client has been
ruled out as its cause.

THIS IS L-11 ARMED, AND L-11 IS NOT HYPOTHETICAL ON THIS ORIGIN. `https://provek.dev/` answers 200
to a browser's user agent and 403 to Python's default one - measured again on 2026-08-20, in the
same hour this file was written, by asking twice with nothing changed but the agent. A prober
without a control request would have read that 403 off a protected path, found it in the set of
refusals the subject's claim named, and published ENFORCED: the subject credited with a control
that was never exercised, because Cloudflare declined to talk to US.

So the control request is not a nicety and its failure is not a warning. It is a veto. Every case
below is about which readings are allowed to become verdicts, and the two that matter most are the
ones where a plausible verdict is refused:

  * a control that does not answer 2xx voids the probe even when the protected path answered
    exactly as the claim predicted (the failure above, in the direction that flatters the subject);
  * a protected path answering 403, 429 or 5xx when the claim did NOT name that status is filed as
    "we could not tell" rather than as divergence - the server declining to say, in L-11's words.

WHAT IS DELIBERATELY NOT IN `DECLINES_TO_SAY`: 401, and one ordering. A path whose claim IS "this
answers 403" and which answers 403 is ENFORCED, because the control already proved the origin
serves this client - and discarding the clearest measurement available on the grounds that its
status also appears in a list of ambiguous ones would be the instrument refusing to read its own
dial.

HOW TO MAKE IT FAIL: delete the `if not control.succeeded` branch from `classify` in
`src/prober/prober.py`. The red run is kept as `evidence/RED-013-prober-without-a-mandate.txt`.
"""
from __future__ import annotations

import pytest

from src.abs_profile.measured import NotMeasured
from src.prober.prober import ControlClaim, ProbeState, Response, classify

CLAIM = ControlClaim(
    subject_id="git:a/b", origin="https://example.test", control_path="/",
    absent_path="/no-such-path", protected_path="/api/apply", method="GET",
    expected_refusal=frozenset({405}),
    claimed_by="functions/api/apply.js, onRequestGet returns 405",
)

OK = Response(200, "control page served")
GONE = Response(404, "catch-all for a path that was never there")
"""The negative control on an ordinary origin: unknown paths answer 404. Every case below passes
this unless it is specifically about the catch-all, so a reading that matches the claim is
distinguishable from absence and is allowed to become a verdict."""


def test_the_classifier_can_return_ENFORCED() -> None:
    """INSTRUMENT CONTROL. Most cases here assert that a verdict is REFUSED, and a classifier
    hard-wired to refuse everything would pass all of them. This is the one that would die."""
    assert classify(CLAIM, OK, GONE, Response(405, "method not allowed")) is ProbeState.ENFORCED


def test_a_refused_control_voids_a_reading_that_would_have_flattered_the_subject() -> None:
    """The exact L-11 failure: the edge refuses our client, and every path answers a refusal.

    The protected path returned 405 - precisely what the claim predicts - and it must NOT be read
    as the control being enforced, because the origin was not answering this client at all.
    """
    state = classify(CLAIM, Response(403, "cloudflare refused the client"), GONE,
                     Response(405, "method not allowed"))
    assert state is ProbeState.ORIGIN_UNREADABLE, (
        "a 403 on the control page means the origin is refusing US. Reading the protected path's "
        "reply as a measurement of the subject's control publishes our own blindness as their "
        "compliance - and in the direction that flatters them, which is the direction nobody "
        "checks."
    )


def test_a_refused_control_also_voids_a_reading_that_would_have_accused_the_subject() -> None:
    """Symmetry, and it is the half that would cause real damage.

    A verifier that says "your control is not enforced" on the strength of a probe that could not
    reach the origin has published an accusation computed from its own failure.
    """
    state = classify(CLAIM, Response(None, "connection refused"), GONE,
                     Response(200, "served"))
    assert state is ProbeState.ORIGIN_UNREADABLE


@pytest.mark.parametrize("status", [403, 429, 500, 502, 503, 599])
def test_a_status_that_encodes_the_asker_is_not_divergence(status: int) -> None:
    """L-11 verbatim: 403, 429 and 5xx are the server declining to say, and must land in a state
    named for not knowing - never in the same field as a measured result."""
    assert classify(CLAIM, OK, GONE, Response(status, "declined")) is ProbeState.SUBJECT_DECLINED


def test_a_declining_path_on_a_readable_origin_is_not_a_refused_origin() -> None:
    """The two "we could not tell" states are two facts, and Fable found them sharing one name.

    `ORIGIN_UNREADABLE` means this origin will not talk to us - the remedy is to ask again as a
    different client. `SUBJECT_DECLINED` means the origin talks to us everywhere except this path -
    the remedy is to ask the subject what sits in front of it. Collapsing them left the caller to
    guess which, in the classifier written to stop exactly that collapse.
    """
    declined = classify(CLAIM, OK, GONE, Response(403, "forbidden"))
    refused_origin = classify(CLAIM, Response(403, "edge refused the client"), GONE,
                              Response(403, "x"))
    assert declined is ProbeState.SUBJECT_DECLINED
    assert refused_origin is ProbeState.ORIGIN_UNREADABLE
    assert declined is not refused_origin


def test_a_claimed_refusal_beats_the_ambiguity_list() -> None:
    """Ordering, and it is the one place the two rules disagree.

    The subject's claim is that this path answers 403. It answered 403, and the control proved the
    origin serves this client. That is the strongest possible evidence the control is enforced, and
    it must not be thrown away because 403 is also a status a CDN uses to refuse strangers.
    """
    claim = ControlClaim(
        subject_id="git:a/b", origin="https://example.test", control_path="/",
        absent_path="/no-such-path", protected_path="/admin", method="GET",
        expected_refusal=frozenset({403}),
        claimed_by="SECURITY.md, 'the admin surface answers 403 to the public'",
    )
    assert classify(claim, OK, GONE, Response(403, "forbidden")) is ProbeState.ENFORCED


def test_a_success_where_a_refusal_was_claimed_is_the_finding() -> None:
    """The whole point of an active probe: the material says closed, the running system says open."""
    result_state = classify(CLAIM, OK, GONE, Response(200, "served a body"))
    assert result_state is ProbeState.NOT_ENFORCED


def test_a_refusal_the_claim_never_named_is_divergence_and_not_a_pass() -> None:
    """410 where 405 was claimed, on an origin whose absence answer is 404.

    The path refuses, and not for the reason the subject documented - a measured FAIL rather than a
    comfortable "well, it refused", because the deployed system and the material describing it are
    not the same system (`src/collector/divergence.py`). The negative control is what licenses the
    reading: 410 is not how this origin says "never existed", so something IS there and it is not
    what the claim describes.
    """
    assert classify(CLAIM, OK, GONE, Response(410, "gone")) is ProbeState.DIVERGED


@pytest.mark.parametrize(("absent", "subject", "why"), [
    (Response(301, "redirected"), Response(301, "redirected"),
     "an origin that redirects every unknown path - the commonest catch-all after 404"),
    (Response(404, "not found"), Response(404, "not found"),
     "the probed path answers exactly as a path that never existed"),
    (Response(None, "connection reset"), Response(410, "gone"),
     "the negative control never answered, so no catch-all was established"),
    (Response(503, "the edge declined"), Response(410, "gone"),
     "the negative control declined to say, which establishes no catch-all either"),
])
def test_divergence_is_never_published_over_an_unestablished_catch_all(
        absent: Response, subject: Response, why: str) -> None:
    """THE THIRD DOOR, AND IT WAS OPEN FOR A ROUND. Fable found it after the repair that closed the
    other two.

    Both vetoes were written inline at ENFORCED and at NOT_ENFORCED, and the fall-through to
    DIVERGED had neither - so a host that had deployed NOTHING, answering every path with the same
    redirect, was accused of divergence on a measured FAIL. That is the mirror image of the
    sentence `INDISTINGUISHABLE_FROM_ABSENT` exists for, and it survived two rounds of repairing
    the same defect in its two neighbours: the rule had two copies and a third place that needed it
    (L-2, inside one function).
    """
    state = classify(CLAIM, OK, absent, subject)
    assert state is ProbeState.INDISTINGUISHABLE_FROM_ABSENT, f"{why}: got {state.value}"


def test_a_refusal_matching_the_catch_all_is_not_a_control_being_enforced() -> None:
    """THE HOLE FABLE FOUND IN THE FIRST SHIPPED CLAIM, and it is the case this project exists for.

    The subject claims a path refuses with 404. It answers 404 - and so does a path that was never
    there. The reading says the path is NOT SERVED, which may be because the subject withholds it
    or because it never existed, and telling those apart is the entire job. Publishing ENFORCED
    would credit a refusal never performed; a host that deployed nothing at all, or a claim with a
    misspelt path, would earn the same verdict.
    """
    claim = ControlClaim(
        subject_id="git:a/b", origin="https://example.test", control_path="/",
        absent_path="/no-such-path", protected_path="/.git/config", method="GET",
        expected_refusal=frozenset({404}),
        claimed_by="wrangler.toml, 'only the build output is published'",
    )
    assert classify(claim, OK, GONE, Response(404, "not found")) is (
        ProbeState.INDISTINGUISHABLE_FROM_ABSENT)
    # ...and the same claim IS measurable on an origin whose catch-all differs from the refusal.
    assert classify(claim, OK, Response(410, "gone"),
                    Response(404, "not found")) is ProbeState.ENFORCED


def test_an_unanswered_negative_control_never_upgrades_a_reading_to_a_pass() -> None:
    """If the catch-all was not established, the comparison cannot be made - and the missing
    comparison lands in "we could not tell", not in the flattering state."""
    assert classify(CLAIM, OK, Response(None, "connection reset"),
                    Response(405, "method not allowed")) is (
        ProbeState.INDISTINGUISHABLE_FROM_ABSENT)


@pytest.mark.parametrize("status", [403, 429, 500, 503])
def test_a_negative_control_that_declines_to_say_establishes_no_catch_all(status: int) -> None:
    """L-11 ON THE NEGATIVE CONTROL, and it was unarmed for one round.

    The condition was "did the negative control answer" - so a 403 counted as an answer, differed
    from the subject's 404, and the reading was promoted to ENFORCED. But 403, 429 and 5xx are the
    server declining to say: they establish no catch-all at all. On an origin that refuses clients
    at its own discretion - which this subject demonstrably is - one unlucky call out of the three
    would have credited it with a control it never exercised. That is the same defect the positive
    control exists to prevent, moved one request to the left, and it was introduced by the repair
    for the previous one.
    """
    claim = ControlClaim(
        subject_id="git:a/b", origin="https://example.test", control_path="/",
        absent_path="/no-such-path", protected_path="/.git/config", method="GET",
        expected_refusal=frozenset({404}),
        claimed_by="wrangler.toml, 'only the build output is published'",
    )
    state = classify(claim, OK, Response(status, "the edge declined"), Response(404, "not found"))
    assert state is ProbeState.INDISTINGUISHABLE_FROM_ABSENT, (
        f"a negative control answering {status} did not establish what this origin returns for a "
        "path that does not exist, so the subject's 404 cannot be read as a refusal. Reporting "
        "ENFORCED here credits a control that was never exercised."
    )


def test_an_unestablished_catch_all_also_blocks_an_accusation() -> None:
    """The veto is symmetric, and this half protects the subject rather than us.

    A 200 on the probed path means the path is served only if the origin does not answer 200 to
    everything. With the catch-all unestablished, a soft 404 has not been ruled out, and
    NOT_ENFORCED would be an accusation computed from a reading we failed to take.
    """
    state = classify(CLAIM, OK, Response(503, "the edge declined"), Response(200, "served a body"))
    assert state is ProbeState.INDISTINGUISHABLE_FROM_ABSENT


def test_a_soft_404_origin_yields_no_reading_in_either_direction() -> None:
    """An origin answering 2xx for paths that do not exist tells us nothing by answering 2xx here.

    Four ERC-8004 identities answered exactly this way in Q-M1 and were on their way to a human as
    businesses (L-23). Without this branch the probe would publish NOT_ENFORCED - an accusation
    computed from the subject's error page.
    """
    soft = Response(200, "single-page-app shell for any path")
    assert classify(CLAIM, OK, soft, Response(200, "served a body")) is (
        ProbeState.INDISTINGUISHABLE_FROM_ABSENT)


def test_no_answer_at_all_is_our_instrument_and_not_their_system() -> None:
    assert (classify(CLAIM, OK, GONE, Response(None, "tls handshake failed"))
            is ProbeState.TRANSPORT_FAILED)


def test_a_transport_may_not_hand_over_an_unnamed_failure() -> None:
    """`curl rc=35` was recorded as a reason once, and a number is not a reason (L-23)."""
    with pytest.raises(ValueError, match="NAMED reason"):
        Response(None, "   ")


def test_an_untestable_claim_is_refused_at_construction() -> None:
    """A claim that does not say what refusal looks like would make every reading DIVERGED - a
    verdict manufactured by the absence of the claim rather than measured against it."""
    with pytest.raises(ValueError, match="untestable"):
        ControlClaim(subject_id="git:a/b", origin="https://example.test", control_path="/",
                     absent_path="/no-such-path", protected_path="/x", method="GET",
                     expected_refusal=frozenset(), claimed_by="somewhere")


@pytest.mark.parametrize("status", [200, 204, 301, 302])
def test_a_claim_may_not_name_a_success_as_the_refusal_it_expects(status: int) -> None:
    """One field, written backwards, would turn an open path into a PASS.

    `classify` returns ENFORCED when the subject's status is in `expected_refusal`, so a claim that
    named 200 would report the exposure it exists to find as compliance. Until Fable asked, the only
    thing standing against it was a test pinning the single shipped instance - and a rule enforced
    by inspecting one caller is not enforced (L-7).
    """
    with pytest.raises(ValueError, match="written backwards"):
        ControlClaim(subject_id="git:a/b", origin="https://example.test", control_path="/",
                     absent_path="/no-such-path", protected_path="/x", method="GET",
                     expected_refusal=frozenset({status}), claimed_by="somewhere")


def test_a_claim_must_cite_where_the_subject_makes_it() -> None:
    with pytest.raises(ValueError, match="accusation"):
        ControlClaim(subject_id="git:a/b", origin="https://example.test", control_path="/",
                     absent_path="/no-such-path", protected_path="/x", method="GET",
                     expected_refusal=frozenset({401}), claimed_by="  ")


VERDICTS = {
    ProbeState.ENFORCED: "PASS",
    ProbeState.NOT_ENFORCED: "FAIL",
    ProbeState.DIVERGED: "FAIL",
    ProbeState.REFUSED_BY_MANDATE: "NOT_MEASURED",
    ProbeState.ORIGIN_UNREADABLE: "NOT_MEASURED",
    ProbeState.SUBJECT_DECLINED: "NOT_MEASURED",
    ProbeState.INDISTINGUISHABLE_FROM_ABSENT: "NOT_MEASURED",
    ProbeState.TRANSPORT_FAILED: "NOT_MEASURED",
}


def test_every_state_has_a_decided_verdict() -> None:
    """A state added without a verdict decision would inherit one from a fallthrough."""
    assert set(VERDICTS) == set(ProbeState)


@pytest.mark.parametrize("state", list(VERDICTS))
def test_the_verdict_is_computed_from_the_state_and_absences_never_fail_a_subject(
        state: ProbeState) -> None:
    """Invariant 2: PASS/FAIL is taken by code from a measured quantity, and invariant 1: an
    absence is a state of its own rather than the bottom of the scale."""
    from src.prober.prober import ProbeResult

    result = ProbeResult(state=state, claim=CLAIM, mandate_ref="m-0001")
    assert result.verdict() == VERDICTS[state]
    if VERDICTS[state] == "NOT_MEASURED":
        assert result.not_measured in (NotMeasured.CHECK_DID_NOT_RUN, NotMeasured.UNREADABLE)
    else:
        assert result.not_measured is None
