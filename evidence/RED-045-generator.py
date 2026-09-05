#!/usr/bin/env python3
"""Produces evidence/RED-045-incubator-as-a-title-or-an-isolated-mention-would-have-shipped.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). T-78's ruling
(`78-texts-for-the-incubator-funnel.ruling-1.md`) admits "incubator" only lowercase, descriptive,
one sentence per funnel surface, beside the "holds no funds" limit - never a title, H1, nav label
or meta. `tests/test_incubator_word_is_descriptive_only.py` enforces both halves and already
carries two `tmp_path`-scratch controls proving each CHECKER FUNCTION can fail - a unit-level proof
that runs every `pytest tests` invocation. Ruling-2 named the gap those controls do not close: no
artefact proves a plant IN THE REAL BUILT TREE turns the REAL tests red, the same standard RED-042
and RED-043 hold every other ordered gate to.

TWO PLANTS, RUN SEQUENTIALLY, EACH RESTORED BEFORE THE NEXT - because the ruling's two halves are
enforced by two separate real-tree tests, not one:

  1. `test_incubator_is_never_capitalised_or_placed_in_a_title_heading_nav_or_meta_tag` - the real
     `web/dist/index.html`'s `<title>` gets a capitalised "Incubator" prepended (the same plant the
     file's own scratch control performs).
  2. `test_each_funnel_surface_uses_incubator_exactly_once_beside_the_funds_limit` - a second,
     isolated lowercase "incubator" mention with no "holds no funds" nearby is appended just before
     `</main>` in the same real `web/dist/index.html`.

Not combined into one mutation (unlike RED-042's precedent): here the two rules are already
partitioned onto two independently-failing test functions by the gate's own design (the module
docstring says so explicitly), so one file per rule would restate nothing.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-045-incubator-as-a-title-or-an-isolated-mention-would-have-shipped.txt"
TEST_FILE = "tests/test_incubator_word_is_descriptive_only.py"
TEST_TITLE = f"{TEST_FILE}::test_incubator_is_never_capitalised_or_placed_in_a_title_heading_nav_or_meta_tag"
TEST_BESIDE = f"{TEST_FILE}::test_each_funnel_surface_uses_incubator_exactly_once_beside_the_funds_limit"
LANDING_INDEX = ROOT / "web" / "dist" / "index.html"


def run_test(node: str) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", node, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def plant_and_run(node: str, mutate) -> tuple[int, str, int, str, int, str]:
    """Runs (before, plant+red, after) for one node. Returns the three (rc, out) pairs flattened."""
    original = LANDING_INDEX.read_bytes()
    rc_before, out_before = run_test(node)
    if rc_before != 0:
        raise RuntimeError(f"REFUSED: {node} is not green before any plant (exit {rc_before}).\n{out_before}")
    try:
        text = original.decode("utf-8")
        mutated = mutate(text)
        if mutated == text:
            raise RuntimeError(f"REFUSED: the plant for {node} did not change the file.")
        LANDING_INDEX.write_bytes(mutated.encode("utf-8"))
        rc_red, out_red = run_test(node)
    finally:
        LANDING_INDEX.write_bytes(original)
    if LANDING_INDEX.read_bytes() != original:
        raise RuntimeError(f"REFUSED: {LANDING_INDEX} was not restored to its original bytes.")
    if rc_red == 0:
        raise RuntimeError(f"REFUSED: planting for {node} did not turn the test red (exit {rc_red}).\n{out_red}")
    rc_after, out_after = run_test(node)
    if rc_after != 0:
        raise RuntimeError(f"REFUSED: {node} is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
    return rc_before, out_before, rc_red, out_red, rc_after, out_after


def main() -> int:
    if not LANDING_INDEX.is_file():
        print(f"REFUSED: {LANDING_INDEX} is absent - run `npm run build` in web/ first "
              "(scripts/push.sh does exactly that before this generator would run).")
        return 1

    def plant_title(text: str) -> str:
        return text.replace("<title>", "<title>Incubator ", 1)

    def plant_isolated_mention(text: str) -> str:
        return text.replace(
            "</main>",
            '<p class="sr-only">This is an incubator for RED-045 purposes only.</p></main>',
            1,
        )

    try:
        b1_rc, b1_out, r1_rc, r1_out, a1_rc, a1_out = plant_and_run(TEST_TITLE, plant_title)
        b2_rc, b2_out, r2_rc, r2_out, a2_rc, a2_out = plant_and_run(TEST_BESIDE, plant_isolated_mention)
    except RuntimeError as e:
        print(str(e))
        return 1

    if "title" not in r1_out and "capitalised" not in r1_out:
        print(f"REFUSED: the red run for the title/capitalisation half does not name either offending placement.\n{r1_out}")
        return 1
    if not re.search(r"beside_limit|holds no funds|/'", r2_out) and "beside" not in r2_out.lower():
        # the assertion message embeds the reading dict, which always carries 'beside_limit'
        if "beside_limit" not in r2_out:
            print(f"REFUSED: the red run for the isolated-mention half does not name the beside-the-limit reading.\n{r2_out}")
            return 1

    body = f"""# RED-045 - incubator as a title or an isolated mention would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-045-generator.py, checked in beside this file so the two runs below can
# be repeated rather than believed. Closes the gap ruling-2 on T-78 found: the new
# incubator-is-a-description gate carried two `tmp_path`-scratch controls proving each CHECKER
# FUNCTION can fail, but no artefact proving a plant IN THE REAL BUILT TREE turns the REAL tests
# red. Two plants, run sequentially against the real web/dist/index.html, each restored before the
# next.
#
# SUBJECT: {TEST_FILE}, both halves of the ruling.

{"=" * 100}
HALF 1 - {TEST_TITLE}
Plant: <title> gets "Incubator " prepended in the real web/dist/index.html.
{"=" * 100}

--- before the plant, exit {b1_rc} ---
{b1_out}

--- with the plant in place, exit {r1_rc} ---
{r1_out}

--- after the plant was removed, exit {a1_rc} ---
{a1_out}

{"=" * 100}
HALF 2 - {TEST_BESIDE}
Plant: a second, isolated lowercase "incubator" mention with no "holds no funds" nearby, appended
just before </main> in the real web/dist/index.html.
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
