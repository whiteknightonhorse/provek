# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

"""Provek Evidence Witness — a GenLayer Intelligent Contract.

WHAT THIS IS. A consensus-backed adjudicator for exactly two machine-checkable criteria over a
public URL: `url_reachable` and `artifact_hash` — the same two names as
`src.witness.witness.SUPPORTED_CRITERIA` in the Provek repository this integration lives beside.
Every check here is requested by the Provek operator (`operator: Address`, set once at
construction) and adjudicated by GenLayer's leader/validator consensus rather than by a single
untrusted process — that is the entire value this contract adds over `src/witness/witness.py`'s
own anonymous GET.

WHAT THIS IS NOT. This contract does not compute a Provek Score, does not implement Provek's
scoring methodology, and is not wired into `src/pipeline.py` or any cohort re-measure. It is a
separate, reusable verification primitive that could, in a later and separately-decided step,
become one input to a `WitnessRecord` (see `src/witness/witness.py`'s own docstring for that
schema) — no such bridge exists yet, and none is added here.

WHY NO LLM. Both criteria resolve from bytes already on the wire (an HTTP status, a hash of a
response body) — there is nothing here an LLM would add evidence for, only latency and a second,
unauditable source of disagreement. GenVM's own equivalence-principle guidance treats a custom
leader/validator pair as the general mechanism and prompt-based comparison as a convenience layer
for cases that need one; this contract is exactly the case that does not.

WHY A CUSTOM VALIDATOR, NOT `strict_eq`. `strict_eq` can only ask "did the validator compute byte-
identical output to the leader" — it cannot distinguish "the validator observed something
different" from "the validator could not observe anything at all", and it cannot reject a
malformed leader result before comparing it. `_judge` below is the one deterministic function
both leader and validator call, so the actual verdict rule lives in exactly one place (an
invariant checked by `tests/direct/test_provek_evidence_witness.py`'s golden-vector tests); the
validator's job is solely to decide whether it AGREES with the leader having reached that verdict,
by independently fetching the same URL and running the identical judgement function itself.

CONSENSUS SEMANTICS, NAMED EXPLICITLY. A leader response of 403/429/5xx is an OBSERVATION, not a
failure to observe: `_judge` turns it into a normal `FAIL` with `observation="status=NNN"`, mirroring
`src/witness/witness.py:154` ("everything that did not confirm is a FAIL"). This is a deliberate
departure from this project's own L-11 lesson (`tasks/lessons.md`), which usually asks 403/429/5xx
to collapse into "the server declined to say", not an absence — here it cannot collapse, because
that state has to survive being written to consensus-agreed on-chain storage as one of exactly two
`Result` values, and `observation` is exactly where the nuance ("status=429", not a bare FAIL) is
kept instead of being lost. Genuinely undetermined disagreement — the validator's OWN attempt to
observe the URL raising an exception — returns `False` from `validator_fn` without constructing a
FAIL: GenVM rotates leaders and the transaction goes undetermined (no state write), because that
case is "nobody could check", not "the claim is false".

OPERATOR-ONLY, BY DESIGN. `witness()` reverts for any `gl.message.sender_address` other than the
`operator` address fixed at construction — this preserves the same "checks run only by joint
request, never on this contract's own initiative" discipline `src/witness/witness.py`'s docstring
names as A-9. There is no permissionless mode in v0.

FIELD NAME NOTE (GL-harness-notes.md #3, GL-facts.md F5). `genlayer.gl.nondet.web.Response` is
defined with a `status` field, not `status_code` — the prose examples on the GenLayer docs site
use `status_code`, but the SDK actually installed (`genlayer-py==0.18.0` / the extracted
`py-lib-genlayer-std` runner pinned by this file's own header hash) defines `status`, confirmed by
running this project's own direct tests against it. This contract uses `response.status`.
"""

import hashlib
import json
from dataclasses import dataclass
from urllib.parse import urlparse

from genlayer import *
import genlayer.gl.vm as glvm

MAX_ARTIFACT_BYTES = 2_000_000
"""Same cap as `src.collector.reachability.MAX_ARTIFACT_BYTES` (ABI-5-3: one number, one reason —
generous for a checksum manifest or small build artefact, small enough that fetching it through
every validator costs nothing worth noticing). Enforced here by measuring the fetched body length
directly rather than by a streaming transfer cap: `gl.nondet.web.get` hands the whole `Response`
back at once, there is no partial-transfer hook to cap from inside a nondet block."""

SUPPORTED_CRITERIA = ("artifact_hash", "url_reachable")
"""Byte-for-byte the same two names as `src.witness.witness.SUPPORTED_CRITERIA` — deliberately: a
third, different vocabulary here would be a second methodology, which this integration exists
specifically not to become."""

_OBSERVATION_KEYS = frozenset({"url", "status", "body_sha256", "bytes", "fetch"})
_FETCH_STATES = frozenset({"ok", "too_large", "error"})


@allow_storage
@dataclass
class WitnessResult:
    """The published record for one `witness()` call — immutable once written, the same
    discipline `src/witness/witness.py`'s own `WitnessRecord` docstring holds historical records
    to. `observation` is a short human string (`"status=200"`, `"sha256 mismatch"`, `"unreachable"`,
    `"too_large"`) — the detail `result` alone would lose."""

    subject_id: str
    criterion: str
    evidence_url: str
    expected: str
    result: str
    evidence_digest: str
    checked_at: str
    observation: str


def _validate_url(url: str) -> None:
    """Deterministic, pre-consensus rejection of anything that is not a plausible public HTTP(S)
    URL. Five distinct malformed shapes are refused here, each with its own reason string:
    non-string/empty/over-length, whitespace-or-control characters, non-http(s) scheme, missing
    host, and userinfo in the authority. This is NOT the SSRF boundary `src.collector.reachability`
    enforces (validators resolve and fetch on their own infrastructure, not this host's) — it is
    the "is this even a URL worth asking a validator to fetch" boundary, kept here so a malformed
    request reverts before it ever reaches consensus."""
    if not isinstance(url, str) or len(url) == 0 or len(url) > 2048:
        raise glvm.UserError("evidence_url must be a non-empty string of at most 2048 characters")
    for ch in url:
        if ord(ch) <= 0x20 or ord(ch) == 0x7F:
            raise glvm.UserError("evidence_url must not contain whitespace or control characters")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise glvm.UserError(f"evidence_url must be http or https, got scheme {parsed.scheme!r}")
    if not parsed.hostname:
        raise glvm.UserError("evidence_url must name a host")
    if "@" in parsed.netloc:
        raise glvm.UserError("evidence_url must not carry userinfo")


def _normalize_observation(url: str, response) -> dict:
    """Turn a `gl.nondet.web.Response` into a plain dict of primitives (so it survives the
    `run_nondet_unsafe` calldata boundary — `genlayer.py.calldata.Decoded` only ever contains
    `None | int | str | bytes | list | dict`, never a custom class). Pure and exception-free —
    the `gl.nondet.web.get(url)` call itself stays written out inline inside `leader_fn` and
    `validator_fn` below rather than factored into a shared helper, because `genvm-lint`'s
    equivalence-principle reachability check statically requires a `gl.nondet.*` call to appear
    textually inside the leader/validator closure passed to `run_nondet_unsafe`, not merely inside
    a function that closure happens to call."""
    body = response.body or b""
    if len(body) > MAX_ARTIFACT_BYTES:
        return {"url": url, "status": response.status, "body_sha256": "", "bytes": len(body),
                "fetch": "too_large"}
    return {"url": url, "status": response.status, "body_sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body), "fetch": "ok"}


def _judge(criterion: str, expected: str, observation: dict) -> tuple[str, str]:
    """The one deterministic verdict function, called identically by the leader and by every
    validator (invariant: the rule that decides PASS/FAIL lives in exactly one place). Never
    raises for a well-formed `observation` dict — `fetch="error"`/`"too_large"` are themselves
    normal inputs, not exceptional ones; a genuine inability to observe is signalled by the
    `gl.nondet.web.get` call itself raising, before this function is ever reached."""
    fetch = observation["fetch"]
    if fetch == "error":
        return "FAIL", "unreachable"
    if fetch == "too_large":
        return "FAIL", "too_large"
    status = observation["status"]
    is_2xx = 200 <= status < 300
    if criterion == "url_reachable":
        return ("PASS" if is_2xx else "FAIL"), f"status={status}"
    # criterion == "artifact_hash"
    if not is_2xx:
        return "FAIL", f"status={status}"
    if observation["body_sha256"] == expected:
        return "PASS", f"status={status}"
    return "FAIL", "sha256 mismatch"


def _url_reachable_digest(url: str, result: str, checked_at: str) -> str:
    """Byte-for-byte `src.witness.witness._digest("url_reachable", url, result, checked_at)` —
    the ONE formula shared verbatim between the 3.10 Provek reader and this 3.12 contract reader
    of `tests/fixtures/digest_golden.json` (see that file and this integration's direct tests)."""
    return hashlib.sha256("|".join(["url_reachable", url, result, checked_at]).encode("utf-8")).hexdigest()


def _unreachable_digest(criterion: str, url: str, fetch: str, checked_at: str) -> str:
    """The `artifact_hash` FAIL-without-bytes digest. Provek's own `_check_artifact_hash` hashes
    `"artifact_hash|url|unreachable|" + str(e) + "|checked_at"` — `str(e)` is not available here
    (the nondet boundary discards the original exception), so a FIXED TOKEN (`fetch`, one of
    `"error"`/`"too_large"`) stands in for it. Named here and in README as a deliberate departure
    from Provek's formula, not an oversight."""
    return hashlib.sha256(
        "|".join(["artifact_hash", url, "unreachable", fetch, checked_at]).encode("utf-8")
    ).hexdigest()


class ProvekEvidenceWitness(gl.Contract):
    """See the module docstring for the full design rationale. Storage: `operator` (immutable
    after construction), `records` (witness_id -> `WitnessResult`, append-only), `index`
    (subject_id -> JSON-encoded list of witness_ids — a `TreeMap[str, DynArray[str]]` does not
    work without an explicit `gl.storage.inmem_allocate`, so the list is kept as a JSON string in a
    `TreeMap[str, str]`, the same workaround the GenLayer boilerplate's own `PatternTest.py`
    documents as "Pattern 7")."""

    operator: Address
    records: TreeMap[str, WitnessResult]
    index: TreeMap[str, str]

    def __init__(self, operator: Address):
        self.operator = operator

    @gl.public.write
    def witness(self, subject_id: str, criterion: str, evidence_url: str, expected: str) -> str:
        """Request one consensus-backed check. Reverts (transaction rolled back, no record
        written) for: a non-operator sender, an empty or over-length `subject_id`, an unsupported
        `criterion`, a malformed `evidence_url` (see `_validate_url`), a malformed `expected` for
        the given criterion, or a `witness_id` that already exists (records are immutable — a
        repeat request is a caller error, not a re-check)."""
        if gl.message.sender_address != self.operator:
            raise glvm.UserError("only the operator may request a witness check")
        if not isinstance(subject_id, str) or len(subject_id) == 0 or len(subject_id) > 256:
            raise glvm.UserError("subject_id must be a non-empty string of at most 256 characters")
        if criterion not in SUPPORTED_CRITERIA:
            raise glvm.UserError(
                f"unsupported criterion {criterion!r}: supported types are {SUPPORTED_CRITERIA}")
        _validate_url(evidence_url)

        expected = expected.strip().lower()
        if criterion == "artifact_hash":
            if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
                raise glvm.UserError("artifact_hash requires a 64-character hex sha256 in `expected`")
        else:  # url_reachable
            if expected != "":
                raise glvm.UserError("url_reachable does not take an `expected` value")

        checked_at = gl.message_raw["datetime"]
        sender = gl.message.sender_address.as_hex

        witness_id = hashlib.sha256(
            json.dumps([subject_id, criterion, evidence_url, expected, checked_at, sender],
                       sort_keys=True).encode("utf-8")
        ).hexdigest()
        if witness_id in self.records:
            raise glvm.UserError(f"duplicate witness_id {witness_id}: this check was already published")

        def leader_fn() -> dict:
            try:
                response = gl.nondet.web.get(evidence_url)
                return _normalize_observation(evidence_url, response)
            except Exception:
                return {"url": evidence_url, "status": 0, "body_sha256": "", "bytes": 0,
                        "fetch": "error"}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, glvm.Return):
                return False
            observation = leader_result.calldata
            if not isinstance(observation, dict):
                return False
            if not _OBSERVATION_KEYS <= observation.keys():
                return False
            if observation.get("fetch") not in _FETCH_STATES:
                return False
            try:
                response = gl.nondet.web.get(evidence_url)
                my_observation = _normalize_observation(evidence_url, response)
            except Exception:
                # The validator could not observe the URL itself — this is "no consensus is
                # possible", not "the claim is false": returning False here (rather than raising)
                # is a deliberate agree/disagree vote, matching run_nondet_unsafe's documented
                # contract that an uncaught exception is ALSO treated as Disagree, but named
                # explicitly rather than left implicit.
                return False
            leader_verdict, _ = _judge(criterion, expected, observation)
            my_verdict, _ = _judge(criterion, expected, my_observation)
            if leader_verdict != my_verdict:
                return False
            if criterion == "artifact_hash" and my_observation["body_sha256"] != observation.get("body_sha256"):
                return False
            return True

        observation = glvm.run_nondet_unsafe(leader_fn, validator_fn)

        result, observation_str = _judge(criterion, expected, observation)

        if criterion == "url_reachable":
            evidence_digest = _url_reachable_digest(evidence_url, result, checked_at)
        elif observation["fetch"] == "ok":
            evidence_digest = observation["body_sha256"]
        else:
            evidence_digest = _unreachable_digest(criterion, evidence_url, observation["fetch"], checked_at)

        self.records[witness_id] = WitnessResult(
            subject_id=subject_id,
            criterion=criterion,
            evidence_url=evidence_url,
            expected=expected,
            result=result,
            evidence_digest=evidence_digest,
            checked_at=checked_at,
            observation=observation_str,
        )

        subject_ids = json.loads(self.index.get(subject_id) or "[]")
        subject_ids.append(witness_id)
        self.index[subject_id] = json.dumps(subject_ids)

        return witness_id

    @gl.public.view
    def get_result(self, witness_id: str) -> WitnessResult:
        """The published record for `witness_id`. Raises if no such record exists — there is no
        "empty record" shape to return, the same `not_measured`-is-a-state-of-its-own discipline
        this repository's `CLAUDE.md` names as its most-violated invariant: a missing record is a
        caller error to surface, not a value to fabricate."""
        if witness_id not in self.records:
            raise glvm.UserError(f"unknown witness_id {witness_id!r}")
        return self.records[witness_id]

    @gl.public.view
    def list_by_subject(self, subject_id: str) -> str:
        """JSON-encoded list of every `witness_id` published for `subject_id`, in request order,
        or `"[]"` for a subject nobody has ever checked — the ordinary "nobody has asked yet"
        default, not an error (same choice `src.witness.witness.load_task_history` makes for a
        subject with no index file)."""
        return self.index.get(subject_id) or "[]"

    @gl.public.view
    def supported_criteria(self) -> list[str]:
        """The exact two criterion names this contract accepts — kept as a method, not just a
        module constant, so an on-chain caller can read it without reading source."""
        return list(SUPPORTED_CRITERIA)

    @gl.public.view
    def get_operator(self) -> Address:
        return self.operator
