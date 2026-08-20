"""The Q-M1 step-2 survey must never let a failure to read count as evidence against a subject.

WHAT THESE TESTS ARE FOR. A filter measurement has one characteristic way of lying: a denominator
of "everything we drew" and a numerator of "everything that matched", with every identity we could
not read quietly joining the non-matchers. The result is a rate that looks measured, reads low,
and is partly a report on our own broken instruments. That is LAW-NOT-MEASURED (L-1) wearing
survey clothing, and in this run it would have been a large lie: 27 of 100 sampled identities were
unreadable, 20 of them behind a single host that serves no TLS certificate.

EACH TEST BELOW CAN FAIL, and the way to see that is to make the collapse the code refuses to
make: move `card_unreadable` into the `nothing_qualified` sum in `tally` and the first three fail.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("qm1s2", ROOT / "scripts" / "measure_qm1_step2.py")
qm1s2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qm1s2)


def rec(agent_id: int, state: str, label: str | None = None, parsed: bool | None = None) -> dict:
    r = {"id": agent_id, "state": state, "uri": "", "detail": "",
         "label": label or qm1s2.L_UNLABELLED, "rationale": ""}
    if parsed is not None:
        r["shape"] = {"parsed": parsed}
    return r


def test_an_unreadable_card_is_not_counted_against_the_subject() -> None:
    """The core of L-1: `unreadable` lands in `unknown`, never in `nothing_qualified`."""
    t = qm1s2.tally([rec(1, qm1s2.S_CARD_UNREADABLE), rec(2, qm1s2.S_RPC_UNREADABLE)])
    assert t["unknown"] == 2
    assert t["nothing_qualified"] == 0
    assert t["candidates"] == 0


def test_nothing_qualified_holds_only_what_was_actually_read() -> None:
    """The other half of the same law: a read-and-rejected identity is evidence, and is counted."""
    t = qm1s2.tally([rec(1, qm1s2.S_NO_REGISTRATION),
                     rec(2, qm1s2.S_TOKEN_ABSENT),
                     rec(3, qm1s2.S_CARD_READ, qm1s2.L_NOT_A_BUSINESS, parsed=True)])
    assert t["nothing_qualified"] == 3
    assert t["unknown"] == 0


def test_the_two_absences_never_collapse_into_one_number() -> None:
    """A sample of pure absence must still say WHICH absence, in two separate counts.

    If the two were summed anywhere upstream this passes trivially for the total and fails here,
    which is exactly the point: the total is not the quantity that carries the information.
    """
    records = [rec(i, qm1s2.S_CARD_UNREADABLE) for i in range(5)]
    records += [rec(10 + i, qm1s2.S_NO_REGISTRATION) for i in range(5)]
    t = qm1s2.tally(records)
    assert (t["unknown"], t["nothing_qualified"]) == (5, 5)


def test_a_collected_but_unclassified_card_is_unknown_and_not_a_rejection() -> None:
    """A card nobody has read yet is `unknown`. Treating it as a rejection would be a free 'no'."""
    t = qm1s2.tally([rec(1, qm1s2.S_CARD_READ, parsed=True)])
    assert t["unlabelled"] == 1
    assert t["unknown"] == 1
    assert t["nothing_qualified"] == 0


def test_a_state_the_report_cannot_classify_raises_instead_of_being_skipped() -> None:
    """A checker that walks past what it does not understand reports success on it (L-6)."""
    with pytest.raises(ValueError, match="unknown state"):
        qm1s2.tally([rec(1, "something_new")])


def test_a_soft_404_is_demoted_to_unreadable_and_never_to_not_a_business() -> None:
    """HTTP 200 with an HTML body is a failure to read, not a subject that failed to qualify."""
    records = [rec(1, qm1s2.S_CARD_READ, parsed=False), rec(2, qm1s2.S_CARD_READ, parsed=True)]
    qm1s2.apply_soft_404_rule(records)
    assert records[0]["state"] == qm1s2.S_CARD_UNREADABLE
    assert records[1]["state"] == qm1s2.S_CARD_READ
    assert qm1s2.tally(records)["nothing_qualified"] == 0


def test_the_states_partition_the_sample() -> None:
    """Counts that do not sum to the sample size mean a record was double-counted or dropped."""
    records = [rec(1, qm1s2.S_NO_REGISTRATION), rec(2, qm1s2.S_CARD_UNREADABLE),
               rec(3, qm1s2.S_CARD_READ, qm1s2.L_CANDIDATE, parsed=True)]
    t = qm1s2.tally(records)
    assert sum(t["counts"].values()) == t["n"] == len(records)


def test_the_committed_sample_is_the_one_the_published_number_was_read_from() -> None:
    """L-3 turned on our own evidence: the file in the repository must still say what we published.

    This is the test that fails if someone re-runs `--collect` and forgets to update the document,
    or edits the document without re-running. The published figure is zero candidates out of a
    hundred sampled identities, with twenty-seven unreadable.
    """
    records = qm1s2._load_records()
    qm1s2.apply_soft_404_rule(records)
    t = qm1s2.tally(records)
    assert t["n"] == qm1s2.SAMPLE_SIZE
    assert t["candidates"] == 0
    assert t["unknown"] == 27
    assert t["nothing_qualified"] == 73
    assert t["unlabelled"] == 0, "every resolved registration file must carry a hand label"


def test_the_evidence_can_see_the_field_the_contested_labels_turn_on() -> None:
    """`card_shape` must count `services`, or the evidence is blind exactly where it is disputed.

    The first version counted `endpoints` only when it was a list and never looked at `services`,
    so FREAK #923 (three services, declared as a dict) and Signalbound #5655 (twenty-two) both
    recorded as zero - in the committed file a third party checks, and biased towards the
    conclusion the document was drawing. An instrument that cannot see a quantity reporting it as
    zero is L-10; pointing it at our own evidence is worse than pointing it at the chain.
    """
    by_id = {r["id"]: r for r in qm1s2._load_records()}
    assert by_id[47258]["shape"]["services"] == 3
    assert by_id[50275]["shape"]["services"] == 22
    assert by_id[34187]["shape"]["capabilities"] == 8


def test_a_content_hash_is_not_a_host_and_neither_is_an_inline_document() -> None:
    """Both were counted as hosts once, inflating the operator picture with rows carrying none."""
    assert qm1s2.host_of("ipfs://QmTnaDpx") == "(content-addressed)"
    assert qm1s2.host_of('{"name":"x"}') == "(inline)"
    assert qm1s2.host_of("https://example.com/a.json") == "example.com"


def op(result: str, size: int | None) -> dict:
    return {"operator": "h", "from_agent_id": 1, "endpoint": "https://h/x",
            "result": result, "bytes": size}


def test_a_refusal_aimed_at_our_request_is_not_the_operators_silence() -> None:
    """The operator probe needs the same three-way split as the identity level, and lacked it.

    The first version counted `http 200` as live and let everything else fall into an unnamed
    remainder, so a POST-only endpoint queried with GET and a host that never replied both read as
    "this operator serves nothing". One of those was our own instrument: the card declared
    `"method": "POST"` in the same object we ignored.
    """
    assert qm1s2.operator_state(op("http 400", 185)) == qm1s2.OP_NOT_MEASURED
    assert qm1s2.operator_state(op("http 405", 12)) == qm1s2.OP_NOT_MEASURED
    assert qm1s2.operator_state(op("http 502", 40)) == qm1s2.OP_NOT_MEASURED
    assert qm1s2.operator_state(op("transport failure rc=56", None)) == qm1s2.OP_NOT_MEASURED
    # A 404 IS the operator answering that nothing is there - measured, and not the same state.
    assert qm1s2.operator_state(op("http 404", 9)) == qm1s2.OP_NO_ARTEFACT


def test_a_200_with_an_empty_body_is_not_an_artefact_at_the_operator_level_either() -> None:
    """`apply_soft_404_rule` learned this one phase earlier; the operator counter had unlearned it."""
    assert qm1s2.operator_state(op("http 200", 0)) == qm1s2.OP_NO_ARTEFACT
    assert qm1s2.operator_state(op("http 200", 1)) == qm1s2.OP_LIVE


def test_the_operator_states_partition_the_probes() -> None:
    probes = [op("http 200", 10), op("http 404", 3), op("http 400", 1), op("x", None)]
    counts = qm1s2.tally_operators(probes)
    assert sum(counts.values()) == len(probes)
    assert counts == {qm1s2.OP_LIVE: 1, qm1s2.OP_NO_ARTEFACT: 1, qm1s2.OP_NOT_MEASURED: 2}


def test_the_committed_operator_probe_is_the_one_the_published_number_was_read_from() -> None:
    """The operator figure reached the headline and PRODUCT.md with nothing pinning it (L-21).

    Without this, re-probing on a day one host is down would silently change what the document
    claims while the suite stayed green - which is the drift the identity-level pin already
    prevents for the other half of the same measurement.
    """
    data = json.loads(qm1s2.OPERATOR_FILE.read_text(encoding="utf-8"))
    ops = data["operators"]
    assert len(ops) == 4
    assert data["external_calls_used"] == 4, "the probe's own cost must be recomputable"
    counts = qm1s2.tally_operators(ops)
    assert counts[qm1s2.OP_LIVE] == 3
    assert counts[qm1s2.OP_NOT_MEASURED] == 1
    assert counts[qm1s2.OP_NO_ARTEFACT] == 0
    # No probe may point at one of the two named non-hosts.
    assert {"(inline)", "(content-addressed)"}.isdisjoint({o["operator"] for o in ops})


def test_an_endpoint_declaring_a_non_get_method_is_not_chosen_for_a_get_probe() -> None:
    """The selector picked a POST-only endpoint over a GET-able one in the same document."""
    card = {"capabilities": [{"endpoint": "https://h/post", "method": "POST"},
                             {"endpoint": "https://h/get", "method": "GET"}],
            "url": "https://h/page"}
    assert qm1s2._first_endpoint(card) == "https://h/get"
    # With only non-GET capabilities, the top-level `url` is what a GET is meant for.
    assert qm1s2._first_endpoint({"capabilities": [{"endpoint": "https://h/post",
                                                    "method": "POST"}],
                                  "url": "https://h/page"}) == "https://h/page"


def test_wilson_returns_both_tails_because_at_zero_only_one_of_them_moves() -> None:
    """At 0 successes the lower tail is identically 0 and carries no information; the upper does."""
    lo, hi = qm1s2.wilson_interval(0, 100)
    assert lo == 0.0
    assert 0.03 < hi < 0.04, "0 of 100 is consistent with a rate near 3.6%, not with zero"

    for successes in (0, 1, 5, 50, 100):
        low, high = qm1s2.wilson_interval(successes, 100)
        assert 0.0 <= low <= successes / 100 <= high <= 1.0

    with pytest.raises(ValueError):
        qm1s2.wilson_interval(0, 0)
