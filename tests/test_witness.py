"""Phase 2 - WitnessRecord v0 (spec 4.2-bis point 4). Mandatory controls named in the operator's
own brief: a non-machine criterion is refused with a reason and creates no record; a forged hash
is a real, published FAIL, never suppressed; the check is anonymously reproducible (no credential,
same evidence for anyone repeating it).

Network calls are monkeypatched exactly the way `tests/test_phase2_service.py` already does for
`reachability.py` - no real network dependency, and the mocked world is what makes "reproducible"
testable at all: two independent calls against the identical mocked world must agree.
"""
from __future__ import annotations

import json

import pytest

import src.collector.reachability as reach
from src.witness.witness import (
    UnsupportedCriterion,
    WitnessRecord,
    load_task_history,
    run_witness,
)


def _fake_curl_status(status: int, location: str | None = None):
    def _fake_run(cmd, **kwargs):
        class R:
            returncode = 0
            stdout = f"{status}\n{location or ''}"
            stderr = ""
        return R()
    return _fake_run


def _fake_curl_body(status: int, body: bytes):
    """Writes `body` to the `-o` path curl was given, the way `_one_hop_capture` expects."""
    def _fake_run(cmd, **kwargs):
        out_path = cmd[cmd.index("-o") + 1]
        with open(out_path, "wb") as f:
            f.write(body)
        class R:
            returncode = 0
            stdout = f"{status}\n"
            stderr = ""
        return R()
    return _fake_run


@pytest.fixture(autouse=True)
def _public_ip(monkeypatch):
    monkeypatch.setattr(reach, "resolve_public_ip", lambda host: "93.184.216.34")


def test_MANDATORY_CONTROL_a_non_machine_criterion_is_refused_with_no_record():
    with pytest.raises(UnsupportedCriterion):
        run_witness("git:example/repo", {"type": "run_a_shell_command", "command": "echo hi"})
    # A criterion missing its type entirely is the same refusal, not a crash.
    with pytest.raises(UnsupportedCriterion):
        run_witness("git:example/repo", {})


def test_url_reachable_pass(monkeypatch):
    monkeypatch.setattr(reach.subprocess, "run", _fake_curl_status(200))
    rec = run_witness("git:example/repo", {"type": "url_reachable", "url": "https://example.com/x"})
    assert rec.result == "PASS"
    assert rec.witnessed_fee_paid is False
    assert rec.subject_id == "git:example/repo"


def test_url_reachable_fail(monkeypatch):
    monkeypatch.setattr(reach.subprocess, "run", _fake_curl_status(404))
    rec = run_witness("git:example/repo", {"type": "url_reachable", "url": "https://example.com/x"})
    assert rec.result == "FAIL"


def test_MANDATORY_CONTROL_forged_hash_is_a_real_FAIL_not_suppressed(monkeypatch):
    monkeypatch.setattr(reach.subprocess, "run", _fake_curl_body(200, b"the real artefact bytes"))
    rec = run_witness("git:example/repo", {
        "type": "artifact_hash", "url": "https://example.com/build.tar",
        "sha256": "0" * 64,   # forged - does not match the real bytes' hash
    })
    assert rec.result == "FAIL", "a forged hash must publish as FAIL, never be silently dropped"
    assert rec.evidence_digest, "a FAIL still carries evidence - the actual hash that was computed"


def test_artifact_hash_pass_on_matching_digest(monkeypatch):
    body = b"the real artefact bytes"
    import hashlib
    correct = hashlib.sha256(body).hexdigest()
    monkeypatch.setattr(reach.subprocess, "run", _fake_curl_body(200, body))
    rec = run_witness("git:example/repo", {
        "type": "artifact_hash", "url": "https://example.com/build.tar", "sha256": correct,
    })
    assert rec.result == "PASS"
    assert rec.evidence_digest == correct


def test_artifact_hash_unreachable_url_is_a_fail_not_an_unsupported_criterion(monkeypatch):
    """The criterion TYPE is machine-checkable; the attempt simply found nothing there. That is a
    FAIL, never `UnsupportedCriterion` - the boundary that exception guards is about the SHAPE of
    the criterion, not about what the network happened to return."""
    def _refuse(cmd, **kwargs):
        class R:
            returncode = 6   # curl: could not resolve host
            stdout = ""
            stderr = "resolve failed"
        return R()
    monkeypatch.setattr(reach.subprocess, "run", _refuse)
    rec = run_witness("git:example/repo", {
        "type": "artifact_hash", "url": "https://example.com/build.tar", "sha256": "a" * 64,
    })
    assert rec.result == "FAIL"


def test_MANDATORY_CONTROL_reproducible_same_world_same_verdict(monkeypatch):
    """ABI-5-3: the SAME mocked world (no credential, no hidden state) run twice must agree - the
    property that makes an anonymous third party's re-run trustworthy at all."""
    body = b"identical artefact bytes"
    import hashlib
    correct = hashlib.sha256(body).hexdigest()
    monkeypatch.setattr(reach.subprocess, "run", _fake_curl_body(200, body))
    r1 = run_witness("git:example/repo",
                     {"type": "artifact_hash", "url": "https://example.com/x", "sha256": correct})
    r2 = run_witness("git:example/repo",
                     {"type": "artifact_hash", "url": "https://example.com/x", "sha256": correct})
    assert r1.result == r2.result == "PASS"
    assert r1.evidence_digest == r2.evidence_digest


def test_no_credential_in_the_underlying_request(monkeypatch):
    """Same discipline as `test_probe_reachable_is_get_only_and_ssrf_pinned` in
    tests/test_phase2_service.py, applied to the artifact fetch: GET only, no header carrying a
    token this collector holds - the mechanical proof behind "anonymously reproducible"."""
    seen = {}

    def _capture(cmd, **kwargs):
        seen["cmd"] = cmd
        out_path = cmd[cmd.index("-o") + 1]
        with open(out_path, "wb") as f:
            f.write(b"x")
        class R:
            returncode = 0
            stdout = "200\n"
            stderr = ""
        return R()

    monkeypatch.setattr(reach.subprocess, "run", _capture)
    run_witness("git:example/repo", {
        "type": "artifact_hash", "url": "https://example.com/x", "sha256": "a" * 64})
    cmd = seen["cmd"]
    assert "--request" in cmd and cmd[cmd.index("--request") + 1] == "GET"
    assert not any(tok in ("-H", "--header", "-u", "--user") for tok in cmd), (
        "the artefact fetch must carry no auth header or credential - a check that needed one "
        "would not be repeatable by an anonymous third party")


def test_MANDATORY_CONTROL_chunked_response_over_the_cap_is_still_caught(monkeypatch):
    """Fable's Defect 2 (design circle, 2026-09-02): curl's `--max-filesize` does not bound a
    response with no `Content-Length` (a chunked transfer) - measured live, a 5 MB chunked body
    passed a 2 MB `--max-filesize` with exit 0. This fakes exactly that: curl reports success
    (returncode 0, as it genuinely does for a chunked transfer it never refused) while writing a
    body larger than `MAX_ARTIFACT_BYTES` to the `-o` path - the second enforcement path
    (`os.path.getsize` after the transfer) must catch what the first one missed."""
    oversized = b"x" * (reach.MAX_ARTIFACT_BYTES + 1)

    def _chunked_bypass(cmd, **kwargs):
        out_path = cmd[cmd.index("-o") + 1]
        with open(out_path, "wb") as f:
            f.write(oversized)
        class R:
            returncode = 0    # curl did NOT refuse - this is the bypass being simulated
            stdout = "200\n"
            stderr = ""
        return R()

    monkeypatch.setattr(reach.subprocess, "run", _chunked_bypass)
    with pytest.raises(reach.ArtifactTooLarge):
        reach.fetch_artifact("https://example.com/big")
    # And through the witness checker, this is a FAIL, not a crash - the same "a machine-checkable
    # criterion that could not be verified is a real FAIL" rule the SSRF/unreachable path holds.
    rec = run_witness("git:example/repo", {
        "type": "artifact_hash", "url": "https://example.com/big", "sha256": "a" * 64})
    assert rec.result == "FAIL"


def test_witness_record_to_machine_is_exactly_the_published_schema():
    rec = WitnessRecord(
        witness_id="w1", subject_id="git:example/repo",
        criterion={"type": "url_reachable", "url": "https://example.com"},
        result="PASS", evidence_digest="abc", checked_at="2026-09-02T00:00:00+00:00")
    m = rec.to_machine()
    assert set(m.keys()) == {"witness_id", "subject_id", "criterion", "result",
                             "evidence_digest", "checked_at", "witnessed_fee_paid"}
    assert m["witnessed_fee_paid"] is False
    # Round-trips through JSON exactly, since that IS the artefact `scripts/witness.py` writes.
    json.dumps(m)


def test_load_task_history_empty_for_unknown_subject(tmp_path):
    assert load_task_history("git:nobody/here", tmp_path) == []


def test_load_task_history_reads_the_index_in_order(tmp_path):
    (tmp_path / "by_subject").mkdir(parents=True)
    (tmp_path / "by_subject" / "git_example_repo.json").write_text(json.dumps(["w1", "w2"]))
    (tmp_path / "w1.json").write_text(json.dumps({"witness": {
        "witness_id": "w1", "subject_id": "git:example/repo",
        "criterion": {"type": "url_reachable", "url": "https://example.com"},
        "result": "PASS", "evidence_digest": "d1", "checked_at": "t1",
        "witnessed_fee_paid": False}}))
    (tmp_path / "w2.json").write_text(json.dumps({"witness": {
        "witness_id": "w2", "subject_id": "git:example/repo",
        "criterion": {"type": "url_reachable", "url": "https://example.com"},
        "result": "FAIL", "evidence_digest": "d2", "checked_at": "t2",
        "witnessed_fee_paid": False}}))
    hist = load_task_history("git:example/repo", tmp_path)
    assert [h["witness_id"] for h in hist] == ["w1", "w2"]
