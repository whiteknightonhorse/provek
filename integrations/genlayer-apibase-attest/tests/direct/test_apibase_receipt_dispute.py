"""Direct-mode tests for `ApibaseReceiptDispute` (claim `upstream_failed_but_billed`) — no network.

The only web call is the receipt GET, mocked with `direct_vm.mock_web()`. As in the attest suite,
direct mode writes the LEADER's result to state with no simulated vote, so the validator is tested
afterwards through `direct_vm.run_validator()` with swapped mocks or a forged leader observation.
"""
import ast
import copy
import hashlib
import json
import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
# Same values as `conftest.py` (a conftest is not importable from a test module without a package).
RECEIPT_BASE_URL = "https://receipts.example/r/"
RECEIPT_ID = "ab" * 16
RECEIPT_URL = f"{RECEIPT_BASE_URL}{RECEIPT_ID}.json"
CONTRACTS = Path(__file__).resolve().parent.parent.parent / "contracts"
SHA = "ab" * 32


def _receipt(**changes):
    receipt = json.loads((FIXTURES / "receipt_pass.json").read_text(encoding="utf-8"))
    receipt.update(billed=True, upstream_status=503)
    receipt.update(changes)
    return receipt


def _world(direct_vm, receipt=None, status=200, body=None):
    receipt = _receipt() if receipt is None else receipt
    direct_vm.mock_web(re.escape(RECEIPT_URL),
                       {"status": status, "body": json.dumps(receipt) if body is None else body})


def _dispute(contract, receipt_id=RECEIPT_ID):
    return contract.get_dispute(contract.dispute_receipt(receipt_id))


# --- verdicts ----------------------------------------------------------------------------------

def test_refund_on_a_billed_503(direct_vm, receipt_dispute_contract):
    _world(direct_vm)
    record = _dispute(receipt_dispute_contract)
    assert (record.verdict, record.reason) == ("REFUND", "upstream_failed_but_billed")
    assert record.claim == "upstream_failed_but_billed"
    assert record.receipt_id == RECEIPT_ID
    assert record.payer == "0x688130810f0bede38742b66e7a443274c01d4213"
    assert record.payee == "0x781dfd3f2687f8e5656313b2179fdefdf99d339d"
    assert record.amount_atomic == "1000000"
    assert record.chain_id == "8453"
    assert (record.policy_version, record.policy_sha256) == ("refund-policy-1", SHA)
    assert record.evidence_sha256 == hashlib.sha256(json.dumps(_receipt()).encode()).hexdigest()
    assert re.fullmatch(r"0x[0-9a-fA-F]{40}", record.requester)


def test_release_when_not_billed(direct_vm, receipt_dispute_contract):
    _world(direct_vm, _receipt(billed=False))
    record = _dispute(receipt_dispute_contract)
    assert (record.verdict, record.reason) == ("RELEASE", "not_billed")


def test_release_when_upstream_succeeded(direct_vm, receipt_dispute_contract):
    _world(direct_vm, _receipt(upstream_status=200))
    record = _dispute(receipt_dispute_contract)
    assert (record.verdict, record.reason) == ("RELEASE", "upstream_status_200")


def test_499_is_released_and_500_is_refunded(direct_vm, receipt_dispute_contract, direct_alice):
    _world(direct_vm, _receipt(upstream_status=499))
    assert _dispute(receipt_dispute_contract).reason == "upstream_status_499"
    direct_vm.clear_mocks()
    _world(direct_vm, _receipt(upstream_status=500))
    with direct_vm.prank(direct_alice):  # a second sender: the same sender would repeat the dispute_id
        assert _dispute(receipt_dispute_contract).verdict == "REFUND"


def test_second_refund_on_the_same_payment_is_released(direct_vm, receipt_dispute_contract, direct_alice):
    _world(direct_vm)
    first = receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    with direct_vm.prank(direct_alice):
        second = _dispute(receipt_dispute_contract)
    assert (second.verdict, second.reason) == ("RELEASE", f"refund_verdict_exists:{first}")


# --- reverts that write nothing ------------------------------------------------------------------

def test_receipt_404_reverts(direct_vm, receipt_dispute_contract):
    _world(direct_vm, status=404, body="not found")
    with direct_vm.expect_revert("not readable"):
        receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    assert json.loads(receipt_dispute_contract.list_recent()) == []


def test_unreachable_receipt_reverts(direct_vm, receipt_dispute_contract):
    with direct_vm.expect_revert("not readable"):
        receipt_dispute_contract.dispute_receipt(RECEIPT_ID)


def test_unsupported_rail_reverts(direct_vm, receipt_dispute_contract):
    _world(direct_vm, _receipt(rail="mpp-tempo"))
    with direct_vm.expect_revert("unsupported rail"):
        receipt_dispute_contract.dispute_receipt(RECEIPT_ID)


@pytest.mark.parametrize("key", ["schema", "payment_tx", "payer", "amount_atomic", "response_sha256", "upstream_status"])
def test_malformed_receipt_reverts_naming_the_key(direct_vm, receipt_dispute_contract, key):
    _world(direct_vm, _receipt(**{key: "garbage" if key != "upstream_status" else "503"}))
    with direct_vm.expect_revert(f"malformed receipt: {key}"):
        receipt_dispute_contract.dispute_receipt(RECEIPT_ID)


def test_policy_unset_reverts(direct_vm, deploy_receipt_dispute_contract):
    _world(direct_vm)
    with direct_vm.expect_revert("refund policy not published"):
        deploy_receipt_dispute_contract().dispute_receipt(RECEIPT_ID)


@pytest.mark.parametrize("bad_id", ["AB" * 16, "ab" * 8, "zz" * 16, "ab" * 33, ""])
def test_bad_receipt_id_reverts(direct_vm, receipt_dispute_contract, bad_id):
    with direct_vm.expect_revert("receipt_id must be 32-64 lowercase hex characters"):
        receipt_dispute_contract.dispute_receipt(bad_id)


def test_duplicate_dispute_id_reverts(direct_vm, receipt_dispute_contract):
    _world(direct_vm)
    receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    with direct_vm.expect_revert("duplicate dispute_id"):
        receipt_dispute_contract.dispute_receipt(RECEIPT_ID)


# --- permissions, state, reads -----------------------------------------------------------------

def test_dispute_is_permissionless(direct_vm, receipt_dispute_contract, direct_alice):
    _world(direct_vm)
    with direct_vm.prank(direct_alice):
        assert _dispute(receipt_dispute_contract).verdict == "REFUND"


def test_set_policy_is_operator_only(direct_vm, deploy_receipt_dispute_contract, direct_alice):
    contract = deploy_receipt_dispute_contract()
    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("only the operator may publish the refund policy"):
            contract.set_policy("v1", SHA)


@pytest.mark.parametrize("version,sha", [("", SHA), ("x" * 33, SHA), ("v1", "zz" * 32), ("v1", "ab" * 31)])
def test_set_policy_validates(direct_vm, deploy_receipt_dispute_contract, version, sha):
    with direct_vm.expect_revert("policy"):
        deploy_receipt_dispute_contract().set_policy(version, sha)


def test_get_config_and_unknown_dispute(direct_vm, receipt_dispute_contract):
    config = json.loads(receipt_dispute_contract.get_config())
    assert config["receipt_base_url"] == RECEIPT_BASE_URL
    assert (config["policy_version"], config["policy_sha256"]) == ("refund-policy-1", SHA)
    assert "chains" not in config
    with direct_vm.expect_revert("unknown dispute_id"):
        receipt_dispute_contract.get_dispute("0" * 64)


def test_list_by_subject_both_keys_and_recent_order(direct_vm, receipt_dispute_contract, direct_alice):
    _world(direct_vm)
    first = receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    with direct_vm.prank(direct_alice):
        second = receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    tx = _receipt()["payment_tx"]
    assert json.loads(receipt_dispute_contract.list_by_subject(RECEIPT_ID)) == [first, second]
    assert json.loads(receipt_dispute_contract.list_by_subject(tx)) == [first, second]
    assert json.loads(receipt_dispute_contract.list_recent()) == [first, second]
    assert json.loads(receipt_dispute_contract.list_by_subject("cd" * 16)) == []


def test_list_recent_keeps_the_last_200(direct_vm, receipt_dispute_contract, receipt_dispute_module):
    contract = receipt_dispute_contract
    contract.recent = json.dumps([f"id{i}" for i in range(200)])
    _world(direct_vm)
    new = contract.dispute_receipt(RECEIPT_ID)
    recent = json.loads(contract.list_recent())
    assert len(recent) == 200 and recent[-1] == new and recent[0] == "id1"


# --- validator, via direct_vm.run_validator() ----------------------------------------------------

def _leader_observation(direct_vm):
    return copy.deepcopy(direct_vm._captured_validators[-1][0])


def test_validator_agrees_in_the_same_world(direct_vm, receipt_dispute_contract):
    _world(direct_vm)
    receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    assert direct_vm.run_validator() is True
    assert direct_vm.run_validator(leader_result=_leader_observation(direct_vm)) is True


def test_validator_disagrees_when_the_receipt_changes(direct_vm, receipt_dispute_contract):
    _world(direct_vm)
    receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    direct_vm.clear_mocks()
    _world(direct_vm, _receipt(tool="some.other.tool"))
    assert direct_vm.run_validator() is False


def test_validator_returns_false_when_its_own_fetch_raises(direct_vm, receipt_dispute_contract):
    _world(direct_vm)
    receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    direct_vm.clear_mocks()
    assert direct_vm.run_validator() is False


def test_validator_rejects_a_malformed_leader_result(direct_vm, receipt_dispute_contract):
    _world(direct_vm)
    receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    assert direct_vm.run_validator(leader_result="not-an-observation") is False
    assert direct_vm.run_validator(leader_result={"fetch": "ok"}) is False
    assert direct_vm.run_validator(leader_error=RuntimeError("leader blew up")) is False


@pytest.mark.parametrize("forge", [
    lambda o: o["receipt"].update(upstream_status=200),
    lambda o: o["receipt"].update(billed=False),
    lambda o: o["receipt"].update(payer="0x" + "ee" * 20),
    lambda o: o.update(receipt_sha256="00" * 32),
], ids=["upstream_status", "billed", "payer", "sha"])
def test_forged_leader_observation_is_rejected(direct_vm, receipt_dispute_contract, forge):
    _world(direct_vm)
    receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    forged = _leader_observation(direct_vm)
    forge(forged)
    assert direct_vm.run_validator(leader_result=forged) is False


def test_a_forged_receipt_with_the_true_sha_is_rejected(direct_vm, receipt_dispute_contract):
    _world(direct_vm)
    receipt_dispute_contract.dispute_receipt(RECEIPT_ID)
    forged = _leader_observation(direct_vm)
    forged["receipt"]["amount_atomic"] = "999999999"  # sha of the real body kept: still not equal
    assert direct_vm.run_validator(leader_result=forged) is False


# --- structure ---------------------------------------------------------------------------------

def test_module_docstring_and_public_methods():
    tree = ast.parse((CONTRACTS / "apibase_receipt_dispute.py").read_text(encoding="utf-8"))
    doc = ast.get_docstring(tree)
    assert doc, "module docstring missing"
    assert len(doc.encode("utf-8")) <= 600 and len(doc.splitlines()) <= 8
    for needle in ("apibase.pro/r/", "Base", "README"):
        assert needle in doc, needle
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ApibaseReceiptDispute")
    public = [n for n in cls.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
    assert sorted(n.name for n in public) == ["dispute_receipt", "get_config", "get_dispute",
                                              "list_by_subject", "list_recent", "set_policy"]
    for fn in public:
        text = ast.get_docstring(fn)
        assert text and len(text.encode("utf-8")) <= 100, (fn.name, text)


def test_receipt_dispute_header_names_the_babwp_runner():
    head = (CONTRACTS / "apibase_receipt_dispute.py").read_text(encoding="utf-8").splitlines()[:2]
    assert head == ["# v0.3.0",
                    '# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }']
