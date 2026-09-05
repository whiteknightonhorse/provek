"""LAW-TEMPLATE-WAS-RUN (ADR-0011, D-57) - a template's page may be emitted only after a witnessed
dry run: run once, in a fresh directory, against a real coding agent, recorded at
`evidence/TEMPLATE-RUN-<slug>.json` keyed to the sha256 of the SKILL.md body at run time.

Three states, never collapsed (CLAUDE.md invariant 1 applied to a template's own freshness):
no record ("ready-to-use template" with nobody having tried it - the exact unfalsified-claim
defect this product exists to detect, aimed at itself), a hash mismatch (the body moved after the
recorded run - the page must say the dry run predates the current revision, never show it as
fresh), and a matching record (publishable).

Phase 0 ships this gate against ZERO real templates (templates/README.md, D-18's precedent for a
specification preceding its instances), so every case is proven with fixtures under
tests/fixtures/template_run/, each shown able to fail before the real (currently empty) tree is
trusted.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
EVIDENCE = ROOT / "evidence"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "template_run"

MISSING = "missing_record"
MISMATCH = "hash_mismatch"
OK = "ok"


def body_sha256(skill_md: Path) -> str:
    return hashlib.sha256(skill_md.read_bytes()).hexdigest()


def check_run_records(templates_root: Path, evidence_root: Path) -> dict[str, str]:
    """slug -> one of MISSING / MISMATCH / OK. Templates with no SKILL.md are not templates and
    are skipped rather than reported - this law binds a witnessed dry run, not directory shape."""
    results: dict[str, str] = {}
    if not templates_root.exists():
        return results
    for slug_dir in sorted(p for p in templates_root.iterdir() if p.is_dir()):
        skill = slug_dir / "SKILL.md"
        if not skill.exists():
            continue
        slug = slug_dir.name
        record_path = evidence_root / f"TEMPLATE-RUN-{slug}.json"
        if not record_path.exists():
            results[slug] = MISSING
            continue
        record = json.loads(record_path.read_text(encoding="utf-8"))
        results[slug] = OK if record.get("body_sha256") == body_sha256(skill) else MISMATCH
    return results


# --- control: each state is proven reachable before the real tree is trusted -----------------

def test_a_template_with_no_evidence_record_is_reported_missing():
    scenario = FIXTURES / "missing"
    results = check_run_records(scenario / "templates", scenario / "evidence")
    assert results == {"some-template": MISSING}


def test_a_stale_evidence_record_is_reported_as_a_mismatch_not_a_pass():
    scenario = FIXTURES / "mismatch"
    results = check_run_records(scenario / "templates", scenario / "evidence")
    assert results == {"some-template": MISMATCH}


def test_a_matching_evidence_record_is_reported_ok():
    scenario = FIXTURES / "ok"
    results = check_run_records(scenario / "templates", scenario / "evidence")
    assert results == {"some-template": OK}


def test_missing_and_mismatch_are_distinguished_states():
    """The one assertion this whole law exists for: they must never collapse into each other."""
    missing = check_run_records(FIXTURES / "missing" / "templates", FIXTURES / "missing" / "evidence")
    mismatch = check_run_records(FIXTURES / "mismatch" / "templates", FIXTURES / "mismatch" / "evidence")
    assert missing["some-template"] != mismatch["some-template"]


# --- the real tree ------------------------------------------------------------------------

def test_no_real_template_is_missing_its_dry_run():
    """Phase 0 ships zero templates; this stays armed as templates land in later phases."""
    results = check_run_records(TEMPLATES, EVIDENCE)
    bad = {slug: state for slug, state in results.items() if state != OK}
    assert not bad, f"template(s) without a valid witnessed dry run: {bad}"
