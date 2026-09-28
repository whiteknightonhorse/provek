"""Direct-mode tests for `ProvekEvidenceWitness` — no real GenVM WASM boundary, no network.

Every test runs against `direct_vm.mock_web()` (per the design ruling: the whole acceptance list
goes through `mock_web`). `direct_deploy`'s monkey-patched `run_nondet_unsafe` (see `GL-harness-notes.md #4`
and `gltest/direct/loader.py:_patch_run_nondet_for_direct_mode`) calls `leader_fn()` directly and
records `(result, leader_fn, validator_fn)` on `direct_vm._captured_validators` — the contract's
own state write always reflects the leader's result in direct mode (there is no simulated
consensus vote gating it), so the validator's actual agree/disagree behaviour is tested
separately, after the fact, via `direct_vm.run_validator()`.
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "digest_golden.json"

ARTIFACT_URL = "https://example.com/artifact.bin"
ARTIFACT_BODY = b"provek evidence witness fixture body"
ARTIFACT_SHA256 = hashlib.sha256(ARTIFACT_BODY).hexdigest()

REACHABLE_URL = "https://example.com/reachable"
SUBJECT = "git:whiteknightonhorse/provek"


def _url_pattern(url: str) -> str:
    return re.escape(url)


# --------------------------------------------------------------------------------------------
# artifact_hash
# --------------------------------------------------------------------------------------------

def test_valid_artifact_passes(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": ARTIFACT_BODY.decode()})
    wid = witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, ARTIFACT_SHA256)
    record = witness_contract.get_result(wid)
    assert record.result == "PASS"
    assert record.observation == "status=200"
    assert record.evidence_digest == ARTIFACT_SHA256


def test_unreachable_artifact_fails(direct_vm, witness_contract):
    # Deliberately no mock registered for this URL: `gl.nondet.web.get` raises
    # `MockNotFoundError` inside `leader_fn`'s own gl.nondet.web.get(url) call, caught and normalized
    # to `fetch="error"` — this is what "the fetch attempt itself failed" looks like here.
    wid = witness_contract.witness(SUBJECT, "artifact_hash", "https://example.com/gone", "0" * 64)
    record = witness_contract.get_result(wid)
    assert record.result == "FAIL"
    assert record.observation == "unreachable"


def test_wrong_hash_fails(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": ARTIFACT_BODY.decode()})
    wrong = "0" * 64
    wid = witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, wrong)
    record = witness_contract.get_result(wid)
    assert record.result == "FAIL"
    assert record.observation == "sha256 mismatch"
    # The digest published is still the REAL fetched body's hash, not the caller's wrong claim —
    # a third party can verify the FAIL was legitimate.
    assert record.evidence_digest == ARTIFACT_SHA256


def test_non_2xx_status_is_a_fail_observation_not_an_exception(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 503, "body": ""})
    wid = witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, "0" * 64)
    record = witness_contract.get_result(wid)
    assert record.result == "FAIL"
    assert record.observation == "status=503"


def test_body_over_cap_fails(direct_vm, contract_module, witness_contract):
    big_body = "a" * (contract_module.MAX_ARTIFACT_BYTES + 1)
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": big_body})
    wid = witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, ARTIFACT_SHA256)
    record = witness_contract.get_result(wid)
    assert record.result == "FAIL"
    assert record.observation == "too_large"


# --------------------------------------------------------------------------------------------
# url_reachable
# --------------------------------------------------------------------------------------------

def test_url_reachable_passes_on_2xx(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(REACHABLE_URL), {"status": 200, "body": ""})
    wid = witness_contract.witness(SUBJECT, "url_reachable", REACHABLE_URL, "")
    record = witness_contract.get_result(wid)
    assert record.result == "PASS"
    assert record.observation == "status=200"


def test_url_reachable_fails_on_404(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(REACHABLE_URL), {"status": 404, "body": ""})
    wid = witness_contract.witness(SUBJECT, "url_reachable", REACHABLE_URL, "")
    record = witness_contract.get_result(wid)
    assert record.result == "FAIL"
    assert record.observation == "status=404"


# --------------------------------------------------------------------------------------------
# deterministic, pre-consensus rejections (revert, no record written)
# --------------------------------------------------------------------------------------------

def test_unknown_criterion_reverts(direct_vm, witness_contract):
    with direct_vm.expect_revert("unsupported criterion"):
        witness_contract.witness(SUBJECT, "body_contains", REACHABLE_URL, "")


@pytest.mark.parametrize("bad_url", [
    "example.com/no-scheme",                      # 1. no scheme
    "https:///no-host",                            # 2. no host
    "https://user:pass@example.com/",               # 3. userinfo
    "https://example.com/has space",                # 4. whitespace
    "https://example.com/" + "a" * 2048,            # 5. over length (>2048 total)
])
def test_malformed_url_reverts(direct_vm, witness_contract, bad_url):
    with direct_vm.expect_revert():
        witness_contract.witness(SUBJECT, "url_reachable", bad_url, "")


def test_bad_expected_for_artifact_hash_reverts(direct_vm, witness_contract):
    with direct_vm.expect_revert("64-character hex sha256"):
        witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, "not-a-hash")


def test_nonempty_expected_for_url_reachable_reverts(direct_vm, witness_contract):
    with direct_vm.expect_revert("does not take an `expected`"):
        witness_contract.witness(SUBJECT, "url_reachable", REACHABLE_URL, "unexpected")


def test_duplicate_witness_id_reverts(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(REACHABLE_URL), {"status": 200, "body": ""})
    witness_contract.witness(SUBJECT, "url_reachable", REACHABLE_URL, "")
    # Same subject/criterion/url/expected/sender AND the same VM datetime (unchanged since the
    # first call) => the exact same deterministic witness_id => must revert as a duplicate.
    with direct_vm.expect_revert("duplicate witness_id"):
        witness_contract.witness(SUBJECT, "url_reachable", REACHABLE_URL, "")


def test_non_operator_sender_reverts(direct_vm, witness_contract, direct_alice):
    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("only the operator"):
            witness_contract.witness(SUBJECT, "url_reachable", REACHABLE_URL, "")


# --------------------------------------------------------------------------------------------
# state and reads
# --------------------------------------------------------------------------------------------

def test_get_result_matches_what_was_written(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": ARTIFACT_BODY.decode()})
    wid = witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, ARTIFACT_SHA256)
    record = witness_contract.get_result(wid)
    assert record.subject_id == SUBJECT
    assert record.criterion == "artifact_hash"
    assert record.evidence_url == ARTIFACT_URL
    assert record.expected == ARTIFACT_SHA256
    assert record.result == "PASS"


def test_get_result_unknown_id_raises(direct_vm, witness_contract):
    with pytest.raises(Exception):
        witness_contract.get_result("0" * 64)


def test_list_by_subject_preserves_order(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(REACHABLE_URL), {"status": 200, "body": ""})
    first = witness_contract.witness(SUBJECT, "url_reachable", REACHABLE_URL, "")
    direct_vm.warp("2026-02-02T00:00:00Z")
    second_url = REACHABLE_URL + "/2"
    direct_vm.mock_web(_url_pattern(second_url), {"status": 200, "body": ""})
    second = witness_contract.witness(SUBJECT, "url_reachable", second_url, "")

    ids = json.loads(witness_contract.list_by_subject(SUBJECT))
    assert ids == [first, second]


def test_list_by_subject_unknown_subject_is_empty(direct_vm, witness_contract):
    assert json.loads(witness_contract.list_by_subject("git:nobody/asked")) == []


def test_supported_criteria(direct_vm, witness_contract):
    assert set(witness_contract.supported_criteria()) == {"artifact_hash", "url_reachable"}


def test_checked_at_is_the_tx_datetime_not_merely_nonempty(direct_vm, deploy_witness_contract):
    # warp() BEFORE deploy: this direct-mode harness captures gl.message_raw once, at
    # deploy/import time (see deploy_witness_contract's docstring) — warping an
    # already-deployed instance's VM would have no visible effect on it.
    direct_vm.warp("2026-03-01T00:00:00Z")
    contract = deploy_witness_contract()
    direct_vm.mock_web(_url_pattern(REACHABLE_URL), {"status": 200, "body": ""})
    wid = contract.witness(SUBJECT, "url_reachable", REACHABLE_URL, "")
    record = contract.get_result(wid)
    assert record.checked_at == "2026-03-01T00:00:00Z"


# --------------------------------------------------------------------------------------------
# validator behaviour, exercised via direct_vm.run_validator()
# --------------------------------------------------------------------------------------------

def test_validator_agrees_in_the_same_world(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": ARTIFACT_BODY.decode()})
    witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, ARTIFACT_SHA256)
    assert direct_vm.run_validator() is True


def test_validator_disagrees_in_a_different_world(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": ARTIFACT_BODY.decode()})
    witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, ARTIFACT_SHA256)

    # Swap the mock so the validator's OWN fetch sees different bytes than the leader saw.
    direct_vm.clear_mocks()
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": "a different body entirely"})
    assert direct_vm.run_validator() is False


def test_validator_returns_false_when_its_own_fetch_raises(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": ARTIFACT_BODY.decode()})
    witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, ARTIFACT_SHA256)

    # No mock left at all: the validator's own gl.nondet.web.get(url) call raises
    # `MockNotFoundError`, caught explicitly by `validator_fn`, which returns False rather than
    # letting the exception propagate — "could not observe", not "observed false".
    direct_vm.clear_mocks()
    assert direct_vm.run_validator() is False


def test_validator_rejects_a_malformed_leader_result(direct_vm, witness_contract):
    direct_vm.mock_web(_url_pattern(ARTIFACT_URL), {"status": 200, "body": ARTIFACT_BODY.decode()})
    witness_contract.witness(SUBJECT, "artifact_hash", ARTIFACT_URL, ARTIFACT_SHA256)

    # Not a dict at all -> validator_fn's isinstance(observation, dict) check rejects it before
    # ever attempting its own fetch.
    assert direct_vm.run_validator(leader_result="not-a-well-formed-observation") is False
    # A VMError/UserError leader result (not a Return) is rejected the same way.
    assert direct_vm.run_validator(leader_error=RuntimeError("leader blew up")) is False


# --------------------------------------------------------------------------------------------
# golden vector — the ONE digest formula shared byte-for-byte with `src.witness.witness._digest`
# --------------------------------------------------------------------------------------------

def test_url_reachable_digest_matches_golden_vector(contract_module):
    vectors = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert len(vectors) > 0
    for vector in vectors:
        computed = contract_module._url_reachable_digest(
            vector["url"], vector["result"], vector["checked_at"])
        assert computed == vector["digest"], vector
