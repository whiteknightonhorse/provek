#!/usr/bin/env python3
"""Produces evidence/RED-046-landing-missing-or-mismatched-a-template-would-have-shipped.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). T-03's ruling
(`03-landing-never-names-the-agents.ruling-1.md`, D-59) requires the landing's "What you can build
today" section to name every published template, in `templates/manifest.json`'s own order, with
its own `businessOperation` text. `tests/test_landing_names_every_template.py` already carries a
`tmp_path`-scratch control proving the CHECKER FUNCTION (`_check`) can fail against a copy of the
real build. This artefact closes the gap RED-044/045 were written against on the two prior tasks:
no `tmp_path` control proves a plant IN THE REAL BUILT TREE (the real `web/dist/index.html`, not a
copy of it) turns the REAL test function red - the same standard every other ordered gate here is
held to.

TWO PLANTS, RUN SEQUENTIALLY, EACH RESTORED BEFORE THE NEXT, both against the real
`web/dist/index.html` and both read by the same real-tree test function,
`test_landing_names_every_published_template_in_manifest_order_with_its_own_operation`:

  1. The first template's entire `<li>` row is removed from the "What you can build today"
     section - the count and the order both break.
  2. The row is restored, then a second plant swaps one template's `businessOperation` text for
     another's - the order stays intact, only the text is wrong.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-046-landing-missing-or-mismatched-a-template-would-have-shipped.txt"
TEST_FILE = "tests/test_landing_names_every_template.py"
TEST_NODE = (
    f"{TEST_FILE}::test_landing_names_every_published_template_in_manifest_order_with_its_own_operation"
)
LANDING_INDEX = ROOT / "web" / "dist" / "index.html"


def run_test() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_NODE, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def plant_and_run(mutate) -> tuple[int, str, int, str, int, str]:
    original = LANDING_INDEX.read_bytes()
    rc_before, out_before = run_test()
    if rc_before != 0:
        raise RuntimeError(f"REFUSED: {TEST_NODE} is not green before any plant (exit {rc_before}).\n{out_before}")
    try:
        text = original.decode("utf-8")
        mutated = mutate(text)
        if mutated == text:
            raise RuntimeError("REFUSED: the plant did not change the file.")
        LANDING_INDEX.write_bytes(mutated.encode("utf-8"))
        rc_red, out_red = run_test()
    finally:
        LANDING_INDEX.write_bytes(original)
    if LANDING_INDEX.read_bytes() != original:
        raise RuntimeError(f"REFUSED: {LANDING_INDEX} was not restored to its original bytes.")
    if rc_red == 0:
        raise RuntimeError(f"REFUSED: the plant did not turn {TEST_NODE} red (exit {rc_red}).\n{out_red}")
    rc_after, out_after = run_test()
    if rc_after != 0:
        raise RuntimeError(f"REFUSED: {TEST_NODE} is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
    return rc_before, out_before, rc_red, out_red, rc_after, out_after


def main() -> int:
    if not LANDING_INDEX.is_file():
        print(f"REFUSED: {LANDING_INDEX} is absent - run `npm run build` in web/ first "
              "(scripts/push.sh does exactly that before this generator would run).")
        return 1

    def plant_remove_row(text: str) -> str:
        m = re.search(r"What you can build today</h2>([\s\S]*?)</section>", text)
        if not m:
            return text
        li = re.search(r"<li>[\s\S]*?</li>", m.group(1))
        if not li:
            return text
        return text.replace(li.group(0), "", 1)

    def plant_swap_operation(text: str) -> str:
        rows = re.findall(r'<a href="/build/[a-z0-9-]+/"[^>]*>[\s\S]*?</a>\s*—\s*([^<]*)</li>', text)
        if len(rows) < 2:
            return text
        op_a, op_b = rows[0].strip(), rows[1].strip()
        return text.replace(f"— {op_a}</li>", f"— {op_b}</li>", 1)

    try:
        b1_rc, b1_out, r1_rc, r1_out, a1_rc, a1_out = plant_and_run(plant_remove_row)
        b2_rc, b2_out, r2_rc, r2_out, a2_rc, a2_out = plant_and_run(plant_swap_operation)
    except RuntimeError as e:
        print(str(e))
        return 1

    if "order_or_membership" not in r1_out and "landing_vs_templates_json" not in r1_out:
        print(f"REFUSED: the red run for the removed-row plant does not name the broken check.\n{r1_out}")
        return 1
    if "business_operation_text" not in r2_out:
        print(f"REFUSED: the red run for the swapped-operation plant does not name the broken check.\n{r2_out}")
        return 1

    body = f"""# RED-046 - landing missing or mismatched a template would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-046-generator.py, checked in beside this file so the two runs below can
# be repeated rather than believed. Closes the gap RED-044 and RED-045 were written against on the
# prior two tasks: the new gate carried a `tmp_path`-scratch control proving its CHECKER FUNCTION
# can fail, but no artefact proved a plant IN THE REAL BUILT TREE turns the REAL test red. Two
# plants, run sequentially against the real web/dist/index.html, each restored before the next.
#
# SUBJECT: {TEST_NODE}.

{"=" * 100}
PLANT 1 - remove the first template's row entirely from the real web/dist/index.html.
{"=" * 100}

--- before the plant, exit {b1_rc} ---
{b1_out}

--- with the plant in place, exit {r1_rc} ---
{r1_out}

--- after the plant was removed, exit {a1_rc} ---
{a1_out}

{"=" * 100}
PLANT 2 - swap the first template's businessOperation text for the second's, in the real
web/dist/index.html. The row count and order stay correct; only the text is wrong.
{"=" * 100}

--- before the plant, exit {b2_rc} ---
{b2_out}

--- with the plant in place, exit {r2_rc} ---
{r2_out}

--- after the plant was removed, exit {a2_rc} ---
{a2_out}
"""
    OUT.write_text(body, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
