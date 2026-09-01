"""LAW #ONE-PLACE (Fable, 2026-09-01): the profile version and the "deployment collector does not
exist" reason each lived in three-plus places with drifted values.

Measured before this fix:
  src/pipeline.py               PROFILE_VERSION = "1.0.0"
  scripts/cohort.py             Provenance("1.0.0", "1.1.0", ...)
  scripts/measure_qm2.py:100    Provenance("1.0.0", "1.0.0", 30)

- three different profile-version strings for one fact. And "collector not implemented" was typed
literally in `scripts/cohort.py` (both branches) while `src/pipeline.py` and
`scripts/measure_qm2.py` silently OMITTED the `deployment` key from their own coverage maps -
under-reporting what was out of reach rather than agreeing on the reason.

`scripts/cohort.py` performs live GitHub calls at MODULE SCOPE and must never be imported by a
test (see `tests/test_cohort_l4_requires_signature.py`'s docstring for the same constraint). Every
check below reads source text with `ast`, never `import`.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = sorted([*(ROOT / "src").rglob("*.py"), *(ROOT / "scripts").rglob("*.py")])
CANON = ROOT / "src" / "passport" / "passport.py"
COVERAGE_MODULE = ROOT / "src" / "verify" / "control_map.py"
EMITTERS = (ROOT / "src" / "pipeline.py", ROOT / "scripts" / "cohort.py",
           ROOT / "scripts" / "measure_qm2.py")


def _provenance_literal_offenders() -> list[str]:
    """Every `Provenance(...)` call outside its own module whose protocol/profile version arrives
    as a string LITERAL rather than an imported name."""
    offenders = []
    for path in SOURCES:
        if path == CANON:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "Provenance"):
                continue
            checked = list(node.args[:2]) + [kw.value for kw in node.keywords
                                             if kw.arg in ("protocol_version", "profile_version")]
            for a in checked:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    offenders.append(f"{path.relative_to(ROOT)}:{node.lineno} -> {ast.unparse(node)}")
                    break
    return offenders


def test_no_call_site_hardcodes_the_profile_or_protocol_version():
    offenders = _provenance_literal_offenders()
    assert offenders == [], (
        "PROTOCOL_VERSION/PROFILE_VERSION must be imported from src.passport.passport, never "
        "retyped as a literal at a Provenance(...) call site:\n  " + "\n  ".join(offenders))


def test_the_canonical_versions_live_in_one_named_place():
    src = CANON.read_text(encoding="utf-8")
    assert 'PROTOCOL_VERSION = "1.0.0"' in src
    assert 'PROFILE_VERSION = "1.1.0"' in src, (
        "1.1.0 is what is actually published (time-windowed evidence, platform closure, "
        "ratified 2026-08-25) - the canonical value must say so")


def test_every_emitter_imports_the_canonical_versions():
    for path in EMITTERS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "src.passport.passport":
                imported.update(a.name for a in node.names)
        assert {"PROTOCOL_VERSION", "PROFILE_VERSION"} <= imported, (
            f"{path.relative_to(ROOT)} does not import the canonical version constants")


def _deployment_reason_offenders() -> list[str]:
    offenders = []
    for path in SOURCES:
        if path == COVERAGE_MODULE:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and node.value == "collector not implemented":
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    return offenders


def test_the_deployment_not_collected_reason_lives_in_one_named_place():
    offenders = _deployment_reason_offenders()
    assert offenders == [], (
        "'collector not implemented' must come from "
        "src.verify.control_map.DEPLOYMENT_NOT_COLLECTED, never be retyped as a second literal:\n"
        "  " + "\n  ".join(offenders))


def test_coverage_is_constructed_in_one_place():
    """`Coverage(...)` the dataclass may only be built inside `build_coverage()` - every emitter
    calls that function rather than hand-rolling its own coverage map."""
    offenders = []
    for path in SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "Coverage" and path != COVERAGE_MODULE):
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert offenders == [], (
        f"Coverage(...) built outside {COVERAGE_MODULE.relative_to(ROOT)}, bypassing "
        "build_coverage():\n  " + "\n  ".join(offenders))


def test_every_emitter_calls_build_coverage():
    for path in EMITTERS:
        assert "build_coverage(" in path.read_text(encoding="utf-8"), (
            f"{path.relative_to(ROOT)} does not call the shared coverage constructor")


def test_these_gates_would_fire():
    """Controls, planted as the exact shapes these checks exist to forbid."""
    planted_provenance = ast.parse('PROV = Provenance("1.0.0", "1.0.0", 30)\n')
    call = next(n for n in ast.walk(planted_provenance)
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "Provenance")
    assert any(isinstance(a, ast.Constant) and isinstance(a.value, str) for a in call.args[:2]), (
        "the Provenance-literal gate cannot see a planted hardcoded version")

    planted_string = ast.parse('OUT = {"deployment": "collector not implemented"}\n')
    assert any(isinstance(n, ast.Constant) and n.value == "collector not implemented"
              for n in ast.walk(planted_string)), (
        "the deployment-reason gate cannot see a planted literal")

    planted_coverage = ast.parse('c = Coverage([], {}, "x")\n')
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "Coverage"
              for n in ast.walk(planted_coverage)), (
        "the Coverage-construction gate cannot see a planted call")
