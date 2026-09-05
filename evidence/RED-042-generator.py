#!/usr/bin/env python3
"""Produces evidence/RED-042-a-template-naming-the-instrument-or-skipping-its-dry-run-would-have-shipped.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). T-70 Phase 0 (ADR-0011, D-57)
added two laws that both bind `templates/`, currently empty: `LAW-TEMPLATE-NAMES-NO-INSTRUMENT`
(`tests/test_templates_never_name_the_instrument.py`) and `LAW-TEMPLATE-WAS-RUN`
(`tests/test_template_was_run.py`). Both test files already carry pytest-level controls against
static fixtures under `tests/fixtures/` - those prove the CHECKER FUNCTIONS can fail, run every
time `pytest tests` does. ADR-0011 line 36 makes a stronger, separate promise: "A planted violation
must turn the check red; the red run is kept under `evidence/`." That promise was still open after
Phase 0's own review (ruling-2): the last RED artefact on disk was RED-041, naming neither law.
This file is what closes it - a REAL plant in the actual (currently empty) `templates/` tree, the
actual test suite run against it as a subprocess, the verbatim red output kept, then the plant
removed and the suite proven clean again. Not the fixtures under `tests/fixtures/` restated: those
already run inside `pytest tests` on every push and would still pass unchanged if a real defect
ever put a real bad template into the real tree - this generator is the artefact that a plant IN
THAT TREE was actually tried, once, and both laws actually caught it.

ONE MUTATION, NOT TWO SEPARATE ONES (RED-040's precedent). A single planted template - one
`SKILL.md` that names Provek's own passport AND has no dry-run evidence record - turns both
`test_no_real_template_names_the_instrument` and `test_no_real_template_is_missing_its_dry_run`
red at once, because a template that should never exist on this surface is invalid on every axis
simultaneously. Two mutations proving two unrelated facts about the same object would be the
restatement RED-032's own generator already refuses; one plant that a real bad template would
actually look like is the right shape here.

WHAT THIS FILE DOES TO THE WORKING TREE, AND WHAT IT PROMISES ABOUT IT. It creates one directory
under `templates/`, proves both real-tree tests go red because of it (and only it - each output is
checked to name the planted slug), deletes the directory in a `finally`, and refuses to write the
artefact unless the full suite is provably green both before the plant and after its removal. A run
that leaves the plant behind, or that cannot restore a green suite, writes nothing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-042-a-template-naming-the-instrument-or-skipping-its-dry-run-would-have-shipped.txt"
TEST_FILES = [
    "tests/test_templates_never_name_the_instrument.py",
    "tests/test_template_was_run.py",
]

PLANT_SLUG = "_red042-planted-agent"
PLANT_DIR = ROOT / "templates" / PLANT_SLUG
PLANT_SKILL = PLANT_DIR / "SKILL.md"
PLANT_TEXT = (
    "---\n"
    f"name: {PLANT_SLUG}\n"
    "description: planted by evidence/RED-042-generator.py to prove both template laws can fail\n"
    "---\n\n"
    "## What to build\n\n"
    "This SKILL.md was planted to check that Provek's own passport and registry are never named\n"
    "by a real template, and that a template with no witnessed dry run is never treated as\n"
    "publishable. It carries no evidence/TEMPLATE-RUN record anywhere.\n"
)


def run_tests() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", *TEST_FILES, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    if PLANT_DIR.exists():
        print(f"REFUSED: {PLANT_DIR} already exists - clean up before running this.")
        return 1

    rc_before, out_before = run_tests()
    if rc_before != 0:
        print(f"REFUSED: the two template-law test files are not green before any plant "
              f"(exit {rc_before}).\n{out_before}")
        return 1

    try:
        PLANT_DIR.mkdir()
        PLANT_SKILL.write_text(PLANT_TEXT, encoding="utf-8")
        if "provek" not in PLANT_TEXT.lower() or "passport" not in PLANT_TEXT.lower():
            print("REFUSED: the plant does not actually name the instrument.")
            return 1

        rc_red, out_red = run_tests()
    finally:
        PLANT_SKILL.unlink(missing_ok=True)
        if PLANT_DIR.exists():
            PLANT_DIR.rmdir()

    if PLANT_DIR.exists():
        print(f"REFUSED: {PLANT_DIR} was not removed.")
        return 1
    if rc_red == 0:
        print(f"REFUSED: planting the violation did not turn the suite red (exit {rc_red}).\n{out_red}")
        return 1
    if "test_no_real_template_names_the_instrument" not in out_red:
        print(f"REFUSED: the red run does not name LAW-TEMPLATE-NAMES-NO-INSTRUMENT's real-tree test.\n{out_red}")
        return 1
    if "test_no_real_template_is_missing_its_dry_run" not in out_red:
        print(f"REFUSED: the red run does not name LAW-TEMPLATE-WAS-RUN's real-tree test.\n{out_red}")
        return 1
    if PLANT_SLUG not in out_red:
        print(f"REFUSED: the red run does not name the planted slug.\n{out_red}")
        return 1

    rc_after, out_after = run_tests()
    if rc_after != 0:
        print(f"REFUSED: the suite is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
        return 1

    body = f"""# RED-042 - a template naming the instrument, or skipping its dry run, would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-042-generator.py, checked in beside this file so the run below can be
# repeated rather than believed. Closes the gap ruling-2 found in T-70 Phase 0's own review: ADR-0011
# line 36 promises a kept red run under evidence/ for this gate; the fixture-level pytest controls
# in the two test files below prove the CHECKER can fail, but until this file existed no artefact
# proved a plant IN THE REAL (currently empty) templates/ tree actually turned the real-tree tests
# red. One planted template - naming Provek's own passport, and shipped with no dry-run record -
# fails both laws at once, because a template that should never exist here is wrong on every axis
# a real bad template would be wrong on.
#
# SUBJECT: tests/test_templates_never_name_the_instrument.py, arming LAW-TEMPLATE-NAMES-NO-INSTRUMENT.
# SUBJECT: tests/test_template_was_run.py, arming LAW-TEMPLATE-WAS-RUN.
# Both laws: ADR-0011, D-57.

{"=" * 100}
BEFORE THE PLANT - `python3 -m pytest {' '.join(TEST_FILES)} -q`, exit {rc_before}
{"=" * 100}

{out_before}

{"=" * 100}
THE PLANT - templates/{PLANT_SLUG}/SKILL.md, verbatim (no evidence/TEMPLATE-RUN-{PLANT_SLUG}.json alongside it)
{"=" * 100}

{PLANT_TEXT}
{"=" * 100}
WITH THE PLANT IN PLACE - `python3 -m pytest {' '.join(TEST_FILES)} -q`, exit {rc_red}
{"=" * 100}

{out_red}

{"=" * 100}
AFTER THE PLANT WAS REMOVED - `python3 -m pytest {' '.join(TEST_FILES)} -q`, exit {rc_after}
{"=" * 100}

{out_after}
"""
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
