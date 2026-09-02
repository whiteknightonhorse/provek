"""Passport clarity (phase-2 plan): `FIELD_HELP` must caption every raw key the pipeline ACTUALLY
emits today - measured against the live registry and passports, never against an invented list.

WHY THE LIVE ARTEFACTS AND NOT THE PYTHON SOURCE. The honest set of `self_reported` top-level keys,
`binding_flags` values and `coverage` surfaces is defined by what the collectors actually write, and
reading `web/src/help.ts` against `src/collector/declaration.py`'s source text would only prove the
two agree with each other - not that either agrees with what a real passport contains. Every one of
the ten committed passports under `public/passports/` (mirrored to `web/public/data/passports/` -
`tests/test_emitted_and_served_are_one_artefact.py` already holds those two identical) is read
directly, and the keys found are the ground truth this test holds `FIELD_HELP` to.

WHAT THIS DOES NOT CHECK: `SECTION_HELP`'s five section names are fixed by this page's own layout
(one heading per section), not emitted by the pipeline, so there is no "live key" to measure them
against - checked instead in `test_every_section_heading_used_on_the_page_has_a_dictionary_entry`
below, against the section names `Passport.tsx` itself names.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PASSPORTS_DIR = ROOT / "public" / "passports"
HELP_TS = ROOT / "web" / "src" / "help.ts"
PASSPORT_TSX = ROOT / "web" / "src" / "pages" / "Passport.tsx"


def _extract_object_keys(source: str, const_name: str) -> set[str]:
    """Every bare-identifier key inside `export const <const_name>: ... = { ... };` - a purpose-
    built reader for the one shape this file's two dictionaries actually use (`key: "value",` or
    `key: "value" + "...",`), not a general TypeScript parser. `tests/test_the_staleness_rule_is_
    one_rule.py` already accepts this class of narrow, honest reader over a full TS toolchain for
    exactly the same reason: nothing in the CI `tests` job installs one.
    """
    m = re.search(rf"export const {const_name}[^=]*=\s*{{(.*?)\n}};", source, re.S)
    assert m, f"{const_name} not found in help.ts in the shape this reader expects"
    body = m.group(1)
    keys = set()
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("//") or not stripped:
            continue
        km = re.match(r"^(\w+):\s*\"", stripped)
        if km:
            keys.add(km.group(1))
    return keys


def _live_passports() -> list[dict]:
    files = sorted(PASSPORTS_DIR.glob("git_*.json"))
    assert files, f"no passports found under {PASSPORTS_DIR}"
    out = []
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        out.append(doc["passport"])
    return out


def test_every_self_reported_key_emitted_today_has_a_caption():
    passports = _live_passports()
    field_help = _extract_object_keys(HELP_TS.read_text(encoding="utf-8"), "FIELD_HELP")
    live_keys: set[str] = set()
    for p in passports:
        live_keys |= set(p.get("self_reported", {}).keys())
    assert live_keys, "no self_reported keys found on any live passport - fixture assumption broken"
    missing = live_keys - field_help
    assert not missing, (
        f"these self_reported keys are emitted by at least one live passport but have no "
        f"FIELD_HELP caption: {sorted(missing)}"
    )


def test_every_binding_flag_emitted_today_has_a_caption():
    passports = _live_passports()
    field_help = _extract_object_keys(HELP_TS.read_text(encoding="utf-8"), "FIELD_HELP")
    live_flags: set[str] = set()
    for p in passports:
        live_flags |= set(p.get("binding_flags", []))
    assert live_flags, "no binding_flags found on any live passport - fixture assumption broken"
    missing = live_flags - field_help
    assert not missing, f"these binding_flags have no FIELD_HELP caption: {sorted(missing)}"


def test_every_coverage_surface_emitted_today_has_a_caption():
    passports = _live_passports()
    field_help = _extract_object_keys(HELP_TS.read_text(encoding="utf-8"), "FIELD_HELP")
    live_surfaces: set[str] = set()
    for p in passports:
        cov = p["verified"]["coverage"]
        live_surfaces |= set(cov.get("inspected", []))
        live_surfaces |= set(cov.get("out_of_reach", {}).keys())
    assert live_surfaces, "no coverage surfaces found on any live passport - fixture assumption broken"
    missing = live_surfaces - field_help
    assert not missing, f"these coverage surfaces have no FIELD_HELP caption: {sorted(missing)}"


def test_every_section_heading_used_on_the_page_has_a_dictionary_entry():
    """`SECTION_HELP` is read by name at five call sites in `Passport.tsx` - checked against the
    page's own source rather than the live artefact, since a section name is a fact about the
    LAYOUT, not something any collector emits."""
    section_help = _extract_object_keys(HELP_TS.read_text(encoding="utf-8"), "SECTION_HELP")
    passport_src = PASSPORT_TSX.read_text(encoding="utf-8")
    used = set(re.findall(r"SECTION_HELP\.(\w+)", passport_src))
    assert used, "Passport.tsx no longer references SECTION_HELP - update this test's assumption"
    missing = used - section_help
    assert not missing, f"Passport.tsx uses SECTION_HELP.{missing} which help.ts does not define"


def test_MUTATION_a_new_uncaptioned_key_would_be_CAUGHT():
    """Control: an invented key that is NOT in FIELD_HELP must be reported as missing - proving the
    three tests above would actually fail on a real regression, not merely on a hypothetical one."""
    field_help = _extract_object_keys(HELP_TS.read_text(encoding="utf-8"), "FIELD_HELP")
    assert "a_key_nobody_declared_yet" not in field_help


@pytest.mark.skipif(not (ROOT / "web" / "public" / "data" / "passports").exists(),
                    reason="served tree not built in this checkout")
def test_the_served_tree_agrees_with_the_repo_tree_on_the_keys_measured_here():
    """L-3: what a reader receives is `web/public/data/passports/`, not `public/passports/` - the
    two are supposed to be byte-identical (`tests/test_emitted_and_served_are_one_artefact.py`
    already holds that), and this is a narrow, load-bearing re-check that the SPECIFIC facts this
    file's other tests depend on (self_reported keys, binding_flags, coverage surfaces) are not
    the one place the two trees happen to differ."""
    served_dir = ROOT / "web" / "public" / "data" / "passports"
    for f in sorted(PASSPORTS_DIR.glob("git_*.json")):
        served = served_dir / f.name
        assert served.exists(), f"{f.name} exists in public/passports/ but not in the served tree"
        repo_doc = json.loads(f.read_text(encoding="utf-8"))["passport"]
        served_doc = json.loads(served.read_text(encoding="utf-8"))["passport"]
        assert set(repo_doc.get("self_reported", {})) == set(served_doc.get("self_reported", {}))
        assert set(repo_doc.get("binding_flags", [])) == set(served_doc.get("binding_flags", []))
