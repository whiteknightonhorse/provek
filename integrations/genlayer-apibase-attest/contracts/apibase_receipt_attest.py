# v0.3.0
# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }

"""APIbase Receipt Attest - what this witness attests.

I attest that an APIbase paid-call receipt matches the USDC transfer it names on Base. Validators
fetch the receipt at https://apibase.pro/r/<receipt_id>.json and the transfer on Base
independently and agree only if they saw the same thing. Attesting is permissionless; APIbase
cannot alter the result. No LLM, no spending.
Full reference: README, section ApibaseReceiptAttest.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import genlayer as gl
from genlayer.types import *

TRANSFER_TOPIC = "0x" + "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
"""`keccak256("Transfer(address,address,uint256)")`, the ERC-20 event topic (split so the repo secret scan stays strict)."""

RECEIPT_SCHEMA = "apibase-receipt/1"
SUPPORTED_RAIL = "x402-base"

_RECEIPT_ID_RE = re.compile(r"^[0-9a-f]{32,64}$")
_TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_DECIMAL_RE = re.compile(r"^[0-9]{1,78}$")

_REQUIRED_OBSERVATION_KEYS = frozenset({"receipt_http", "receipt_sha256", "fetch"})
_FETCH_STATES = frozenset({"ok", "error"})


@gl.storage.allow
@dataclass
class ChainConfig:
    """One chain the contract is willing to ask about: the JSON-RPC endpoint (the stated trust
    assumption) and the lowercase address of that chain's USDC token."""

    rpc_url: str
    usdc: str


@gl.storage.allow
@dataclass
class Attestation:
    """The published record for one `attest()` call — immutable once written. `result` is
    `PASS`/`FAIL`/`NOT_FOUND`; `observation` is the short reason (`payment_matches`,
    `no_matching_transfer`, `tx_reverted`, `tx_not_found`). The receipt's own fields are copied in
    (already validated and lowercased) so the record stands on its own."""

    receipt_id: str
    receipt_sha256: str
    rail: str
    chain_id: str
    payment_tx: str
    payer: str
    payee: str
    amount_atomic: str
    tool: str
    upstream_status: u256
    billed: bool
    response_sha256: str
    result: str
    observation: str
    checked_at: str
    requester: str


def _validate_receipt(doc) -> tuple:
    """Strict shape check of a parsed receipt. Returns `(receipt, None)` with every field
    normalised (addresses, hashes lowercased; `chain_id`/`upstream_status` as int), or
    `(None, key)` naming the FIRST key that is missing or malformed. Pure."""
    if not isinstance(doc, dict):
        return None, "body"
    if doc.get("schema") != RECEIPT_SCHEMA:
        return None, "schema"
    rail = doc.get("rail")
    if not isinstance(rail, str) or rail == "":
        return None, "rail"
    chain_id = doc.get("chain_id")
    if isinstance(chain_id, bool) or not isinstance(chain_id, int) or chain_id < 0:
        return None, "chain_id"
    payment_tx = doc.get("payment_tx")
    if not isinstance(payment_tx, str) or not _TX_RE.match(payment_tx):
        return None, "payment_tx"
    for key in ("payer", "payee"):
        value = doc.get(key)
        if not isinstance(value, str) or not _ADDR_RE.match(value):
            return None, key
    if doc.get("asset") != "USDC":
        return None, "asset"
    amount = doc.get("amount_atomic")
    if not isinstance(amount, str) or not _DECIMAL_RE.match(amount):
        return None, "amount_atomic"
    if not isinstance(doc.get("billed"), bool):
        return None, "billed"
    tool = doc.get("tool")
    if not isinstance(tool, str):
        return None, "tool"
    upstream_status = doc.get("upstream_status")
    if isinstance(upstream_status, bool) or not isinstance(upstream_status, int) or upstream_status < 0:
        return None, "upstream_status"
    response_sha256 = doc.get("response_sha256")
    if not isinstance(response_sha256, str) or not _SHA_RE.match(response_sha256):
        return None, "response_sha256"
    return {
        "schema": RECEIPT_SCHEMA,
        "rail": rail,
        "chain_id": chain_id,
        "payment_tx": payment_tx.lower(),
        "payer": doc["payer"].lower(),
        "payee": doc["payee"].lower(),
        "asset": "USDC",
        "amount_atomic": str(int(amount)),
        "billed": doc["billed"],
        "tool": tool,
        "upstream_status": upstream_status,
        "response_sha256": response_sha256.lower(),
    }, None


def _error_observation() -> dict:
    return {"receipt_http": 0, "receipt_sha256": "", "fetch": "error"}


def _observe_receipt(response, chains_cfg: dict) -> tuple:
    """Turn the APIbase receipt `Response` into `(observation, plan)`. `plan` is `None` when no
    chain lookup is to be made, else `(rpc_url, usdc, payment_tx)`. Pure and exception-free for any
    `Response` — the `gl.nondet.web.*` calls stay written out inside `leader_fn`/`validator_fn`
    (genvm-lint wants the call textually inside the closure; the witness contract explains it)."""
    body = response.body or b""
    observation = {"receipt_http": response.status, "receipt_sha256": hashlib.sha256(body).hexdigest(),
                   "fetch": "ok"}
    if response.status != 200:
        return observation, None
    try:
        doc = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        observation["skip_reason"] = "malformed receipt: body"
        return observation, None
    receipt, bad_key = _validate_receipt(doc)
    if receipt is None:
        observation["skip_reason"] = f"malformed receipt: {bad_key}"
        return observation, None
    observation["receipt"] = receipt
    if receipt["rail"] != SUPPORTED_RAIL:
        observation["skip_reason"] = f"unsupported rail {receipt['rail']}"
        return observation, None
    if receipt["billed"] is not True:
        observation["skip_reason"] = "not billed"
        return observation, None
    chain = chains_cfg.get(str(receipt["chain_id"]))
    if chain is None:
        observation["skip_reason"] = f"chain {receipt['chain_id']} not configured"
        return observation, None
    return observation, (chain[0], chain[1], receipt["payment_tx"])


def _rpc_request_body(payment_tx: str) -> bytes:
    return json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt",
                       "params": [payment_tx]}).encode("utf-8")


def _parse_transfers(logs, usdc: str) -> list:
    """`[from, to, value_hex]` for every ERC-20 `Transfer` log emitted by `usdc` (lowercase
    address), in log order. Logs of other contracts, other events, ERC-721-shaped transfers (four
    topics) and unparseable data are skipped. `value_hex` is `hex(int)` — canonical, no padding."""
    transfers = []
    for log in logs or []:
        if not isinstance(log, dict):
            continue
        if str(log.get("address", "")).lower() != usdc:
            continue
        topics = log.get("topics")
        if not isinstance(topics, list) or len(topics) != 3:
            continue
        if str(topics[0]).lower() != TRANSFER_TOPIC:
            continue
        try:
            value = int(str(log.get("data", "")), 16)
        except ValueError:
            continue
        sender = "0x" + str(topics[1]).lower()[-40:]
        recipient = "0x" + str(topics[2]).lower()[-40:]
        transfers.append([sender, recipient, hex(value)])
    return transfers


def _observe_rpc(observation: dict, rpc_response, usdc: str) -> dict:
    """Fold the JSON-RPC answer into `observation`. Raises `ValueError` for anything that is not a
    well-formed answer (HTTP != 200, not JSON, `error` member, neither a receipt nor `null`) — the
    caller maps a raise to `fetch="error"` (leader) or `False` (validator)."""
    if rpc_response.status != 200:
        raise ValueError(f"rpc http {rpc_response.status}")
    answer = json.loads((rpc_response.body or b"").decode("utf-8"))
    if not isinstance(answer, dict) or "result" not in answer or "error" in answer:
        raise ValueError("rpc answer has no result")
    result = answer["result"]
    if result is None:
        observation["chain_found"] = False
        return observation
    if not isinstance(result, dict):
        raise ValueError("rpc result is neither null nor an object")
    observation["chain_found"] = True
    observation["tx_status"] = int(str(result["status"]), 16)
    observation["transfers"] = _parse_transfers(result.get("logs"), usdc)
    return observation


def _matched_transfer(observation: dict):
    """The `[from, to, value_hex]` entry equal to the receipt's `[payer, payee, amount]` (values
    compared as integers), or `None`."""
    receipt = observation["receipt"]
    want = (receipt["payer"], receipt["payee"], int(receipt["amount_atomic"]))
    for transfer in observation.get("transfers") or []:
        if (transfer[0], transfer[1], int(transfer[2], 16)) == want:
            return transfer
    return None


def _well_formed(observation) -> bool:
    """What the validator demands of the leader's calldata before spending a fetch on it."""
    if not isinstance(observation, dict) or not _REQUIRED_OBSERVATION_KEYS <= observation.keys():
        return False
    if observation["fetch"] not in _FETCH_STATES:
        return False
    if observation["fetch"] != "ok" or observation["receipt_http"] != 200:
        return True
    if "skip_reason" in observation:
        return True
    if not isinstance(observation.get("receipt"), dict) or not isinstance(observation.get("chain_found"), bool):
        return False
    if observation["chain_found"]:
        return (isinstance(observation.get("tx_status"), int)
                and isinstance(observation.get("transfers"), list))
    return True


def _judge(receipt_id: str, observation: dict) -> tuple:
    """The one deterministic verdict function, called identically by leader and validators and by
    `attest()` after consensus. Returns `(result, detail)`; `result == "REVERT"` means "write
    nothing, raise `detail`". Never raises for a `_well_formed` observation."""
    if observation["fetch"] != "ok" or observation["receipt_http"] != 200:
        return "REVERT", f"receipt {receipt_id} is not readable at APIbase (http={observation['receipt_http']})"
    if "skip_reason" in observation:
        return "REVERT", f"receipt {receipt_id} is not attestable by this contract: {observation['skip_reason']}"
    if not observation["chain_found"]:
        return "NOT_FOUND", "tx_not_found"
    if observation["tx_status"] != 1:
        return "FAIL", "tx_reverted"
    if _matched_transfer(observation) is not None:
        return "PASS", "payment_matches"
    return "FAIL", "no_matching_transfer"


class ApibaseReceiptAttest(gl.contract.Contract):
    """See the module docstring. Storage: `operator` (fixed at construction), `receipt_base_url`
    (receipts live at `{receipt_base_url}{receipt_id}.json`), `chains` (chain id -> `ChainConfig`,
    operator-updatable), `records` (attest_id -> `Attestation`, append-only), `index`
    (receipt_id -> JSON list of attest_ids; a list inside a `TreeMap` is kept as a JSON string, the
    same workaround the witness contract uses)."""

    operator: Address
    receipt_base_url: str
    chains: gl.storage.TreeMap[str, ChainConfig]
    records: gl.storage.TreeMap[str, Attestation]
    index: gl.storage.TreeMap[str, str]

    def __init__(self, operator: Address, receipt_base_url: str):
        parsed = urlparse(receipt_base_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or not receipt_base_url.endswith("/"):
            raise gl.vm.UserError("receipt_base_url must be an http(s) URL ending in '/'")
        self.operator = operator
        self.receipt_base_url = receipt_base_url

    @gl.public.write
    def set_chain(self, chain_id: str, rpc_url: str, usdc: str) -> None:
        """Operator-only: set the JSON-RPC URL and USDC address for a chain id."""
        if gl.message.sender_address != self.operator:
            raise gl.vm.UserError("only the operator may configure a chain")
        if not isinstance(chain_id, str) or not re.match(r"^[0-9]{1,20}$", chain_id):
            raise gl.vm.UserError("chain_id must be a decimal string")
        parsed = urlparse(rpc_url) if isinstance(rpc_url, str) else None
        if parsed is None or parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise gl.vm.UserError("rpc_url must be an http(s) URL")
        if not isinstance(usdc, str) or not _ADDR_RE.match(usdc):
            raise gl.vm.UserError("usdc must be a 0x-prefixed 20-byte hex address")
        self.chains[chain_id] = ChainConfig(rpc_url=rpc_url, usdc=usdc.lower())

    @gl.public.write
    def attest(self, receipt_id: str) -> str:
        """Permissionless: attest one receipt id by consensus; returns the attest_id."""
        if not isinstance(receipt_id, str) or not _RECEIPT_ID_RE.match(receipt_id):
            raise gl.vm.UserError("receipt_id must be 32-64 lowercase hex characters")

        checked_at = gl.message.raw["datetime"]
        sender = gl.message.sender_address.as_hex
        attest_id = hashlib.sha256(
            json.dumps([receipt_id, checked_at, sender], sort_keys=True).encode("utf-8")
        ).hexdigest()
        if attest_id in self.records:
            raise gl.vm.UserError(f"duplicate attest_id {attest_id}: this check was already published")

        receipt_url = f"{self.receipt_base_url}{receipt_id}.json"
        chains_cfg = {chain_id: [cfg.rpc_url, cfg.usdc] for chain_id, cfg in self.chains.items()}

        def leader_fn() -> dict:
            try:
                response = gl.nondet.web.get(receipt_url)
                observation, plan = _observe_receipt(response, chains_cfg)
                if plan is not None:
                    rpc_response = gl.nondet.web.post(
                        plan[0], body=_rpc_request_body(plan[2]),
                        headers={"Content-Type": "application/json"})
                    observation = _observe_rpc(observation, rpc_response, plan[1])
                return observation
            except Exception:
                return _error_observation()

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            leader_observation = leader_result.calldata
            if not _well_formed(leader_observation):
                return False
            try:
                response = gl.nondet.web.get(receipt_url)
                my_observation, plan = _observe_receipt(response, chains_cfg)
                if plan is not None:
                    rpc_response = gl.nondet.web.post(
                        plan[0], body=_rpc_request_body(plan[2]),
                        headers={"Content-Type": "application/json"})
                    my_observation = _observe_rpc(my_observation, rpc_response, plan[1])
            except Exception:
                # "Nobody could check" is not "the claim is false": vote Disagree, let GenVM
                # rotate the leader, write nothing.
                return False
            # Every input is immutable by design (write-once receipt, mined Base receipt), so
            # whole-observation equality is the binding: the record is built from all of it.
            return leader_observation == my_observation

        observation = gl.vm.run_nondet(leader_fn, validator_fn)

        result, detail = _judge(receipt_id, observation)
        if result == "REVERT":
            raise gl.vm.UserError(detail)

        receipt = observation["receipt"]
        self.records[attest_id] = Attestation(
            receipt_id=receipt_id,
            receipt_sha256=observation["receipt_sha256"],
            rail=receipt["rail"],
            chain_id=str(receipt["chain_id"]),
            payment_tx=receipt["payment_tx"],
            payer=receipt["payer"],
            payee=receipt["payee"],
            amount_atomic=receipt["amount_atomic"],
            tool=receipt["tool"],
            upstream_status=receipt["upstream_status"],
            billed=receipt["billed"],
            response_sha256=receipt["response_sha256"],
            result=result,
            observation=detail,
            checked_at=checked_at,
            requester=sender,
        )

        attest_ids = json.loads(self.index.get(receipt_id) or "[]")
        attest_ids.append(attest_id)
        self.index[receipt_id] = json.dumps(attest_ids)

        return attest_id

    @gl.public.view
    def get_attestation(self, attest_id: str) -> Attestation:
        """The published record for attest_id; reverts if unknown."""
        if attest_id not in self.records:
            raise gl.vm.UserError(f"unknown attest_id {attest_id!r}")
        return self.records[attest_id]

    @gl.public.view
    def list_by_receipt(self, receipt_id: str) -> str:
        """JSON list of attest_ids for receipt_id, in request order, or "[]"."""
        return self.index.get(receipt_id) or "[]"

    @gl.public.view
    def get_chain(self, chain_id: str) -> ChainConfig:
        """The RPC URL and USDC address for chain_id; reverts if not configured."""
        if chain_id not in self.chains:
            raise gl.vm.UserError(f"chain {chain_id!r} is not configured")
        return self.chains[chain_id]

    @gl.public.view
    def get_config(self) -> str:
        """JSON: operator, receipt_base_url, sorted chain ids."""
        return json.dumps({
            "operator": self.operator.as_hex,
            "receipt_base_url": self.receipt_base_url,
            "chains": sorted(chain_id for chain_id, _ in self.chains.items()),
        }, sort_keys=True)
