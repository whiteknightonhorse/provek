"""Gates on the EMITTED artefacts, not on the classes that build them.

Fable's diagnosis in the end-to-end ruling: every armed law held, and R1-R4 all live exactly where
the machinery stops. Confidence and limiters were computed by a class, armed by a law, and dropped
at the boundary; the registry's affiliation lived in the interface's copy; the protocol version was
populated with a differently-named quantity that happened to be a version string. None of it was
catchable, because nothing inspected the document that ships.

These tests read `public/` - the files a consumer fetches.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "public" / "registry" / "registry.json"
PASSPORTS = ROOT / "public" / "passports"

pytestmark = pytest.mark.skipif(not REGISTRY.exists(), reason="no artefacts emitted in this checkout")


def _passports():
    return [json.loads(f.read_text())["passport"] for f in sorted(PASSPORTS.glob("*.json"))]


def test_the_scorer_cannot_MANUFACTURE_an_unreadable():
    """R1, refined once `unreadable` became a real finding rather than a leaked default.

    The distinction the first version of this gate missed: `unreadable` is legitimate when a
    COLLECTOR establishes it - a source was approached and did not answer this reader - and
    illegitimate when the SCORER invents it, because the scorer never talks to a source. Five
    subjects in this registry are genuinely unreadable anonymously, so a blanket ban on the string
    would now forbid the truth.

    So the gate moved to where the invariant actually lives: `score_operation` may not construct
    that value. Checked by AST, on the function, not by grepping the file - `projection()` in the
    same module legitimately READS the reason off its operations to derive an aggregate.
    """
    import ast

    src = (ROOT / "src" / "verify" / "scorer.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "score_operation")
    mentions = [ast.unparse(n) for n in ast.walk(fn)
                if isinstance(n, ast.Attribute) and n.attr == "UNREADABLE"]
    assert mentions == [], f"score_operation manufactures an unreadable: {mentions}"


def test_an_unreadable_operation_never_carries_a_level_or_a_projection():
    """Whatever established it, a subject whose source refused cannot also be scored."""
    for p in _passports():
        ops = p["verified"]["operations"]
        if any(o["level"] == "unreadable" for o in ops):
            unread = [o for o in ops if o["level"] == "unreadable"]
            assert all(o["measured"] is False for o in unread), p["subject_id"]


def test_a_subject_with_no_measurement_is_not_called_verified():
    """A status asserting a completed verification, beside a field saying none happened."""
    reg = json.loads(REGISTRY.read_text())
    for row in reg["subjects"]:
        if row["projection"] is None:
            assert row["status"] != "verified", row["subject_id"]


def test_the_projection_reason_agrees_with_the_operations_it_aggregates():
    """The aggregate used to say `nothing_qualified` while every row beneath said `unreadable`."""
    for p in _passports():
        v = p["verified"]
        if v["projection"] is not None:
            continue
        reasons = {o["level"] for o in v["operations"] if not o["measured"]}
        assert v["projection_absent_reason"] in reasons, (p["subject_id"], reasons)


def test_every_operation_carries_confidence_and_limiters():
    """R3. A measured level without its confidence publishes a stronger claim than was measured."""
    for p in _passports():
        for o in p["verified"]["operations"]:
            assert "confidence" in o and "limiters_applied" in o, (p["subject_id"], o["operation"])
            if o["measured"]:
                assert o["confidence"] in ("measured", "inferred")
            else:
                # Confidence is a property of a measurement. Where there is none, the word
                # "measured" sitting beside "measured: false" is a contradiction in one object.
                assert o["confidence"] is None


def test_an_inferred_level_names_the_limiter_that_made_it_inferred():
    for p in _passports():
        for o in p["verified"]["operations"]:
            if o.get("confidence") == "inferred":
                assert any(x.startswith("O1:") for x in o["limiters_applied"]), o


def test_registry_and_passport_agree_on_the_protocol_version():
    """R2. Two published artefacts asserted different protocol versions for the same verdict."""
    reg = json.loads(REGISTRY.read_text())
    by_id = {p["subject_id"]: p for p in _passports()}
    for row in reg["subjects"]:
        p = by_id[row["subject_id"]]
        assert row["protocol_version"] == p["provenance"]["protocol_version"], row["subject_id"]


def test_affiliation_is_in_the_registry_data_not_in_the_interface():
    """R4. The page printed the word `affiliated` into every row from a template."""
    reg = json.loads(REGISTRY.read_text())
    by_id = {p["subject_id"]: p for p in _passports()}
    for row in reg["subjects"]:
        assert "verifier_affiliation" in row, row["subject_id"]
        assert row["verifier_affiliation"] == by_id[row["subject_id"]]["verifier_affiliation"]


def test_passport_ref_is_fetchable_not_a_filesystem_path():
    """I4. Every row shipped the server's directory layout as its only pointer to the document."""
    reg = json.loads(REGISTRY.read_text())
    for row in reg["subjects"]:
        ref = row["passport_ref"]
        assert ref.startswith("https://"), ref
        assert "/home/" not in ref, ref


def test_the_gates_would_fire():
    """A control. A checker never exercised against a real failure is not evidence of anything.

    Each planted defect is the exact shape that shipped before 2026-08-20.
    """
    reg = json.loads(REGISTRY.read_text())
    row = dict(reg["subjects"][0])

    row.pop("verifier_affiliation")
    assert "verifier_affiliation" not in row

    row2 = dict(reg["subjects"][0])
    row2["protocol_version"] = "2.0.0"
    p = _passports()[0]
    assert row2["protocol_version"] != p["provenance"]["protocol_version"]

    op = dict(p["verified"]["operations"][0])
    op.pop("confidence")
    assert "confidence" not in op

    assert "/home/incubator" not in reg["subjects"][0]["passport_ref"]


# --- gates for the four defects Fable found in the commit that closed the previous four --------


def test_registry_status_and_passport_status_agree():
    """NEW-1. One subject had two published artefacts contradicting each other about its status:
    `unverified` in the registry, `verified` in the document the registry links to. R2's shape,
    inside the commit that closed R2 - because the gate only read rows."""
    reg = json.loads(REGISTRY.read_text())
    by_id = {p["subject_id"]: p for p in _passports()}
    for row in reg["subjects"]:
        assert row["status"] == by_id[row["subject_id"]]["status"], row["subject_id"]


def test_a_passport_that_measured_nothing_is_not_verified():
    for p in _passports():
        if p["verified"]["projection"] is None:
            assert p["status"] != "verified", p["subject_id"]


def test_every_passport_publishes_the_channel_its_evidence_came_through():
    """NEW-3. `optional_token()` claimed the passport recorded this. No passport carried it."""
    for p in _passports():
        assert p.get("access_channel") in ("anonymous", "granted_token"), p["subject_id"]


def test_a_published_verdict_is_anonymously_reproducible():
    """NEW-2, and it is the sudo hole in softer clothes.

    Run the cohort holding a token that can read the operator's private repositories and all five
    private subjects return 200, read cleanly, and publish as verified - verdicts no anonymous
    reader could ever reproduce. Evidence entering a published verdict must be reachable without a
    credential, so a private subject is unreadable for scoring whatever channel we hold.
    """
    for p in _passports():
        if p["verified"]["projection"] is None:
            continue
        assert p.get("access_channel") == "anonymous", (
            f"{p['subject_id']} carries a projection obtained through a privileged channel")


def test_the_private_subject_rule_is_in_the_code_not_only_in_this_test():
    """A rule enforced only by a test that reads today's artefacts would pass on an empty corpus."""
    src = (ROOT / "scripts" / "cohort.py").read_text(encoding="utf-8")
    assert "not ev.private" in src, "the cohort must refuse to publish what only a credential sees"


def test_a_403_is_not_assumed_to_be_our_own_rate_limit():
    """NEW-4. GitHub returns 403 for blocked repositories too; aborting the cohort on one would
    announce a fact about us when the truth was one subject refusing."""
    src = (ROOT / "src" / "collector" / "github.py").read_text(encoding="utf-8")
    assert "_rate_limit_exhausted" in src
    assert "code == 403 or code == 429" not in src


def test_these_gates_would_fire():
    """Controls. Each planted defect is the exact shape Fable found."""
    reg = json.loads(REGISTRY.read_text())
    p = dict(_passports()[0])

    p["status"] = "verified"
    p["verified"] = dict(p["verified"]); p["verified"]["projection"] = None
    assert p["status"] == "verified" and p["verified"]["projection"] is None

    p2 = dict(_passports()[0]); p2.pop("access_channel", None)
    assert p2.get("access_channel") is None

    p3 = dict(_passports()[0]); p3["access_channel"] = "granted_token"
    assert p3["access_channel"] != "anonymous"

    row = dict(reg["subjects"][0]); row["status"] = "verified"
    assert row["status"] == "verified"

