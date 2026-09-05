#!/usr/bin/env python3
"""Produces evidence/RED-044-a-dangling-fragment-link-site-wide-would-have-shipped.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). T-78 added
`tests/test_site_wide_anchors_resolve.py::test_no_fragment_link_anywhere_points_at_an_anchor_the_target_page_does_not_emit`
- the first check in this repository that resolves a `#fragment` against the actual `id`s the
TARGET page emits, rather than stripping the fragment and checking the route only (that half was
already covered by `test_build_links_resolve.py` / `test_notes_entrance.py`). The file's own
`test_the_check_catches_a_removed_anchor` proves the checker FUNCTION can fail, on a `tmp_path`
scratch copy, every time `pytest tests` runs - that is a unit-level proof, not the artefact
ADR-0011 line 36 and RED-042/043's precedent both require: a plant IN THE REAL BUILT TREE, the real
test run as a subprocess against it, the verbatim red output kept, then the plant removed and the
suite proven clean again. Ruling-2 on T-78 (`78-texts-for-the-incubator-funnel.ruling-1.md`) named
this gap explicitly: "no evidence/RED-* artefact for either new gate".

THE PLANT: `web/dist/method/index.html` carries `id="the-order-link"`, the one anchor every other
funnel surface links to by fragment (`/method/#the-order-link` from Landing, Apply, Registry and
Phase2 in source; MEASURED-005's inventory records which of those survive prerendering). Renaming
that one id - the same mutation the file's own scratch-copy control performs - is done here on the
real `web/dist`, restored from the original bytes in a `finally` regardless of outcome.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-044-a-dangling-fragment-link-site-wide-would-have-shipped.txt"
TEST_FILE = "tests/test_site_wide_anchors_resolve.py"
TEST_NODE = f"{TEST_FILE}::test_no_fragment_link_anywhere_points_at_an_anchor_the_target_page_does_not_emit"
METHOD_INDEX = ROOT / "web" / "dist" / "method" / "index.html"
PLANTED_ID = 'id="the-order-link"'
RENAMED_ID = 'id="the-order-link-red044-planted"'


def run_test() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_NODE, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    if not METHOD_INDEX.is_file():
        print(f"REFUSED: {METHOD_INDEX} is absent - run `npm run build` in web/ first "
              "(scripts/push.sh does exactly that before this generator would run).")
        return 1

    original = METHOD_INDEX.read_bytes()

    rc_before, out_before = run_test()
    if rc_before != 0:
        print(f"REFUSED: {TEST_NODE} is not green before any plant (exit {rc_before}).\n{out_before}")
        return 1

    try:
        text = original.decode("utf-8")
        if PLANTED_ID not in text:
            print(f"REFUSED: {PLANTED_ID!r} not found in {METHOD_INDEX} - nothing to rename.")
            return 1
        mutated = text.replace(PLANTED_ID, RENAMED_ID, 1).encode("utf-8")
        METHOD_INDEX.write_bytes(mutated)

        rc_red, out_red = run_test()
    finally:
        METHOD_INDEX.write_bytes(original)

    if METHOD_INDEX.read_bytes() != original:
        print(f"REFUSED: {METHOD_INDEX} was not restored to its original bytes.")
        return 1
    if rc_red == 0:
        print(f"REFUSED: planting the rename did not turn the test red (exit {rc_red}).\n{out_red}")
        return 1
    if "the-order-link" not in out_red:
        print(f"REFUSED: the red run does not name the broken anchor.\n{out_red}")
        return 1

    rc_after, out_after = run_test()
    if rc_after != 0:
        print(f"REFUSED: the test is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
        return 1

    body = f"""# RED-044 - a dangling fragment link site-wide would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-044-generator.py, checked in beside this file so the run below can be
# repeated rather than believed. Closes the gap ruling-2 on T-78 found: the new site-wide anchor
# gate carried a `tmp_path`-scratch control that proves the CHECKER FUNCTION can fail, but no
# artefact proving a plant IN THE REAL BUILT TREE turns the real test red. `id="the-order-link"` -
# the one anchor `/method/` emits that Landing, Apply, Registry and Phase2 all reference by
# fragment - was renamed in the real `web/dist/method/index.html`, restored unconditionally in a
# `finally`.
#
# SUBJECT: {TEST_NODE}.
# CHANNEL PLANTED: web/dist/method/index.html, id="the-order-link" -> id="the-order-link-red044-planted".

{"=" * 100}
BEFORE THE PLANT - `python3 -m pytest {TEST_NODE} -q`, exit {rc_before}
{"=" * 100}

{out_before}

{"=" * 100}
THE PLANT - the real id="the-order-link" in web/dist/method/index.html renamed to
id="the-order-link-red044-planted", restored from the original bytes in a `finally` regardless of
outcome
{"=" * 100}

{"=" * 100}
WITH THE PLANT IN PLACE - `python3 -m pytest {TEST_NODE} -q`, exit {rc_red}
{"=" * 100}

{out_red}

{"=" * 100}
AFTER THE PLANT WAS REMOVED - `python3 -m pytest {TEST_NODE} -q`, exit {rc_after}
{"=" * 100}

{out_after}
"""
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
