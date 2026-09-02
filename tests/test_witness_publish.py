"""`scripts/witness.py`'s publish step: what gets written where, and - just as load-bearing - what
does NOT get written to the public artefact. Every write goes through `root` (a temp directory
here), never the live `public/witness/` tree - see `publish_record`'s own docstring for why that
parameter exists.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location("witness_cli", ROOT / "scripts" / "witness.py")
witness_cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(witness_cli)

from src.witness.witness import WitnessRecord  # noqa: E402


def _rec(**over):
    base = dict(witness_id="11111111-1111-1111-1111-111111111111", subject_id="git:example/repo",
               criterion={"type": "url_reachable", "url": "https://example.com"},
               result="PASS", evidence_digest="deadbeef", checked_at="2026-09-02T00:00:00+00:00")
    base.update(over)
    return WitnessRecord(**base)


def test_published_record_is_byte_identical_in_both_trees(tmp_path):
    rec = _rec()
    paths = witness_cli.publish_record(rec, customer_contact="c@example.com",
                                       subject_contact="s@example.com", root=tmp_path)
    a = paths["emitted"].read_bytes()
    b = paths["served"].read_bytes()
    assert a == b, "the emitted and served copies of a published WitnessRecord must be identical"


def test_published_record_carries_ONLY_the_seven_schema_fields(tmp_path):
    rec = _rec()
    paths = witness_cli.publish_record(rec, customer_contact="c@example.com",
                                       subject_contact="s@example.com", root=tmp_path)
    doc = json.loads(paths["emitted"].read_text(encoding="utf-8"))["witness"]
    assert set(doc.keys()) == {"witness_id", "subject_id", "criterion", "result",
                               "evidence_digest", "checked_at", "witnessed_fee_paid"}


def test_MANDATORY_CONTROL_contacts_never_reach_the_published_artefact(tmp_path):
    """The whole reason `publish_record` takes the two contacts as separate arguments rather than
    folding them into the record: they must be unreachable from the public JSON by construction,
    not merely omitted by convention. A contact string planted here that turned up in either
    published copy would be the exact privacy leak the module docstring promises does not happen."""
    rec = _rec()
    paths = witness_cli.publish_record(
        rec, customer_contact="secret-customer@example.com",
        subject_contact="secret-subject@example.com", root=tmp_path)
    for key in ("emitted", "served"):
        text = paths[key].read_text(encoding="utf-8")
        assert "secret-customer@example.com" not in text
        assert "secret-subject@example.com" not in text
    # The contacts DO exist somewhere, in the private request file - "never published" is not
    # "never recorded". A dispute about who asked for this still needs an answer.
    req = json.loads(paths["request"].read_text(encoding="utf-8"))
    assert req["customer_contact"] == "secret-customer@example.com"
    assert req["subject_contact"] == "secret-subject@example.com"


def test_the_request_file_is_never_mirrored_to_the_served_tree(tmp_path):
    rec = _rec()
    witness_cli.publish_record(rec, customer_contact="c@example.com",
                               subject_contact="s@example.com", root=tmp_path)
    served = tmp_path / "web" / "public" / "data" / "witness"
    assert not (served / "_requests").exists(), (
        "the private request directory must not exist under the served tree at all")


def test_per_subject_index_accumulates_in_order(tmp_path):
    r1 = _rec(witness_id="11111111-1111-1111-1111-111111111111")
    r2 = _rec(witness_id="22222222-2222-2222-2222-222222222222", result="FAIL")
    witness_cli.publish_record(r1, customer_contact="c", subject_contact="s", root=tmp_path)
    witness_cli.publish_record(r2, customer_contact="c", subject_contact="s", root=tmp_path)
    idx = json.loads((tmp_path / "public" / "witness" / "by_subject"
                      / "git_example_repo.json").read_text(encoding="utf-8"))
    assert idx == ["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"]


def test_MANDATORY_CONTROL_forged_hash_end_to_end_is_published_not_hidden(tmp_path, monkeypatch):
    """The operator's own named control, run through the full CLI path rather than only the
    checker: a run that finds a forged hash must WRITE a FAIL record, not exit quietly with
    nothing published."""
    import src.collector.reachability as reach

    body = b"the real bytes"

    def _fake_run(cmd, **kwargs):
        out_path = cmd[cmd.index("-o") + 1]
        with open(out_path, "wb") as f:
            f.write(body)
        class R:
            returncode = 0
            stdout = "200\n"
            stderr = ""
        return R()

    monkeypatch.setattr(reach, "resolve_public_ip", lambda host: "93.184.216.34")
    monkeypatch.setattr(reach.subprocess, "run", _fake_run)

    from src.witness.witness import run_witness
    rec = run_witness("git:example/repo", {
        "type": "artifact_hash", "url": "https://example.com/build.tar", "sha256": "f" * 64})
    assert rec.result == "FAIL"
    paths = witness_cli.publish_record(rec, customer_contact="c@example.com",
                                       subject_contact="s@example.com", root=tmp_path)
    doc = json.loads(paths["served"].read_text(encoding="utf-8"))["witness"]
    assert doc["result"] == "FAIL", "a forged hash must be published as FAIL on the served copy too"
    assert doc["evidence_digest"] == hashlib.sha256(body).hexdigest()
