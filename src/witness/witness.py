"""Phase 2 - WitnessRecord v0 (spec 4.2-bis point 4, ABI-5-3, ABI-16-11).

WHAT THIS IS. A machine-checkable acceptance criterion, run ONCE by joint request of a customer
and a subject (never on this project's own initiative - A-9: active checks run only when someone
with standing asked), published as a permanent, immutable fact. Not a re-measured passport field:
once a WitnessRecord exists it is never recomputed, the same discipline `Passport`'s own docstring
holds historical passports to (requirement 3 there) - a check ran against the world at one moment,
and the record says what it found THEN.

THE BOUNDARY THIS MODULE ENFORCES, LITERALLY (spec 4.2-bis point 4, echoing 8.5: "an observer
holding no money cannot be an arbiter"). "A criterion not checkable by a machine is not accepted -
no record is created." `run_witness` RAISES for anything outside `SUPPORTED_CRITERIA` rather than
returning a record with some invented third result: a record that exists is a claim that a machine
checked something, and there is nothing weaker to publish about a criterion no machine could
evaluate.

WHAT IS MACHINE-CHECKABLE IN v0. The specification names three examples: a URL answers; an
artefact at a URL matches a declared hash; a test command with a deterministic exit. This module
ships the first two. THE THIRD IS DELIBERATELY NOT IMPLEMENTED: running an externally-named
command is arbitrary code execution on this host, triggered by a request from outside it - a
different order of decision than an SSRF-guarded GET, and shipping it as a shortcut inside this
ticket was not asked for and is not decided here (flagged to Fable/the operator; see the session's
own report). A criterion of that type hits `UnsupportedCriterion` exactly like a typo would - no
record, same as the specification requires for any non-machine-checkable criterion.

REPRODUCIBILITY, NOT JUST A NUMBER (ABI-5-3). Every check here resolves through
`src.collector.reachability`'s anonymous, credential-free GET - the exact channel this project
already uses for `service_endpoint` - so a third party who repeats the same GET at the same moment
reaches the same evidence this module reached. Nothing here carries an authorization header, a
token, or any state private to us.

WHAT IS DELIBERATELY NOT IN THIS RECORD. `witness_id, subject_id, criterion, result,
evidence_digest, checked_at, witnessed_fee_paid` is the WHOLE published schema (spec 4.2-bis point
4, quoted verbatim) - see `WitnessRecord.to_machine`. Who asked for the check is not part of it:
publishing a customer's or a subject's contact address on a permanent public page they did not
agree to have shown was not asked for, and this project already has a place for "who submitted
this and how do we reach them" (`web/functions/api/apply.js`'s KV record) - private storage, never
a public artefact. `scripts/witness.py` keeps that provenance in a separate, unpublished file; see
its own header for why.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.collector.reachability import (
    ArtifactTooLarge,
    ArtifactUnreachable,
    SSRFRefused,
    fetch_artifact,
    probe_reachable,
)

Result = Literal["PASS", "FAIL"]

SUPPORTED_CRITERIA = frozenset({"url_reachable", "artifact_hash"})
"""The machine-checkable criterion types this collector can evaluate today. See the module
docstring for why a third, spec-named example ("a test command with a deterministic exit") is not
in this set."""


class UnsupportedCriterion(ValueError):
    """The criterion's `type` is not one this collector can check by machine (spec 4.2-bis point
    4: "a criterion not checkable by a machine is not accepted"). Raising here - rather than
    returning a record with some third result - IS the refusal: no `WitnessRecord` is constructed,
    because no record is the correct outcome here, not a weaker one."""


@dataclass(frozen=True)
class WitnessRecord:
    """The published fact, and NOTHING else beyond it - see the module docstring for what this
    deliberately omits. Every field here appears verbatim in spec 4.2-bis point 4's schema."""
    witness_id: str
    subject_id: str
    criterion: dict
    result: Result
    evidence_digest: str
    checked_at: str
    witnessed_fee_paid: bool = False
    """ALWAYS False in v0 (spec 4.2-bis point 4: "until enabled - free with an explicit label").
    Turning this on for a real charge is a separate operator decision and the A-1 trigger (first
    revenue -> legal entity) - not a parameter this function accepts."""

    def to_machine(self) -> dict:
        return {
            "witness_id": self.witness_id,
            "subject_id": self.subject_id,
            "criterion": self.criterion,
            "result": self.result,
            "evidence_digest": self.evidence_digest,
            "checked_at": self.checked_at,
            "witnessed_fee_paid": self.witnessed_fee_paid,
        }


def _digest(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _check_url_reachable(criterion: dict, *, checked_at: str) -> tuple[Result, str]:
    url = criterion.get("url")
    if not isinstance(url, str) or not url:
        raise UnsupportedCriterion("url_reachable requires a non-empty 'url'")
    try:
        ok = probe_reachable(url)
    except SSRFRefused:
        # A criterion naming a URL that resolves privately is a legitimate FAIL, not a refusal to
        # accept the criterion TYPE - the type is machine-checkable, the address it names is not
        # one this collector will ever reach, which is exactly what "not reachable" means.
        ok = False
    result: Result = "PASS" if ok else "FAIL"
    return result, _digest("url_reachable", url, result, checked_at)


def _check_artifact_hash(criterion: dict, *, checked_at: str) -> tuple[Result, str]:
    url = criterion.get("url")
    expected = criterion.get("sha256")
    if not isinstance(url, str) or not url:
        raise UnsupportedCriterion("artifact_hash requires a non-empty 'url'")
    if not isinstance(expected, str) or not expected:
        raise UnsupportedCriterion("artifact_hash requires a non-empty 'sha256'")
    expected = expected.strip().lower()
    try:
        body = fetch_artifact(url)
    except (SSRFRefused, ArtifactUnreachable, ArtifactTooLarge) as e:
        # A LEGITIMATE FAIL, not "not accepted": the criterion TYPE is machine-checkable, the
        # attempt to check it just did not find the artefact claimed. Published as FAIL, same as a
        # forged hash below - both are the check running and finding the claim false, and spec
        # 4.2-bis point 4 requires a FAIL to publish exactly like a PASS, never to be suppressed.
        return "FAIL", _digest("artifact_hash", url, "unreachable", str(e), checked_at)
    actual = hashlib.sha256(body).hexdigest()
    result: Result = "PASS" if actual == expected else "FAIL"
    # The evidence digest IS the fetched artefact's own hash, not a hash of a description of it -
    # so a third party who fetches the same URL and gets the same bytes reaches the identical
    # published digest, whether the result was PASS or FAIL.
    return result, actual


_CHECKS = {
    "url_reachable": _check_url_reachable,
    "artifact_hash": _check_artifact_hash,
}


def run_witness(subject_id: str, criterion: dict, *, now: datetime | None = None) -> WitnessRecord:
    """Run ONE machine-checkable criterion and return the record to publish.

    Raises `UnsupportedCriterion` - and creates no record - for anything outside
    `SUPPORTED_CRITERIA`. Every other outcome, including every network failure, is a PASS or a
    FAIL: a check that ran and found the claim false is evidence, not an absence.
    """
    ctype = criterion.get("type")
    if ctype not in SUPPORTED_CRITERIA:
        raise UnsupportedCriterion(
            f"{ctype!r} is not machine-checkable by this collector: supported types are "
            f"{sorted(SUPPORTED_CRITERIA)}")
    checked_at = (now or datetime.now(timezone.utc)).isoformat()
    result, evidence_digest = _CHECKS[ctype](criterion, checked_at=checked_at)
    return WitnessRecord(
        witness_id=str(uuid.uuid4()),
        subject_id=subject_id,
        criterion=dict(criterion),
        result=result,
        evidence_digest=evidence_digest,
        checked_at=checked_at,
    )


def load_task_history(subject_id: str, witness_root: Path) -> list[dict]:
    """Every published `WitnessRecord` for `subject_id`, in the order they were run - read from
    the per-subject index `witness_root/by_subject/<slug>.json`, never by scanning every witness
    record ever published (keeps a cohort re-measure O(subjects), not O(all records ever run)).

    A subject with no index file has an empty history - the ordinary "nobody has asked yet"
    default, not an error: WitnessRecord v0 shipping with a working, tested mechanism and zero
    subjects who have used it yet is an honest state, the same one `service`/`service_endpoint`
    were published in after phase 1 (spec 4.2-bis point 1) before any subject had declared an
    `order_url`.
    """
    slug = subject_id.replace(":", "_").replace("/", "_")
    idx = witness_root / "by_subject" / f"{slug}.json"
    if not idx.exists():
        return []
    ids = json.loads(idx.read_text(encoding="utf-8"))
    records = []
    for wid in ids:
        f = witness_root / f"{wid}.json"
        if not f.exists():
            continue
        records.append(json.loads(f.read_text(encoding="utf-8"))["witness"])
    return records


def demo() -> None:
    """ponytail: smallest runnable self-check. No fixture server needed - the two checks are
    exercised through their own already-tested primitives (`probe_reachable`/`fetch_artifact`),
    against `.invalid` (RFC 2606: guaranteed never to resolve, so this needs no live network to be
    deterministic). This demo only proves the routing: an unsupported type is refused with no
    record, a supported one always returns a record shaped correctly."""
    refused = False
    try:
        run_witness("git:example/repo", {"type": "no_such_check"})
    except UnsupportedCriterion:
        refused = True
    assert refused, "an unsupported criterion type must raise UnsupportedCriterion"
    rec = run_witness("git:example/repo", {"type": "artifact_hash", "url": "https://x.invalid/a",
                                           "sha256": "0" * 64})
    assert rec.result == "FAIL"          # x.invalid never resolves - a real, reproducible failure
    assert rec.witnessed_fee_paid is False
    assert len(rec.witness_id) == 36
    rec2 = run_witness("git:example/repo", {"type": "url_reachable", "url": "https://x.invalid/a"})
    assert rec2.result == "FAIL"
    print("witness demo: ok")


if __name__ == "__main__":
    demo()
