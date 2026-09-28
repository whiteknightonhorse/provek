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
from gltest.types import TransactionStatus

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


def test_url_reachable_goes_undetermined_against_an_unreachable_url():
    contract = load_fixture(deploy_provek_evidence_witness)
    # A `.invalid` host is a DNS failure: the validator's OWN `gl.nondet.web.get` call raises, so
    # `validator_fn` returns False without ever constructing a FAIL — see the contract's own
    # "CONSENSUS SEMANTICS" docstring. This is "nobody could observe the URL", not "the claim is
    # false": GenVM rotates leaders and the transaction never reaches ACCEPTED, no `WitnessResult`
    # is written. Ask for UNDETERMINED explicitly (default `transact()` targets ACCEPTED, and
    # `wait_for_transaction_receipt` treats UNDETERMINED as an already-decided match for that
    # target too, which would let a wrongly-ACCEPTED transaction slip past unnoticed here).
    receipt = contract.witness(
        "git:whiteknightonhorse/provek", "url_reachable", UNREACHABLE_URL, "",
    ).transact(wait_transaction_status=TransactionStatus.UNDETERMINED)
    assert not tx_execution_succeeded(receipt)


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
