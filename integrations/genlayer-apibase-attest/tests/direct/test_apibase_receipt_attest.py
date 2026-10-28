"""Direct-mode tests for `ApibaseReceiptAttest` — no GenVM WASM boundary, no network.

Every world is built from `direct_vm.mock_web()`: the receipt GET and the JSON-RPC POST. As in the
witness suite, direct mode writes the LEADER's result to state with no simulated vote, so the
validator's agree/disagree behaviour is tested afterwards via `direct_vm.run_validator()` against
swapped mocks.
"""
import ast
import copy
import hashlib
import json
import re
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
# Same values as `conftest.py` (a conftest is not importable from a test module without a package;
# `test_get_config` and `test_set_chain_lowercases_usdc_and_get_chain_reads_it` fail if they drift).
RECEIPT_BASE_URL = "https://receipts.example/r/"
BASE_RPC_URL = "https://rpc.example/base"
BASE_USDC = "0x833589fCd6eDb6E08f4c7C32D4f71b54bdA02913"
RECEIPT_ID = "ab" * 16
RECEIPT_URL = f"{RECEIPT_BASE_URL}{RECEIPT_ID}.json"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _world(direct_vm, receipt=None, rpc=None, receipt_status=200, receipt_body=None):
    """Register the receipt GET and the RPC POST mocks. `receipt` / `rpc` are dicts (default: the
    PASS fixtures); `receipt_body` overrides the serialised receipt text."""
    receipt = _load("receipt_pass.json") if receipt is None else receipt
    rpc = _load("rpc_receipt_pass.json") if rpc is None else rpc
    body = json.dumps(receipt) if receipt_body is None else receipt_body
    direct_vm.mock_web(re.escape(RECEIPT_URL), {"status": receipt_status, "body": body})
    direct_vm.mock_web(re.escape(BASE_RPC_URL), {"method": "POST", "status": 200, "body": json.dumps(rpc)})


def _attest(contract, receipt_id=RECEIPT_ID):
    return contract.get_attestation(contract.attest(receipt_id))


# --------------------------------------------------------------------------------------------
# verdicts
# --------------------------------------------------------------------------------------------

def test_pass_vector(direct_vm, attest_contract):
    _world(direct_vm)
    record = _attest(attest_contract)
    assert (record.result, record.observation) == ("PASS", "payment_matches")
    assert record.receipt_id == RECEIPT_ID
    assert record.payer == "0x688130810f0bede38742b66e7a443274c01d4213"
    assert record.payee == "0x781dfd3f2687f8e5656313b2179fdefdf99d339d"
    assert record.amount_atomic == "1000000"
    assert record.chain_id == "8453"
    assert record.billed is True
    assert record.upstream_status == 200
    assert record.receipt_sha256 == hashlib.sha256(json.dumps(_load("receipt_pass.json")).encode()).hexdigest()


def test_fail_when_the_amount_is_off_by_one(direct_vm, attest_contract):
    receipt = _load("receipt_pass.json")
    receipt["amount_atomic"] = str(int(receipt["amount_atomic"]) + 1)
    _world(direct_vm, receipt=receipt)
    record = _attest(attest_contract)
    assert (record.result, record.observation) == ("FAIL", "no_matching_transfer")


def test_fail_when_the_payee_differs(direct_vm, attest_contract):
    receipt = _load("receipt_pass.json")
    receipt["payee"] = "0x" + "11" * 20
    _world(direct_vm, receipt=receipt)
    record = _attest(attest_contract)
    assert (record.result, record.observation) == ("FAIL", "no_matching_transfer")


def test_fail_when_the_transaction_reverted(direct_vm, attest_contract):
    _world(direct_vm, rpc=_load("rpc_receipt_reverted.json"))
    record = _attest(attest_contract)
    assert (record.result, record.observation) == ("FAIL", "tx_reverted")


def test_not_found_when_the_node_returns_null(direct_vm, attest_contract):
    _world(direct_vm, rpc=_load("rpc_receipt_null.json"))
    record = _attest(attest_contract)
    assert (record.result, record.observation) == ("NOT_FOUND", "tx_not_found")


def test_a_transfer_from_another_token_does_not_count(direct_vm, attest_contract):
    rpc = _load("rpc_receipt_pass.json")
    rpc["result"]["logs"][0]["address"] = "0x" + "22" * 20
    _world(direct_vm, rpc=rpc)
    assert _attest(attest_contract).observation == "no_matching_transfer"


def test_the_amount_is_compared_as_an_integer_not_as_text(direct_vm, attest_contract):
    receipt = _load("receipt_pass.json")
    receipt["amount_atomic"] = "0001000000"
    _world(direct_vm, receipt=receipt)
    record = _attest(attest_contract)
    assert (record.result, record.amount_atomic) == ("PASS", "1000000")


# --------------------------------------------------------------------------------------------
# reverts that write nothing
# --------------------------------------------------------------------------------------------

def test_receipt_404_is_not_readable(direct_vm, attest_contract):
    _world(direct_vm, receipt_status=404, receipt_body="not found")
    with direct_vm.expect_revert("not readable"):
        attest_contract.attest(RECEIPT_ID)
    assert json.loads(attest_contract.list_by_receipt(RECEIPT_ID)) == []


def test_unreachable_receipt_is_not_readable(direct_vm, attest_contract):
    with direct_vm.expect_revert("not readable"):
        attest_contract.attest(RECEIPT_ID)


def test_rpc_failure_is_not_a_fail_verdict(direct_vm, attest_contract):
    _world(direct_vm)
    direct_vm.clear_mocks()
    direct_vm.mock_web(re.escape(RECEIPT_URL), {"status": 200, "body": json.dumps(_load("receipt_pass.json"))})
    direct_vm.mock_web(re.escape(BASE_RPC_URL), {"method": "POST", "status": 502, "body": "bad gateway"})
    with direct_vm.expect_revert("not readable"):
        attest_contract.attest(RECEIPT_ID)


def test_unsupported_rail_reverts(direct_vm, attest_contract):
    receipt = _load("receipt_pass.json")
    receipt["rail"] = "mpp-tempo"
    _world(direct_vm, receipt=receipt)
    with direct_vm.expect_revert("unsupported rail"):
        attest_contract.attest(RECEIPT_ID)


def test_unbilled_receipt_reverts(direct_vm, attest_contract):
    receipt = _load("receipt_pass.json")
    receipt["billed"] = False
    _world(direct_vm, receipt=receipt)
    with direct_vm.expect_revert("not billed"):
        attest_contract.attest(RECEIPT_ID)


def test_unconfigured_chain_reverts(direct_vm, bare_contract):
    _world(direct_vm)
    with direct_vm.expect_revert("not configured"):
        bare_contract.attest(RECEIPT_ID)


@pytest.mark.parametrize("key", ["schema", "payment_tx", "payer", "amount_atomic", "response_sha256", "upstream_status"])
def test_malformed_receipt_reverts_naming_the_key(direct_vm, attest_contract, key):
    receipt = _load("receipt_pass.json")
    receipt[key] = "garbage" if key != "upstream_status" else "200"
    _world(direct_vm, receipt=receipt)
    with direct_vm.expect_revert(f"malformed receipt: {key}"):
        attest_contract.attest(RECEIPT_ID)


@pytest.mark.parametrize("bad_id", ["AB" * 16, "ab" * 8, "zz" * 16, "ab" * 33, ""])
def test_bad_receipt_id_reverts(direct_vm, attest_contract, bad_id):
    with direct_vm.expect_revert("receipt_id must be 32-64 lowercase hex characters"):
        attest_contract.attest(bad_id)


def test_duplicate_attest_id_reverts(direct_vm, attest_contract):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    with direct_vm.expect_revert("duplicate attest_id"):
        attest_contract.attest(RECEIPT_ID)


# --------------------------------------------------------------------------------------------
# permissions, state, reads
# --------------------------------------------------------------------------------------------

def test_attest_is_permissionless(direct_vm, attest_contract, direct_alice):
    _world(direct_vm)
    with direct_vm.prank(direct_alice):
        attest_id = attest_contract.attest(RECEIPT_ID)
    assert attest_contract.get_attestation(attest_id).result == "PASS"


def test_set_chain_is_operator_only(direct_vm, bare_contract, direct_alice):
    with direct_vm.prank(direct_alice):
        with direct_vm.expect_revert("only the operator may configure a chain"):
            bare_contract.set_chain("8453", BASE_RPC_URL, BASE_USDC)


def test_set_chain_lowercases_usdc_and_get_chain_reads_it(direct_vm, attest_contract):
    chain = attest_contract.get_chain("8453")
    assert chain.usdc == BASE_USDC.lower()
    assert chain.rpc_url == BASE_RPC_URL


def test_get_chain_unknown_reverts(direct_vm, attest_contract):
    with direct_vm.expect_revert("not configured"):
        attest_contract.get_chain("1")


def test_get_config(direct_vm, attest_contract):
    attest_contract.set_chain("84532", BASE_RPC_URL, BASE_USDC)
    config = json.loads(attest_contract.get_config())
    assert config["receipt_base_url"] == RECEIPT_BASE_URL
    assert config["chains"] == ["8453", "84532"]
    assert re.fullmatch(r"0x[0-9a-fA-F]{40}", config["operator"])


def test_get_attestation_matches_what_was_written(direct_vm, attest_contract):
    _world(direct_vm)
    attest_id = attest_contract.attest(RECEIPT_ID)
    record = attest_contract.get_attestation(attest_id)
    receipt = _load("receipt_pass.json")
    assert record.payment_tx == receipt["payment_tx"]
    assert record.tool == receipt["tool"]
    assert record.response_sha256 == receipt["response_sha256"]
    assert record.rail == "x402-base"
    assert re.fullmatch(r"0x[0-9a-fA-F]{40}", record.requester)
    assert attest_id == hashlib.sha256(json.dumps(
        [RECEIPT_ID, record.checked_at, record.requester], sort_keys=True).encode()).hexdigest()


def test_get_attestation_unknown_id_reverts(direct_vm, attest_contract):
    with direct_vm.expect_revert("unknown attest_id"):
        attest_contract.get_attestation("0" * 64)


def test_list_by_receipt_preserves_order(direct_vm, attest_contract, direct_alice):
    _world(direct_vm)
    first = attest_contract.attest(RECEIPT_ID)
    # `warp()` after deploy has no effect in this harness (see conftest), so the second attest gets
    # a distinct attest_id from a distinct sender instead of a distinct datetime.
    with direct_vm.prank(direct_alice):
        second = attest_contract.attest(RECEIPT_ID)
    assert first != second
    assert json.loads(attest_contract.list_by_receipt(RECEIPT_ID)) == [first, second]


def test_list_by_receipt_unknown_is_empty(direct_vm, attest_contract):
    assert json.loads(attest_contract.list_by_receipt("cd" * 16)) == []


def test_checked_at_is_the_tx_datetime(direct_vm, deploy_attest_contract):
    direct_vm.warp("2026-03-01T00:00:00Z")
    contract = deploy_attest_contract()
    contract.set_chain("8453", BASE_RPC_URL, BASE_USDC)
    _world(direct_vm)
    assert _attest(contract).checked_at == "2026-03-01T00:00:00Z"


# --------------------------------------------------------------------------------------------
# validator, via direct_vm.run_validator()
# --------------------------------------------------------------------------------------------

def test_validator_agrees_in_the_same_world(direct_vm, attest_contract):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    assert direct_vm.run_validator() is True


def test_validator_disagrees_when_the_receipt_body_changes(direct_vm, attest_contract):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    # Only `tool` changes, so `_judge` still says PASS on both sides: this isolates the
    # receipt_sha256 clause of the agreement rule.
    receipt = _load("receipt_pass.json")
    receipt["tool"] = "some.other.tool"
    direct_vm.clear_mocks()
    _world(direct_vm, receipt=receipt)
    assert direct_vm.run_validator() is False


def test_validator_disagrees_when_the_rpc_value_changes(direct_vm, attest_contract):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    rpc = copy.deepcopy(_load("rpc_receipt_pass.json"))
    data = rpc["result"]["logs"][0]["data"]
    rpc["result"]["logs"][0]["data"] = "0x" + format(int(data, 16) + 1, "064x")
    direct_vm.clear_mocks()
    _world(direct_vm, rpc=rpc)
    assert direct_vm.run_validator() is False


def test_validator_returns_false_when_its_own_fetch_raises(direct_vm, attest_contract):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    direct_vm.clear_mocks()
    assert direct_vm.run_validator() is False


def test_validator_returns_false_when_only_its_rpc_fetch_raises(direct_vm, attest_contract):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    direct_vm.clear_mocks()
    direct_vm.mock_web(re.escape(RECEIPT_URL), {"status": 200, "body": json.dumps(_load("receipt_pass.json"))})
    assert direct_vm.run_validator() is False


def test_validator_rejects_a_malformed_leader_result(direct_vm, attest_contract):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    assert direct_vm.run_validator(leader_result="not-an-observation") is False
    assert direct_vm.run_validator(leader_result={"fetch": "ok"}) is False
    assert direct_vm.run_validator(leader_error=RuntimeError("leader blew up")) is False


def _leader_observation(direct_vm):
    return copy.deepcopy(direct_vm._captured_validators[-1][0])


@pytest.mark.parametrize("forge", [
    lambda o: o.update(tx_status=0),
    lambda o: o["receipt"].update(payee="0x" + "ee" * 20),
    lambda o: o.update(chain_found=False),
], ids=["tx_status", "receipt_payee", "chain_found"])
def test_validator_rejects_a_forged_unbound_field(direct_vm, attest_contract, forge):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    forged = _leader_observation(direct_vm)
    forge(forged)
    assert direct_vm.run_validator(leader_result=forged) is False


def test_validator_agrees_with_the_true_leader_observation(direct_vm, attest_contract):
    _world(direct_vm)
    attest_contract.attest(RECEIPT_ID)
    assert direct_vm.run_validator(leader_result=_leader_observation(direct_vm)) is True


# --------------------------------------------------------------------------------------------
# golden vector — a REAL eth_getTransactionReceipt of a USDC transfer on Base
# --------------------------------------------------------------------------------------------

def test_parse_transfers_golden_vector(contract_module):
    real = _load("rpc_receipt_real_base_usdc.json")
    logs = real["result"]["logs"]
    assert len(logs) == 2  # one non-Transfer log (a shop event) and one USDC Transfer
    assert contract_module._parse_transfers(logs, BASE_USDC.lower()) == [[
        "0x688130810f0bede38742b66e7a443274c01d4213",
        "0x781dfd3f2687f8e5656313b2179fdefdf99d339d",
        "0xf4240",
    ]]
    assert int("0xf4240", 16) == 1_000_000
    assert contract_module._parse_transfers(logs, "0x" + "00" * 20) == []


# --- Gas-cap gates (GA-DEPLOY-GAS-1020, D-67): a size ceiling for every deployable contract, and a proof
# that shortening this contract changed documentation only. Pure `ast` and `git`; the reference for the
# docs-only comparison is a byte copy of the contract at the accepted commit 774a184 (fixture, sha256
# asserted below; the CI genlayer job is a depth-1 clone, so `git show` is not available there).
ATTEST = Path(__file__).resolve().parent.parent.parent / "contracts" / "apibase_receipt_attest.py"
ROOT = ATTEST.parents[3]
CONTRACT_FILES = sorted((ROOT / "integrations").glob("*/contracts/*.py"))

REFERENCE = Path(__file__).resolve().parent.parent / "fixtures" / "apibase_receipt_attest.774a184.py.txt"
REFERENCE_SHA256 = "1203e946c6082bc8e85c9a3deeb43f2e5f37e88e3c55afadde8e2c49b14836a8"
MAX_CONTRACT_BYTES = 19_000


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]
    return tree


def _without_validator_body(tree: ast.AST) -> ast.AST:
    """T-GLR-01 replaced the body of `validator_fn` (and only that) with whole-observation
    equality; it is checked by the forged-observation tests below, so it is blanked here."""
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "validator_fn":
            node.body = [ast.Pass()]
    return tree


def test_contract_sizes():
    assert ATTEST in CONTRACT_FILES and len(CONTRACT_FILES) >= 2, CONTRACT_FILES
    too_big = {str(p.relative_to(ROOT)): p.stat().st_size for p in CONTRACT_FILES
               if p.stat().st_size > MAX_CONTRACT_BYTES}
    assert not too_big, f"over {MAX_CONTRACT_BYTES} bytes (Bradbury per-tx gas cap): {too_big}"


# T-GLR-04: the one place the v0.2.16 -> v0.3.0 (py-genlayer babwp) API mapping is written down. The
# reference is the 774a184 file in the OLD API; applying exactly these substitutions to it must give
# the current file, validator body and docstrings aside, so the port changed names and nothing else.
API_MAP = (
    ("from genlayer import *\nimport genlayer.gl.vm as glvm", "import genlayer as gl\nfrom genlayer.types import *"),
    ("@allow_storage", "@gl.storage.allow"),
    ("(gl.Contract)", "(gl.contract.Contract)"),
    (": TreeMap[", ": gl.storage.TreeMap["),
    ("gl.message_raw[", "gl.message.raw["),
    ("glvm.run_nondet_unsafe(", "gl.vm.run_nondet("),
    ("glvm.", "gl.vm."),
)


def test_attest_header_names_the_babwp_runner():
    head = ATTEST.read_text(encoding="utf-8").splitlines()[:2]
    assert head == ["# v0.3.0",
                    '# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }']


def test_attest_docs_only_change():
    raw = REFERENCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == REFERENCE_SHA256, "reference is not the 774a184 file"
    reference = raw.decode("utf-8")
    for old_api, new_api in API_MAP:
        assert old_api in reference, old_api
        reference = reference.replace(old_api, new_api)
    before = _without_validator_body(_strip_docstrings(ast.parse(reference)))
    after = _without_validator_body(_strip_docstrings(ast.parse(ATTEST.read_text(encoding="utf-8"))))
    assert ast.dump(before, include_attributes=False) == ast.dump(after, include_attributes=False)


def test_attest_module_docstring():
    tree = ast.parse(ATTEST.read_text(encoding="utf-8"))
    doc = ast.get_docstring(tree)
    assert doc, "module docstring missing"
    assert len(doc.encode("utf-8")) <= 600 and len(doc.splitlines()) <= 8
    for needle in ("apibase.pro/r/", "Base", "README"):
        assert needle in doc, needle
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "ApibaseReceiptAttest")
    public = [n for n in cls.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
    assert len(public) == 6, [n.name for n in public]
    for fn in public:
        text = ast.get_docstring(fn)
        assert text and len(text.encode("utf-8")) <= 100, (fn.name, text)
