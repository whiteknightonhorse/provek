# v0.3.0
# { "Depends": "py-genlayer:babwp9t37jw9g4j2bccgn14g6x7x9s1f7dsmh7emvz735pz4zxa0" }

"""APIbase Receipt Dispute - what this witness decides.

I decide REFUND or RELEASE for one closed claim: the receipt at https://apibase.pro/r/<receipt_id>.json
billed a call whose upstream failed. Validators fetch it independently and agree only if they saw
the same thing. A verdict never pays; moving USDC on Base is APIbase's capped refund worker's job.
Full reference: README, section ApibaseReceiptDispute.
"""

import hashlib
import json
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import genlayer as gl
from genlayer.types import *

RECEIPT_SCHEMA = "apibase-receipt/1"
SUPPORTED_RAIL = "x402-base"

_RECEIPT_ID_RE = re.compile(r"^[0-9a-f]{32,64}$")
_TX_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_SHA_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_DECIMAL_RE = re.compile(r"^[0-9]{1,78}$")

_REQUIRED_OBSERVATION_KEYS = frozenset({"receipt_http", "receipt_sha256", "fetch"})
_FETCH_STATES = frozenset({"ok", "error"})
_RECENT_MAX = 200


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


def _observe_receipt(response) -> dict:
    """The APIbase receipt `Response` as an observation. Pure; the web call stays in the closure."""
    body = response.body or b""
    observation = {"receipt_http": response.status, "receipt_sha256": hashlib.sha256(body).hexdigest(),
                   "fetch": "ok"}
    if response.status != 200:
        return observation
    try:
        doc = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        observation["skip_reason"] = "malformed receipt: body"
        return observation
    receipt, bad_key = _validate_receipt(doc)
    if receipt is None:
        observation["skip_reason"] = f"malformed receipt: {bad_key}"
    elif receipt["rail"] != SUPPORTED_RAIL:
        observation["skip_reason"] = f"unsupported rail {receipt['rail']}"
    else:
        observation["receipt"] = receipt
    return observation


def _well_formed(observation) -> bool:
    """What the validator demands of the leader's calldata before spending a fetch on it."""
    if not isinstance(observation, dict) or not _REQUIRED_OBSERVATION_KEYS <= observation.keys():
        return False
    if observation["fetch"] not in _FETCH_STATES:
        return False
    if observation["fetch"] != "ok" or observation["receipt_http"] != 200 or "skip_reason" in observation:
        return True
    return isinstance(observation.get("receipt"), dict)


def _judge(receipt_id: str, observation: dict, prior: str) -> tuple:
    """`(verdict, reason)`; `REVERT` means "write nothing, raise `reason`". Same code for every node."""
    if observation["fetch"] != "ok" or observation["receipt_http"] != 200:
        return "REVERT", f"receipt {receipt_id} is not readable at APIbase (http={observation['receipt_http']})"
    if "skip_reason" in observation:
        return "REVERT", f"receipt {receipt_id} is not disputable by this contract: {observation['skip_reason']}"
    receipt = observation["receipt"]
    if receipt["billed"] is not True:
        return "RELEASE", "not_billed"
    if receipt["upstream_status"] < 500:
        return "RELEASE", f"upstream_status_{receipt['upstream_status']}"
    if prior:
        return "RELEASE", f"refund_verdict_exists:{prior}"
    return "REFUND", "upstream_failed_but_billed"


class ApibaseReceiptDispute(gl.contract.Contract):
    """See the module docstring and the README."""

    operator: Address
    receipt_base_url: str
    policy_version: str
    policy_sha256: str
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
    def dispute_receipt(self, receipt_id: str) -> str:
        """Permissionless: dispute upstream_failed_but_billed for a receipt; returns dispute_id."""
        if not isinstance(receipt_id, str) or not _RECEIPT_ID_RE.match(receipt_id):
            raise gl.vm.UserError("receipt_id must be 32-64 lowercase hex characters")
        dispute_id, checked_at, sender = self._open("receipt", receipt_id)
        url = f"{self.receipt_base_url}{receipt_id}.json"

        def leader_fn() -> dict:
            try:
                return _observe_receipt(gl.nondet.web.get(url))
            except Exception:
                return _error_observation()

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            leader_observation = leader_result.calldata
            if not _well_formed(leader_observation):
                return False
            try:
                my_observation = _observe_receipt(gl.nondet.web.get(url))
            except Exception:
                # "Nobody could check" is not "the claim is false": vote Disagree, write nothing.
                return False
            # Every input is immutable by design (write-once receipt), so whole-observation
            # equality is the binding: the record is built from all of it.
            return leader_observation == my_observation

        observation = gl.vm.run_nondet(leader_fn, validator_fn)
        prior = self.refund_verdicts.get(observation.get("receipt", {}).get("payment_tx", "")) or ""
        verdict, reason = _judge(receipt_id, observation, prior)
        if verdict == "REVERT":
            raise gl.vm.UserError(reason)
        receipt = observation["receipt"]
        return self._publish(Dispute(
            dispute_id=dispute_id, claim="upstream_failed_but_billed", receipt_id=receipt_id,
            chain_id=str(receipt["chain_id"]), payment_tx=receipt["payment_tx"], payer=receipt["payer"],
            payee=receipt["payee"], amount_atomic=receipt["amount_atomic"],
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
    def get_config(self) -> str:
        """JSON: operator, receipt_base_url, policy version and sha-256."""
        return json.dumps({
            "operator": self.operator.as_hex,
            "receipt_base_url": self.receipt_base_url,
            "policy_version": self.policy_version,
            "policy_sha256": self.policy_sha256,
        }, sort_keys=True)
