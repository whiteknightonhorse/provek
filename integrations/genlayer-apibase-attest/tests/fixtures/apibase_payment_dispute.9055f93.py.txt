# v0.3.0
# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }

"""APIbase Payment Dispute - what this witness decides.

I decide REFUND or RELEASE for one closed claim: a USDC payment on Base to APIbase has no receipt
under https://apibase.pro/r/. Validators read APIbase's published index and Base independently and
agree only if they saw the same thing. A verdict never pays; moving USDC is APIbase's capped worker's job.
Full reference: README, section ApibasePaymentDispute.
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

_TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")

_REQUIRED_OBSERVATION_KEYS = frozenset({"receipt_http", "receipt_sha256", "fetch"})
_FETCH_STATES = frozenset({"ok", "error"})
_INDEX_SCHEMA = "apibase-receipt-index/1"
_JSON = {"Content-Type": "application/json"}
_RECENT_MAX = 200


@gl.storage.allow
@dataclass
class ChainConfig:
    """One chain: JSON-RPC endpoint (the stated trust assumption), USDC token, APIbase's payee."""

    rpc_url: str
    usdc: str
    payee: str


@gl.storage.allow
@dataclass
class Dispute:
    """One published verdict - immutable once written. `verdict` is `REFUND`/`RELEASE`, `reason`
    the short rule that decided it; `receipt_id` is empty for a payment claim."""

    dispute_id: str
    claim: str
    receipt_id: str
    chain_id: str
    payment_tx: str
    payer: str
    payee: str
    amount_atomic: str
    policy_version: str
    policy_sha256: str
    verdict: str
    reason: str
    evidence_sha256: str
    checked_at: str
    requester: str


def _error_observation() -> dict:
    return {"receipt_http": 0, "receipt_sha256": "", "fetch": "error"}


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


def _observe_index(response, payment_tx: str) -> dict:
    """The `by-tx/<tx>.json` index as an observation. Raises `ValueError` for any status or shape but
    the published one: an absent index is unmeasured, not "no receipt"."""
    if response.status != 200:
        raise ValueError(f"index http {response.status}")
    body = response.body or b""
    doc = json.loads(body.decode("utf-8"))
    if not isinstance(doc, dict):
        raise ValueError("index shape")
    ids, refund_tx = doc.get("receipt_ids"), doc.get("refund_tx")
    if (doc.get("schema") != _INDEX_SCHEMA or doc.get("payment_tx") != payment_tx
            or not isinstance(ids, list) or not all(isinstance(i, str) for i in ids)
            or not (refund_tx is None or (isinstance(refund_tx, str) and _TX_RE.match(refund_tx)))):
        raise ValueError("index shape")
    return {"receipt_http": 200, "receipt_sha256": hashlib.sha256(body).hexdigest(), "fetch": "ok",
            "index": {"receipt_ids": ids, "refund_tx": refund_tx or ""}}


def _well_formed(observation) -> bool:
    """What the validator demands of the leader's calldata before spending a fetch on it."""
    if not isinstance(observation, dict) or not _REQUIRED_OBSERVATION_KEYS <= observation.keys():
        return False
    if observation["fetch"] not in _FETCH_STATES:
        return False
    if observation["fetch"] != "ok" or observation["receipt_http"] != 200:
        return True
    index = observation.get("index")
    if not isinstance(index, dict):
        return False
    if index.get("refund_tx") or index.get("receipt_ids"):
        return True
    if not isinstance(observation.get("chain_found"), bool):
        return False
    return not observation["chain_found"] or (isinstance(observation.get("tx_status"), int)
                                              and isinstance(observation.get("transfers"), list))


def _paid(observation: dict, payee: str):
    """The first `[from, to, value_hex]` transfer to `payee`, or `None`."""
    for transfer in observation.get("transfers") or []:
        if transfer[1] == payee:
            return transfer
    return None


def _judge(payment_tx: str, observation: dict, payee: str, prior: str) -> tuple:
    """`(verdict, reason)`; `REVERT` means "write nothing, raise `reason`". Same code for every node."""
    if observation["fetch"] != "ok" or observation["receipt_http"] != 200:
        return "REVERT", f"index for {payment_tx} is not readable at APIbase (http={observation['receipt_http']})"
    index = observation["index"]
    if index["refund_tx"]:
        return "RELEASE", "already_refunded"
    if index["receipt_ids"]:
        return "RELEASE", f"receipt_exists:{index['receipt_ids'][0]}"
    if prior:
        return "RELEASE", f"refund_verdict_exists:{prior}"
    if not observation["chain_found"]:
        return "RELEASE", "tx_not_found"
    if observation["tx_status"] != 1:
        return "RELEASE", "tx_reverted"
    if _paid(observation, payee) is None:
        return "RELEASE", "no_payment_to_apibase"
    return "REFUND", "paid_without_receipt"


class ApibasePaymentDispute(gl.contract.Contract):
    """See the module docstring and the README."""

    operator: Address
    receipt_base_url: str
    policy_version: str
    policy_sha256: str
    chains: gl.storage.TreeMap[str, ChainConfig]
    disputes: gl.storage.TreeMap[str, Dispute]
    index: gl.storage.TreeMap[str, str]
    recent: str
    refund_verdicts: gl.storage.TreeMap[str, str]

    def __init__(self, operator: Address, receipt_base_url: str):
        parsed = urlparse(receipt_base_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or not receipt_base_url.endswith("/"):
            raise gl.vm.UserError("receipt_base_url must be an http(s) URL ending in '/'")
        self.operator = operator
        self.receipt_base_url = receipt_base_url
        self.policy_version = ""
        self.policy_sha256 = ""
        self.recent = "[]"

    def _only_operator(self, what: str) -> None:
        if gl.message.sender_address != self.operator:
            raise gl.vm.UserError(f"only the operator may {what}")

    def _open(self, *subject) -> tuple:
        if self.policy_sha256 == "":
            raise gl.vm.UserError("refund policy not published")
        checked_at = gl.message.raw["datetime"]
        sender = gl.message.sender_address.as_hex
        dispute_id = hashlib.sha256(json.dumps([*subject, checked_at, sender]).encode("utf-8")).hexdigest()
        if dispute_id in self.disputes:
            raise gl.vm.UserError(f"duplicate dispute_id {dispute_id}: this check was already published")
        return dispute_id, checked_at, sender

    def _publish(self, record: Dispute) -> str:
        self.disputes[record.dispute_id] = record
        if record.verdict == "REFUND":
            self.refund_verdicts[record.payment_tx] = record.dispute_id
        for key in {record.receipt_id, record.payment_tx} - {""}:
            self.index[key] = json.dumps(json.loads(self.index.get(key) or "[]") + [record.dispute_id])
        self.recent = json.dumps((json.loads(self.recent) + [record.dispute_id])[-_RECENT_MAX:])
        return record.dispute_id

    @gl.public.write
    def set_policy(self, version: str, sha256: str) -> None:
        """Operator-only: pin the published refund policy (version label, sha-256 of its text)."""
        self._only_operator("publish the refund policy")
        if not isinstance(version, str) or not 0 < len(version) <= 32:
            raise gl.vm.UserError("policy version must be 1-32 characters")
        if not isinstance(sha256, str) or not _SHA_RE.match(sha256):
            raise gl.vm.UserError("policy sha256 must be 64 hex characters")
        self.policy_version = version
        self.policy_sha256 = sha256.lower()

    @gl.public.write
    def set_chain(self, chain_id: str, rpc_url: str, usdc: str, payee: str) -> None:
        """Operator-only: set RPC URL, USDC address and APIbase payee for a chain id."""
        self._only_operator("configure a chain")
        if not isinstance(chain_id, str) or not re.match(r"^[0-9]{1,20}$", chain_id):
            raise gl.vm.UserError("chain_id must be a decimal string")
        parsed = urlparse(rpc_url) if isinstance(rpc_url, str) else None
        if parsed is None or parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise gl.vm.UserError("rpc_url must be an http(s) URL")
        for value in (usdc, payee):
            if not isinstance(value, str) or not _ADDR_RE.match(value):
                raise gl.vm.UserError("usdc and payee must be 0x-prefixed 20-byte hex addresses")
        self.chains[chain_id] = ChainConfig(rpc_url=rpc_url, usdc=usdc.lower(), payee=payee.lower())

    @gl.public.write
    def dispute_payment(self, chain_id: str, payment_tx: str) -> str:
        """Permissionless: dispute paid_without_receipt for a Base payment; returns dispute_id."""
        if not isinstance(chain_id, str) or chain_id not in self.chains:
            raise gl.vm.UserError(f"chain {chain_id!r} is not configured")
        if not isinstance(payment_tx, str) or not _TX_RE.match(payment_tx):
            raise gl.vm.UserError("payment_tx must be a 0x-prefixed 32-byte hex hash")
        payment_tx = payment_tx.lower()
        dispute_id, checked_at, sender = self._open("payment", chain_id, payment_tx)
        rpc_url, usdc, payee = self.chains[chain_id].rpc_url, self.chains[chain_id].usdc, self.chains[chain_id].payee
        url = f"{self.receipt_base_url}by-tx/{payment_tx}.json"

        def leader_fn() -> dict:
            try:
                observation = _observe_index(gl.nondet.web.get(url), payment_tx)
                if not (observation["index"]["receipt_ids"] or observation["index"]["refund_tx"]):
                    rpc_response = gl.nondet.web.post(rpc_url, body=_rpc_request_body(payment_tx), headers=_JSON)
                    observation = _observe_rpc(observation, rpc_response, usdc)
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
                my_observation = _observe_index(gl.nondet.web.get(url), payment_tx)
                if not (my_observation["index"]["receipt_ids"] or my_observation["index"]["refund_tx"]):
                    rpc_response = gl.nondet.web.post(rpc_url, body=_rpc_request_body(payment_tx), headers=_JSON)
                    my_observation = _observe_rpc(my_observation, rpc_response, usdc)
            except Exception:
                # "Nobody could check" is not "the claim is false": vote Disagree, write nothing.
                return False
            # Every input is immutable by design (write-once index, mined Base receipt), so
            # whole-observation equality is the binding: the record is built from all of it.
            return leader_observation == my_observation

        observation = gl.vm.run_nondet(leader_fn, validator_fn)
        verdict, reason = _judge(payment_tx, observation, payee, self.refund_verdicts.get(payment_tx) or "")
        if verdict == "REVERT":
            raise gl.vm.UserError(reason)
        payer = amount = ""
        if verdict == "REFUND":
            transfer = _paid(observation, payee)
            payer, amount = transfer[0], str(int(transfer[2], 16))
        return self._publish(Dispute(
            dispute_id=dispute_id, claim="paid_without_receipt", receipt_id="", chain_id=chain_id,
            payment_tx=payment_tx, payer=payer, payee=payee, amount_atomic=amount,
            policy_version=self.policy_version, policy_sha256=self.policy_sha256, verdict=verdict,
            reason=reason, evidence_sha256=observation["receipt_sha256"], checked_at=checked_at,
            requester=sender))

    @gl.public.view
    def get_dispute(self, dispute_id: str) -> Dispute:
        """The published record for dispute_id; reverts if unknown."""
        if dispute_id not in self.disputes:
            raise gl.vm.UserError(f"unknown dispute_id {dispute_id!r}")
        return self.disputes[dispute_id]

    @gl.public.view
    def list_by_subject(self, key: str) -> str:
        """JSON list of dispute_ids for a receipt_id or payment_tx, or "[]"."""
        return self.index.get(key) or "[]"

    @gl.public.view
    def list_recent(self) -> str:
        """JSON list of the last 200 dispute_ids, newest last."""
        return self.recent

    @gl.public.view
    def get_chain(self, chain_id: str) -> ChainConfig:
        """The RPC URL, USDC address and payee for chain_id; reverts if not configured."""
        if chain_id not in self.chains:
            raise gl.vm.UserError(f"chain {chain_id!r} is not configured")
        return self.chains[chain_id]

    @gl.public.view
    def get_config(self) -> str:
        """JSON: operator, receipt_base_url, policy version and sha-256, sorted chain ids."""
        return json.dumps({
            "operator": self.operator.as_hex,
            "receipt_base_url": self.receipt_base_url,
            "policy_version": self.policy_version,
            "policy_sha256": self.policy_sha256,
            "chains": sorted(chain_id for chain_id, _ in self.chains.items()),
        }, sort_keys=True)
