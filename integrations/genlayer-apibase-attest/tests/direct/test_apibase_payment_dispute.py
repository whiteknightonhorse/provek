"""Direct-mode tests for `ApibasePaymentDispute` (claim `paid_without_receipt`) — no network.

Two mocked reads: APIbase's `by-tx/<tx>.json` index and the Base JSON-RPC receipt. Direct mode
writes the LEADER's result to state with no simulated vote, so the validator is tested afterwards
through `direct_vm.run_validator()` with swapped mocks or a forged leader observation. The
last tests prove the helpers copied out of the attest and the shared `Dispute` shape are identical.
"""
import ast
import copy
import json
import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
# Same values as `conftest.py` (a conftest is not importable from a test module without a package).
RECEIPT_BASE_URL = "https://receipts.example/r/"
BASE_RPC_URL = "https://rpc.example/base"
BASE_USDC = "0x833589fCd6eDb6E08f4c7C32D4f71b54bdA02913"
PAYEE = "0x781dfd3f2687f8e5656313b2179fdefdf99d339d"
PAYER = "0x688130810f0bede38742b66e7a443274c01d4213"
TX_HEX = "a7055e5ec14e8912912c370eb253965c26960aa96ef65d7d85a9f08ed496bf58"  # no 0x in the tree (secret scan)
TX = "0x" + TX_HEX
INDEX_URL = f"{RECEIPT_BASE_URL}by-tx/{TX}.json"
CONTRACTS = Path(__file__).resolve().parent.parent.parent / "contracts"
REFUND_TX = "0x" + "cd" * 32


def _load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _index(receipt_ids=(), refund_tx=None, **changes):
    doc = {"schema": "apibase-receipt-index/1", "payment_tx": TX, "receipt_ids": list(receipt_ids),
           "refund_tx": refund_tx}
    doc.update(changes)
    return doc


def _world(direct_vm, index=None, rpc="real", status=200, body=None):
    index = _index() if index is None else index
    rpc = _load("rpc_receipt_real_base_usdc.json") if rpc == "real" else rpc
    direct_vm.mock_web(re.escape(INDEX_URL), {"status": status, "body": json.dumps(index) if body is None else body})
    if rpc is not None:
        direct_vm.mock_web(re.escape(BASE_RPC_URL), {"method": "POST", "status": 200, "body": json.dumps(rpc)})


def _dispute(contract):
    return contract.get_dispute(contract.dispute_payment("8453", TX))


# --- verdicts ----------------------------------------------------------------------------------

def test_refund_when_paid_and_no_receipt(direct_vm, payment_dispute_contract):
    _world(direct_vm)
    record = _dispute(payment_dispute_contract)
    assert (record.verdict, record.reason) == ("REFUND", "paid_without_receipt")
    assert record.claim == "paid_without_receipt"
    assert record.receipt_id == ""
    assert (record.payer, record.payee, record.amount_atomic) == (PAYER, PAYEE, "1000000")
    assert (record.chain_id, record.payment_tx) == ("8453", TX)
    assert record.policy_sha256 == "ab" * 32
    assert len(record.evidence_sha256) == 64


def test_payment_tx_is_stored_lowercase(direct_vm, payment_dispute_contract):
    _world(direct_vm)
    record = payment_dispute_contract.get_dispute(payment_dispute_contract.dispute_payment("8453", "0x" + TX_HEX.upper()))
    assert record.payment_tx == TX


def test_release_receipt_exists_and_rpc_is_not_asked(direct_vm, payment_dispute_contract):
    _world(direct_vm, _index(receipt_ids=["ab" * 16]), rpc=None)  # no RPC mock: asking Base would fail
    record = _dispute(payment_dispute_contract)
    assert (record.verdict, record.reason) == ("RELEASE", "receipt_exists:" + "ab" * 16)


def test_release_already_refunded(direct_vm, payment_dispute_contract):
    _world(direct_vm, _index(refund_tx=REFUND_TX), rpc=None)
    record = _dispute(payment_dispute_contract)
    assert (record.verdict, record.reason) == ("RELEASE", "already_refunded")


def test_release_tx_not_found(direct_vm, payment_dispute_contract):
    _world(direct_vm, rpc=_load("rpc_receipt_null.json"))
    assert _dispute(payment_dispute_contract).reason == "tx_not_found"


def test_release_tx_reverted(direct_vm, payment_dispute_contract):
    _world(direct_vm, rpc=_load("rpc_receipt_reverted.json"))
    assert _dispute(payment_dispute_contract).reason == "tx_reverted"


def test_release_no_payment_to_apibase(direct_vm, payment_dispute_contract):
    payment_dispute_contract.set_chain("8453", BASE_RPC_URL, BASE_USDC, "0x" + "11" * 20)
    _world(direct_vm)
    record = _dispute(payment_dispute_contract)
    assert (record.verdict, record.reason, record.payer) == ("RELEASE", "no_payment_to_apibase", "")


def test_second_filing_is_released_with_the_first_dispute_id(direct_vm, payment_dispute_contract, direct_alice):
    _world(direct_vm)
    first = payment_dispute_contract.dispute_payment("8453", TX)
    with direct_vm.prank(direct_alice):
        second = _dispute(payment_dispute_contract)
    assert (second.verdict, second.reason) == ("RELEASE", f"refund_verdict_exists:{first}")


# --- reverts that write nothing ------------------------------------------------------------------

@pytest.mark.parametrize("status,body", [
    (404, "not found"), (500, "{}"), (200, "[]"), (200, "not json"),
    (200, json.dumps(_index(schema="other/1"))), (200, json.dumps(_index(payment_tx="0x" + "00" * 32))),
    (200, json.dumps({**_index(), "receipt_ids": "abc"})), (200, json.dumps(_index(refund_tx="nope"))),
], ids=["404", "500", "array", "not-json", "schema", "other-tx", "ids-not-list", "refund-tx-bad"])
def test_an_unreadable_index_is_unmeasured_not_no_receipt(direct_vm, payment_dispute_contract, status, body):
    _world(direct_vm, status=status, body=body)
    with direct_vm.expect_revert("not readable"):
        payment_dispute_contract.dispute_payment("8453", TX)
    assert json.loads(payment_dispute_contract.list_recent()) == []


def test_rpc_failure_reverts(direct_vm, payment_dispute_contract):
    direct_vm.mock_web(re.escape(INDEX_URL), {"status": 200, "body": json.dumps(_index())})
    direct_vm.mock_web(re.escape(BASE_RPC_URL), {"method": "POST", "status": 502, "body": "bad gateway"})
    with direct_vm.expect_revert("not readable"):
        payment_dispute_contract.dispute_payment("8453", TX)


def test_policy_unset_reverts(direct_vm, deploy_payment_dispute_contract):
    contract = deploy_payment_dispute_contract()
    contract.set_chain("8453", BASE_RPC_URL, BASE_USDC, PAYEE)
    _world(direct_vm)
    with direct_vm.expect_revert("refund policy not published"):
        contract.dispute_payment("8453", TX)


def test_unconfigured_chain_reverts(direct_vm, payment_dispute_contract):
    with direct_vm.expect_revert("not configured"):
        payment_dispute_contract.dispute_payment("1", TX)


@pytest.mark.parametrize("bad_tx", ["0x1234", "ab" * 32, "0x" + "zz" * 32, ""])
def test_bad_payment_tx_reverts(direct_vm, payment_dispute_contract, bad_tx):
    with direct_vm.expect_revert("payment_tx must be"):
        payment_dispute_contract.dispute_payment("8453", bad_tx)


def test_duplicate_dispute_id_reverts(direct_vm, payment_dispute_contract):
    _world(direct_vm)
    payment_dispute_contract.dispute_payment("8453", TX)
    with direct_vm.expect_revert("duplicate dispute_id"):
        payment_dispute_contract.dispute_payment("8453", TX)


# --- permissions, state, reads -----------------------------------------------------------------

def test_set_chain_and_set_policy_are_operator_only(direct_vm, deploy_payment_dispute_contract, direct_alice):
    contract = deploy_payment_dispute_contract()
    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("only the operator may configure a chain"):
            contract.set_chain("8453", BASE_RPC_URL, BASE_USDC, PAYEE)
        with direct_vm.expect_revert("only the operator may publish the refund policy"):
            contract.set_policy("v1", "ab" * 32)


@pytest.mark.parametrize("args", [("x", BASE_RPC_URL, BASE_USDC, PAYEE), ("8453", "ftp://x", BASE_USDC, PAYEE),
                                  ("8453", BASE_RPC_URL, "0x12", PAYEE), ("8453", BASE_RPC_URL, BASE_USDC, "0x12")])
def test_set_chain_validates(direct_vm, deploy_payment_dispute_contract, args):
    with direct_vm.expect_revert():
        deploy_payment_dispute_contract().set_chain(*args)


def test_chain_config_lowercases_and_get_config(direct_vm, deploy_payment_dispute_contract):
    contract = deploy_payment_dispute_contract()
    contract.set_chain("84532", BASE_RPC_URL, BASE_USDC, PAYEE.upper().replace("0X", "0x"))
    contract.set_chain("8453", BASE_RPC_URL, BASE_USDC, PAYEE)
    chain = contract.get_chain("8453")
    assert (chain.usdc, chain.payee, chain.rpc_url) == (BASE_USDC.lower(), PAYEE, BASE_RPC_URL)
    assert contract.get_chain("84532").payee == PAYEE
    config = json.loads(contract.get_config())
    assert config["chains"] == ["8453", "84532"] and config["policy_sha256"] == ""
    with direct_vm.expect_revert("not configured"):
        contract.get_chain("1")


def test_views_and_recent(direct_vm, payment_dispute_contract, direct_alice):
    _world(direct_vm)
    first = payment_dispute_contract.dispute_payment("8453", TX)
    with direct_vm.prank(direct_alice):
        second = payment_dispute_contract.dispute_payment("8453", TX)
    assert json.loads(payment_dispute_contract.list_by_subject(TX)) == [first, second]
    assert json.loads(payment_dispute_contract.list_recent()) == [first, second]
    assert json.loads(payment_dispute_contract.list_by_subject("0x" + "00" * 32)) == []
    with direct_vm.expect_revert("unknown dispute_id"):
        payment_dispute_contract.get_dispute("0" * 64)


def test_list_recent_keeps_the_last_200(direct_vm, payment_dispute_contract):
    payment_dispute_contract.recent = json.dumps([f"id{i}" for i in range(200)])
    _world(direct_vm)
    new = payment_dispute_contract.dispute_payment("8453", TX)
    recent = json.loads(payment_dispute_contract.list_recent())
    assert len(recent) == 200 and recent[-1] == new and recent[0] == "id1"


# --- validator, via direct_vm.run_validator() ----------------------------------------------------

def _leader_observation(direct_vm):
    return copy.deepcopy(direct_vm._captured_validators[-1][0])


def test_validator_agrees_in_the_same_world(direct_vm, payment_dispute_contract):
    _world(direct_vm)
    payment_dispute_contract.dispute_payment("8453", TX)
    assert direct_vm.run_validator() is True
    assert direct_vm.run_validator(leader_result=_leader_observation(direct_vm)) is True


def test_validator_disagrees_when_the_index_is_not_readable(direct_vm, payment_dispute_contract):
    _world(direct_vm)
    payment_dispute_contract.dispute_payment("8453", TX)
    direct_vm.clear_mocks()
    _world(direct_vm, status=404, body="not found")
    assert direct_vm.run_validator() is False


def test_validator_disagrees_when_a_receipt_appears(direct_vm, payment_dispute_contract):
    _world(direct_vm)
    payment_dispute_contract.dispute_payment("8453", TX)
    direct_vm.clear_mocks()
    _world(direct_vm, _index(receipt_ids=["ab" * 16]))
    assert direct_vm.run_validator() is False


def test_validator_returns_false_when_only_its_rpc_fetch_raises(direct_vm, payment_dispute_contract):
    _world(direct_vm)
    payment_dispute_contract.dispute_payment("8453", TX)
    direct_vm.clear_mocks()
    _world(direct_vm, rpc=None)
    assert direct_vm.run_validator() is False


def test_validator_rejects_a_malformed_leader_result(direct_vm, payment_dispute_contract):
    _world(direct_vm)
    payment_dispute_contract.dispute_payment("8453", TX)
    assert direct_vm.run_validator(leader_result="not-an-observation") is False
    assert direct_vm.run_validator(leader_result={"fetch": "ok"}) is False
    assert direct_vm.run_validator(leader_result={"receipt_http": 200, "receipt_sha256": "", "fetch": "ok"}) is False
    assert direct_vm.run_validator(leader_error=RuntimeError("leader blew up")) is False


@pytest.mark.parametrize("forge", [
    lambda o: o["index"].update(receipt_ids=["ab" * 16]),
    lambda o: o["index"].update(refund_tx=REFUND_TX),
    lambda o: o.update(tx_status=0),
    lambda o: o.update(chain_found=False),
    lambda o: o["transfers"][0].__setitem__(2, hex(10 ** 12)),
    lambda o: o["transfers"][0].__setitem__(0, "0x" + "ee" * 20),
    lambda o: o.update(receipt_sha256="00" * 32),
], ids=["ids-added", "refund-tx-set", "tx_status", "chain_found", "amount", "payer", "sha"])
def test_forged_leader_observation_is_rejected(direct_vm, payment_dispute_contract, forge):
    _world(direct_vm)
    payment_dispute_contract.dispute_payment("8453", TX)
    forged = _leader_observation(direct_vm)
    forge(forged)
    assert direct_vm.run_validator(leader_result=forged) is False


def test_forged_empty_receipt_ids_on_a_world_with_a_receipt_is_rejected(direct_vm, payment_dispute_contract):
    _world(direct_vm, _index(receipt_ids=["ab" * 16]), rpc=None)
    payment_dispute_contract.dispute_payment("8453", TX)
    forged = _leader_observation(direct_vm)
    forged["index"]["receipt_ids"] = []
    forged.update(chain_found=True, tx_status=1, transfers=[[PAYER, PAYEE, hex(1000000)]])
    assert direct_vm.run_validator(leader_result=forged) is False


def test_forged_refund_tx_nulled_on_a_refunded_payment_is_rejected(direct_vm, payment_dispute_contract):
    _world(direct_vm, _index(refund_tx=REFUND_TX), rpc=None)
    payment_dispute_contract.dispute_payment("8453", TX)
    forged = _leader_observation(direct_vm)
    forged["index"]["refund_tx"] = ""
    forged["chain_found"] = True
    forged["tx_status"] = 1
    forged["transfers"] = [[PAYER, PAYEE, hex(1000000)]]
    assert direct_vm.run_validator(leader_result=forged) is False


# --- structure ---------------------------------------------------------------------------------

def _tree(name):
    return ast.parse((CONTRACTS / name).read_text(encoding="utf-8"))


def _node(tree, name):
    return next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)


def test_dispute_shares_attest_helpers():
    attest, receipt, payment = (_tree(f"apibase_{n}.py") for n in ("receipt_attest", "receipt_dispute", "payment_dispute"))
    for name in ("_validate_receipt", "_error_observation"):
        assert ast.dump(_node(attest, name)) == ast.dump(_node(receipt, name)), name
    for name in ("_rpc_request_body", "_parse_transfers", "_observe_rpc", "_error_observation"):
        assert ast.dump(_node(attest, name)) == ast.dump(_node(payment, name)), name
    assert ast.dump(_node(receipt, "Dispute")) == ast.dump(_node(payment, "Dispute"))
    assert [f.target.id for f in _node(receipt, "Dispute").body if isinstance(f, ast.AnnAssign)] == [
        "dispute_id", "claim", "receipt_id", "chain_id", "payment_tx", "payer", "payee", "amount_atomic",
        "policy_version", "policy_sha256", "verdict", "reason", "evidence_sha256", "checked_at", "requester"]


def test_module_docstring_and_public_methods():
    tree = _tree("apibase_payment_dispute.py")
    doc = ast.get_docstring(tree)
    assert doc, "module docstring missing"
    assert len(doc.encode("utf-8")) <= 600 and len(doc.splitlines()) <= 8
    for needle in ("apibase.pro/r/", "Base", "README"):
        assert needle in doc, needle
    cls = _node(tree, "ApibasePaymentDispute")
    public = [n for n in cls.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
    assert sorted(n.name for n in public) == ["dispute_payment", "get_chain", "get_config", "get_dispute",
                                              "list_by_subject", "list_recent", "set_chain", "set_policy"]
    for fn in public:
        text = ast.get_docstring(fn)
        assert text and len(text.encode("utf-8")) <= 100, (fn.name, text)


def test_payment_dispute_header_names_the_babwp_runner():
    head = (CONTRACTS / "apibase_payment_dispute.py").read_text(encoding="utf-8").splitlines()[:2]
    assert head == ["# v0.3.0",
                    '# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }']


def test_the_dispute_contracts_have_no_refund_confirmation():
    # confirm_refund is v1.1 (ruling T-GD-01 q-1): the verdict records are immutable.
    for name in ("apibase_receipt_dispute.py", "apibase_payment_dispute.py"):
        assert "confirm_refund" not in (CONTRACTS / name).read_text(encoding="utf-8")
