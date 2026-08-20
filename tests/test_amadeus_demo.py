"""T-2.16 - the Amadeus demo's classifier, exercised through injected artefacts.

NO SOCKET IS OPENED HERE AND NOTHING SKIPS. The live run belongs to `scripts/amadeus_demo.py`;
what is tested here is the law it applies, which is the half that can be wrong silently. Every
test below fails if the corresponding branch is broken - in particular the shape tests, which
guard the one behaviour this demo was built around: a 200 whose body is not this chain's shape
must never become a number.
"""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

from src.abs_profile.measured import NotMeasured
from src.amadeus.demo_audit import (
    ABSENCE,
    DEFECT_EXIT,
    DemoVerdict,
    ReadingState,
    SdkFinding,
    classify_control,
    classify_reading,
    judge,
)

# A REDUCED RECONSTRUCTION of the CKAN package_search envelope observed on 2026-08-20 - the same
# stand-in `auditor.mjs` serves from its local socket, NOT the captured bytes. Only the leading
# ~400 characters were ever retained; see `evidence/AMADEUS-RPC-ANOMALY-001.txt`. A draft of this
# comment said "the body actually observed", which claimed a capture that does not exist while
# the JavaScript two directories away called the same object a stand-in. Found by Fable.
FOREIGN_BODY = {
    "help": "https://ckan.opendata.swiss/api/3/action/help_show?name=package_search",
    "success": True,
    "result": {"count": 188, "facets": {}, "results": [{"name": "not-a-chain-entry"}]},
}

HEIGHT = 80355720


def reading(endpoint="chain.getTip", transport="answered", body=None, status=200, error=None):
    return {"endpoint": endpoint, "transport": transport, "http_status": status,
            "error": error, "body": body}


def tip_body(height=HEIGHT):
    return {"entry": {"header": {"height": height, "slot": height}}}


def artefact(**over):
    """A well-formed artefact of the shape `auditor.mjs` emits. Tests mutate one thing at a time."""
    base = {
        "sdk": {"package": "@amadeus-protocol/sdk", "pinned_version": "1.2.0",
                "reported_version": "1.2.0"},
        "network": {"name": "mainnet", "rpc_url": "https://mainnet-rpc.ama.one/api"},
        "readings": [
            reading("chain.getTip", body=tip_body()),
            reading("chain.getStats", body={"stats": {"height": HEIGHT}}),
            reading("chain.getKpi", body={"kpi": {"block_time": 500}}),
        ],
        "foreign_payload_control": {"performed": True, "sdk_threw": False, "height_seen": None,
                                    "served": FOREIGN_BODY, "returned": FOREIGN_BODY,
                                    "error": None},
        "self_audit": {"loaded": True, "path": "public/passports/x.json", "sha256": "ab" * 32,
                       "subject_id": "git:whiteknightonhorse/provek", "projection": 80,
                       "error": None},
        "anchor": {"present": True, "network": "mainnet", "height": HEIGHT, "slot": HEIGHT},
        "payload": {"built": True, "base58": "CnGx...", "sha256": "cd" * 32, "byte_length": 469},
        "onchain_write": {"attempted": False, "state": "check_did_not_run",
                          "blockers": ["no signing key", "no AMA"]},
    }
    base.update(over)
    return base


# --------------------------------------------------------------------------------------------
# The reading classifier: `answered` and `measured` are different states.
# --------------------------------------------------------------------------------------------

def test_a_well_shaped_tip_is_measured():
    r = classify_reading(reading(body=tip_body()))
    assert r.state is ReadingState.MEASURED
    assert r.value.is_measured and r.value.value == HEIGHT


def test_the_foreign_200_is_unreadable_and_carries_no_number():
    """THE TEST THIS DEMO EXISTS FOR. The SDK returns this body as the chain tip; the classifier
    must refuse to read a height out of it, and must not substitute a zero."""
    r = classify_reading(reading(body=FOREIGN_BODY))
    assert r.state is ReadingState.SHAPE_UNRECOGNISED
    assert not r.value.is_measured
    assert r.value.absent is NotMeasured.UNREADABLE
    assert r.value.value is None


@pytest.mark.parametrize("body", [
    None,                                   # answered with nothing
    {},                                     # answered with an empty object
    {"entry": {}},                          # right outer key, no header
    {"entry": {"header": {}}},              # right header, no height
    {"entry": {"header": {"height": None}}},   # the field exists and is null
    {"entry": {"header": {"height": "80355720"}}},  # a height as a string
    {"entry": {"header": {"height": 80355720.5}}},  # a float
])
def test_near_misses_are_unreadable_rather_than_measured(body):
    r = classify_reading(reading(body=body))
    assert r.state is ReadingState.SHAPE_UNRECOGNISED, body
    assert not r.value.is_measured


def test_a_boolean_height_is_not_a_height():
    """`bool` is a subclass of `int`, so `True` passes a naive isinstance check and would be
    recorded as a height of 1. It is not a height."""
    r = classify_reading(reading(body={"entry": {"header": {"height": True}}}))
    assert r.state is ReadingState.SHAPE_UNRECOGNISED


def test_zero_is_a_legitimate_height_and_is_measured():
    """The inverse error: a shape check that rejects falsy values would turn a real zero into an
    absence, which is invariant 1 with the sign flipped."""
    r = classify_reading(reading(body=tip_body(height=0)))
    assert r.state is ReadingState.MEASURED
    assert r.value.is_measured and r.value.value == 0


def test_transport_failures_keep_their_own_names():
    assert classify_reading(reading(transport="no_answer", body=None)).state is \
        ReadingState.NO_ANSWER
    assert classify_reading(reading(transport="source_declined", status=503)).state is \
        ReadingState.SOURCE_DECLINED
    assert classify_reading(reading(transport="something_new")).state is \
        ReadingState.CHECK_DID_NOT_RUN


def test_an_endpoint_with_no_declared_shape_is_not_silently_passed():
    """A classifier that walks past what it does not recognise reports success on what it never
    examined - but the request DID run, so this is UNREADABLE and not `check_did_not_run`.
    Merging "never ran" with "ran, and we cannot read it" is the collapse invariant 1 forbids."""
    r = classify_reading(reading(endpoint="chain.getSomethingElse", body={"x": 1}))
    assert r.state is ReadingState.NO_DECLARED_SHAPE
    assert r.value.absent is NotMeasured.UNREADABLE


def test_an_unknown_endpoint_that_never_answered_keeps_its_transport_state():
    """The inverse: no shape AND no answer must not be reported as though we looked at a body."""
    r = classify_reading(reading(endpoint="chain.getSomethingElse", transport="no_answer"))
    assert r.state is ReadingState.NO_ANSWER


def test_a_reading_with_no_endpoint_is_a_malformed_artefact():
    """REGRESSION from the NO_DECLARED_SHAPE fix: `str(None)` is `"None"`, which sailed past every
    branch and was reported as an unfamiliar endpoint. Our broken artefact must not wear the
    description of somebody else's new API."""
    r = classify_reading({"transport": "answered", "body": {"x": 1}})
    assert r.state is ReadingState.CHECK_DID_NOT_RUN
    assert r.value.absent is NotMeasured.CHECK_DID_NOT_RUN


def test_every_absent_state_has_an_entry_in_the_absence_table():
    """The table is the single definition of how a non-measurement maps onto the three absences.
    It was dead code for one round - every branch hardcoded its own - so it could drift from the
    classifier with no test noticing."""
    for state in ReadingState:
        if state is ReadingState.MEASURED:
            assert state not in ABSENCE, "a measured reading has no absence"
        else:
            assert state in ABSENCE, f"{state} has no declared absence"


def test_a_drifted_endpoint_list_is_a_defect_and_not_a_trailing_remark():
    """`READINGS` in auditor.mjs and `SHAPE` here are two copies of one list. An endpoint we
    requested and then could not read is our instrument gap, and it used to exit 0."""
    a = artefact()
    a["readings"] = [*a["readings"], reading("chain.getNewThing", body={"whatever": 1})]
    j = judge(a)
    assert j.verdict is DemoVerdict.DEFECT
    assert any("drifted apart" in f for f in j.findings)


# --------------------------------------------------------------------------------------------
# The instrument control.
# --------------------------------------------------------------------------------------------

def test_control_reports_the_sdk_accepting_an_unvalidated_response():
    finding, sentence = classify_control({"performed": True, "sdk_threw": False,
                                          "height_seen": None})
    assert finding is SdkFinding.ACCEPTS_UNVALIDATED
    assert "chain tip" in sentence


def test_control_is_able_to_report_the_finding_retired():
    """If a future SDK validates its responses this flips - which is what makes the control a
    measurement rather than a decoration."""
    finding, _ = classify_control({"performed": True, "sdk_threw": True})
    assert finding is SdkFinding.VALIDATES


def test_a_control_that_did_not_run_is_not_a_result_about_the_sdk():
    for c in ({"performed": False}, {"performed": True, "sdk_threw": None}, {}):
        assert classify_control(c)[0] is SdkFinding.CONTROL_DID_NOT_RUN


# --------------------------------------------------------------------------------------------
# The verdict.
# --------------------------------------------------------------------------------------------

def test_a_complete_run_is_demonstrated():
    j = judge(artefact())
    assert j.verdict is DemoVerdict.DEMONSTRATED
    assert j.exit_code == 0
    assert j.anchor_height.value == HEIGHT


def test_a_missing_top_level_key_is_our_defect_not_a_finding():
    a = artefact()
    del a["payload"]
    j = judge(a)
    assert j.verdict is DemoVerdict.DEFECT
    assert j.exit_code == DEFECT_EXIT


def test_our_bug_and_their_outage_do_not_share_an_exit_code():
    """The contract the README states in as many words. It was false for one round: both failing
    verdicts returned 1, and two tests asserted that wrong number rather than catching it."""
    broken = artefact()
    del broken["payload"]
    outage = artefact(readings=[reading("chain.getTip", transport="no_answer", status=None)],
                      anchor={"present": False, "absent_reason": "tip reading no_answer"})
    defect_code = judge(broken).exit_code
    outage_code = judge(outage).exit_code
    assert judge(artefact()).exit_code == 0
    assert defect_code != outage_code
    assert 0 not in (defect_code, outage_code)


def test_a_control_that_never_ran_cannot_go_out_as_a_demonstrated_run():
    """The headline finding is the control's. A run that could not bind a socket has not
    established it, and must not exit 0 carrying the README's claim."""
    j = judge(artefact(foreign_payload_control={"performed": False, "error": "no socket"}))
    assert j.sdk_finding is SdkFinding.CONTROL_DID_NOT_RUN
    assert j.verdict is DemoVerdict.NOT_DEMONSTRATED
    assert j.exit_code != 0


def test_an_unreachable_chain_is_not_demonstrated_and_is_not_a_defect():
    """Their RPC being down and us shipping a broken demo must not share an outcome."""
    a = artefact(readings=[reading("chain.getTip", transport="no_answer", body=None, status=None),
                           reading("chain.getStats", transport="no_answer", body=None,
                                   status=None),
                           reading("chain.getKpi", transport="no_answer", body=None, status=None)],
                 anchor={"present": False, "absent_reason": "tip reading no_answer"})
    j = judge(a)
    assert j.verdict is DemoVerdict.NOT_DEMONSTRATED
    assert j.exit_code == 1


def test_a_chain_answering_foreign_documents_is_not_demonstrated():
    """The whole run over the observed outage: three 200s, nothing measured, and the demo must
    say so rather than anchor an audit at a height it never read."""
    a = artefact(readings=[reading("chain.getTip", body=FOREIGN_BODY),
                           reading("chain.getStats", body=FOREIGN_BODY),
                           reading("chain.getKpi", body=FOREIGN_BODY)],
                 anchor={"present": False, "absent_reason": "tip answered but carries no integer "
                                                            "height"})
    j = judge(a)
    assert j.verdict is DemoVerdict.NOT_DEMONSTRATED
    assert any("shape_unrecognised" in f for f in j.findings)


def test_an_agent_that_invents_an_anchor_is_caught():
    """The cross-check over the language boundary: the agent claims a height the tip never gave."""
    a = artefact(readings=[reading("chain.getTip", body=FOREIGN_BODY)],
                 anchor={"present": True, "network": "mainnet", "height": 999, "slot": 999})
    j = judge(a)
    assert j.verdict is DemoVerdict.DEFECT
    assert any("disagree about the anchor" in f for f in j.findings)


def test_an_agent_that_drops_a_measured_anchor_is_caught_too():
    a = artefact(anchor={"present": False, "absent_reason": "invented"})
    assert judge(a).verdict is DemoVerdict.DEFECT


def test_a_disagreeing_height_is_caught_even_when_both_sides_claim_presence():
    a = artefact(anchor={"present": True, "network": "mainnet", "height": HEIGHT + 1,
                         "slot": HEIGHT})
    j = judge(a)
    assert j.verdict is DemoVerdict.DEFECT
    assert any("anchored at height" in f for f in j.findings)


def test_a_write_without_a_sentinel_is_a_defect():
    """A blocked step that leaves no named blocker is how 'cannot' becomes 'forgot'."""
    for write in ({"attempted": False, "state": "check_did_not_run", "blockers": []},
                  {"attempted": True, "state": "done", "blockers": ["x"]},
                  {}):
        assert judge(artefact(onchain_write=write)).verdict is DemoVerdict.DEFECT


def test_an_unread_self_audit_is_not_demonstrated():
    a = artefact(self_audit={"loaded": False, "error": "file missing", "path": "x",
                             "sha256": None, "subject_id": None, "projection": None})
    assert judge(a).verdict is DemoVerdict.NOT_DEMONSTRATED


def test_a_record_that_lost_a_passport_field_is_a_defect_not_a_null():
    """A bare null would read as "this field is legitimately empty". A passport missing its
    subject is not empty, it is malformed, and the record has to say which."""
    a = artefact(payload={"built": True, "base58": "CnGx...", "sha256": "cd" * 32,
                          "byte_length": 400,
                          "record": {"missing_fields": ["subject_id", "issued_at"]}})
    j = judge(a)
    assert j.verdict is DemoVerdict.DEFECT
    assert any("subject_id, issued_at" in f for f in j.findings)


def test_a_record_with_no_missing_fields_passes():
    a = artefact(payload={"built": True, "base58": "CnGx...", "sha256": "cd" * 32,
                          "byte_length": 469, "record": {"missing_fields": []}})
    assert judge(a).verdict is DemoVerdict.DEMONSTRATED


def test_a_payload_claiming_to_be_built_with_nothing_in_it_is_a_defect():
    assert judge(artefact(payload={"built": True, "base58": "", "sha256": None})).verdict \
        is DemoVerdict.DEFECT


def test_a_relative_out_path_does_not_crash_the_runner():
    """REGRESSION. `--out evidence/X` is the form the README documents, and the runner's bare
    `Path.relative_to(ROOT)` raised on it AFTER writing both files - a traceback exiting 1, the
    same code as `not_demonstrated`. The runner whose subject is keeping those apart could not
    keep its own crash apart from its own honest failure."""
    import importlib.util

    root = pathlib.Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location("ad", root / "scripts" / "amadeus_demo.py")
    ad = importlib.util.module_from_spec(spec)
    sys.modules["ad"] = ad
    spec.loader.exec_module(ad)

    assert ad._shown(pathlib.Path("evidence/X.json")) == "evidence/X.json"   # relative, inside
    assert ad._shown(root / "evidence" / "X.json") == "evidence/X.json"      # absolute, inside
    outside = ad._shown(pathlib.Path("/tmp/X.json"))                         # outside the repo
    assert outside.startswith("/") and "X.json" in outside


def test_the_judgement_does_not_mutate_what_it_was_given():
    """The runner stamps the artefact after judging; a classifier that edited it in passing would
    make the two orders produce different files."""
    a = artefact()
    before = copy.deepcopy(a)
    judge(a)
    assert a == before
