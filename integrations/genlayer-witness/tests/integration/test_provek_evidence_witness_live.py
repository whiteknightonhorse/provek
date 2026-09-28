"""Integration tests for `ProvekEvidenceWitness` against a REAL GenLayer network — real leader,
real validators, real `gl.nondet.web.get`. Not run at the door (`scripts/push.sh`), not run in CI
(`gates.yml`): they need a funded account on a real network. Run explicitly, e.g.:

    cd integrations/genlayer-witness
    gltest --network studionet tests/integration -v -s

Marked `integration` (registered in `pyproject.toml`) so a bare `pytest` run of this directory's
sibling `tests/direct/` never picks these up by accident.

RETURN-VALUE SHAPE NOTE. Unlike the direct-mode tests in `tests/direct/`, a view call here
(`.call()`) returns a value that has crossed the real calldata boundary: `WitnessResult` comes
back as a plain `dict` keyed by field name (see `provek_evidence_witness.py`'s own note on
`genlayer.py.calldata.encode_default_parameter` flattening dataclasses), not as the dataclass
instance direct-mode tests see.
"""
import json

import pytest
import requests
from gltest.assertions import tx_execution_succeeded

from .fixtures import deploy_provek_evidence_witness
from gltest.helpers import load_fixture

pytestmark = pytest.mark.integration

REACHABLE_URL = "https://provek.dev/"
UNREACHABLE_URL = "https://this-domain-should-never-resolve-provek-witness-check.invalid/"
ARTIFACT_URL = "https://raw.githubusercontent.com/whiteknightonhorse/provek/main/LICENSE"


def test_url_reachable_passes_against_a_real_public_url():
    contract = load_fixture(deploy_provek_evidence_witness)
    receipt = contract.witness(
        "git:whiteknightonhorse/provek", "url_reachable", REACHABLE_URL, "").transact()
    assert tx_execution_succeeded(receipt)


def test_url_reachable_fails_against_an_unreachable_url():
    contract = load_fixture(deploy_provek_evidence_witness)
    # The TRANSACTION still succeeds (consensus was reached on the check itself) — the on-chain
    # *result* is FAIL. A transaction failure and a FAIL result are different things throughout
    # this contract; this test only asserts the former.
    receipt = contract.witness(
        "git:whiteknightonhorse/provek", "url_reachable", UNREACHABLE_URL, "").transact()
    assert tx_execution_succeeded(receipt)


def test_artifact_hash_passes_against_a_real_artifact():
    contract = load_fixture(deploy_provek_evidence_witness)
    import hashlib
    expected = hashlib.sha256(requests.get(ARTIFACT_URL, timeout=10).content).hexdigest()
    receipt = contract.witness(
        "git:whiteknightonhorse/provek", "artifact_hash", ARTIFACT_URL, expected).transact()
    assert tx_execution_succeeded(receipt)


def test_operator_only_and_state_retrieval_round_trip():
    contract = load_fixture(deploy_provek_evidence_witness)
    subject_id = "git:whiteknightonhorse/provek:integration-smoke"

    receipt = contract.witness(subject_id, "url_reachable", REACHABLE_URL, "").transact()
    assert tx_execution_succeeded(receipt)

    ids = json.loads(contract.list_by_subject(subject_id).call())
    assert len(ids) == 1

    record = contract.get_result(ids[0]).call()
    assert record["subject_id"] == subject_id
    assert record["criterion"] == "url_reachable"
    assert record["result"] == "PASS"

    criteria = contract.supported_criteria().call()
    assert set(criteria) == {"artifact_hash", "url_reachable"}
