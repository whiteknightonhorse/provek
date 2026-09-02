"""`scripts/witness.py`'s publish step: what gets written where, and - just as load-bearing - what
does NOT get written to the public artefact OR to the git-tracked tree. Every write goes through
`public_root`/`private_root` (temp directories here), never the live trees.

Two mandatory controls in this file exist because Fable's design-circle review found the first
version of this module wrong: `test_MANDATORY_CONTROL_private_request_root_is_never_inside_a_git_
tree` and `test_MANDATORY_CONTROL_default_private_root_is_outside_the_repository` guard the exact
defect (the private request file living inside `~/incubator`, the tree `push.sh` publishes to a
public GitHub remote) that a "never mirrored, never read by the site" claim alone did not catch.
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


def _publish(rec, tmp_path, **over):
    kwargs = dict(customer_contact="c@example.com", subject_contact="s@example.com",
                 joint_intent_evidence="customer email of 2026-09-02, subject email of 2026-09-01",
                 public_root=tmp_path / "repo", private_root=tmp_path / "private")
    kwargs.update(over)
    return witness_cli.publish_record(rec, **kwargs)


def test_published_record_is_byte_identical_in_both_trees(tmp_path):
    paths = _publish(_rec(), tmp_path)
    a = paths["emitted"].read_bytes()
    b = paths["served"].read_bytes()
    assert a == b, "the emitted and served copies of a published WitnessRecord must be identical"


def test_published_record_carries_ONLY_the_seven_schema_fields(tmp_path):
    paths = _publish(_rec(), tmp_path)
    doc = json.loads(paths["emitted"].read_text(encoding="utf-8"))["witness"]
    assert set(doc.keys()) == {"witness_id", "subject_id", "criterion", "result",
                               "evidence_digest", "checked_at", "witnessed_fee_paid"}


def test_MANDATORY_CONTROL_contacts_never_reach_the_published_artefact(tmp_path):
    """The whole reason `publish_record` takes the two contacts as separate arguments rather than
    folding them into the record: they must be unreachable from the public JSON by construction,
    not merely omitted by convention. A contact string planted here that turned up in either
    published copy would be the exact privacy leak the module docstring promises does not happen."""
    paths = _publish(_rec(), tmp_path, customer_contact="secret-customer@example.com",
                     subject_contact="secret-subject@example.com")
    for key in ("emitted", "served"):
        text = paths[key].read_text(encoding="utf-8")
        assert "secret-customer@example.com" not in text
        assert "secret-subject@example.com" not in text
    # The contacts DO exist somewhere, in the private request file - "never published" is not
    # "never recorded". A dispute about who asked for this still needs an answer.
    req = json.loads(paths["request"].read_text(encoding="utf-8"))
    assert req["customer_contact"] == "secret-customer@example.com"
    assert req["subject_contact"] == "secret-subject@example.com"


def test_MANDATORY_CONTROL_private_request_root_is_never_inside_a_git_tree(tmp_path):
    """Fable's Defect 1: the first version of this module wrote the private request file to
    `public_root / "public" / "witness" / "_requests"` - INSIDE the tree `push.sh` publishes to a
    public GitHub remote. This proves the write for a realistic layout (a `.git` directory
    actually present at `public_root`) never lands under it, however `private_root` is later
    changed - the assertion is on where the byte landed, not on the code's intent."""
    public_root = tmp_path / "repo"
    (public_root / ".git").mkdir(parents=True)   # a REAL git tree marker, not just a directory
    private_root = tmp_path / "private"
    rec = _rec()
    paths = witness_cli.publish_record(
        rec, customer_contact="c", subject_contact="s",
        joint_intent_evidence="customer email of 2026-09-02, subject email of 2026-09-01",
        public_root=public_root, private_root=private_root)
    request_path = paths["request"].resolve()
    assert not str(request_path).startswith(str(public_root.resolve())), (
        f"the private request file {request_path} landed inside the git-tracked tree "
        f"{public_root.resolve()} - the exact leak path Fable's review found")
    assert request_path.exists()
    doc = json.loads(request_path.read_text(encoding="utf-8"))
    assert doc["joint_intent_evidence"] == "customer email of 2026-09-02, subject email of 2026-09-01"


def test_MANDATORY_CONTROL_default_private_root_is_outside_the_repository():
    """Same control as above, against the REAL default (`private_request_root()`, no override) -
    proves production behaviour, not only what a test-supplied `private_root` happens to do."""
    default = witness_cli.private_request_root().resolve()
    repo_root = ROOT.resolve()
    assert not str(default).startswith(str(repo_root)), (
        f"the default private request root {default} is inside the repository {repo_root} - "
        "publishing a real record would write private contact data into the git tree")


def test_the_request_file_is_never_mirrored_to_the_served_tree(tmp_path):
    paths = _publish(_rec(), tmp_path)
    served = paths["emitted"].parent.parent.parent / "data" / "witness"
    assert not (served / "_requests").exists(), (
        "the private request directory must not exist under the served tree at all")


def test_per_subject_index_accumulates_in_order(tmp_path):
    r1 = _rec(witness_id="11111111-1111-1111-1111-111111111111")
    r2 = _rec(witness_id="22222222-2222-2222-2222-222222222222", result="FAIL")
    _publish(r1, tmp_path)
    _publish(r2, tmp_path)
    idx = json.loads((tmp_path / "repo" / "public" / "witness" / "by_subject"
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
    paths = _publish(rec, tmp_path)
    doc = json.loads(paths["served"].read_text(encoding="utf-8"))["witness"]
    assert doc["result"] == "FAIL", "a forged hash must be published as FAIL on the served copy too"
    assert doc["evidence_digest"] == hashlib.sha256(body).hexdigest()
