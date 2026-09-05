#!/usr/bin/env python3
"""Produces evidence/RED-048-incubator-back-on-the-landing-or-isolated-on-build-would-have-shipped.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). Fable, T-03 ruling-2
(`03-landing-never-names-the-agents.ruling-2.md`, D2) narrowed `FUNNEL_ROUTES` in
`tests/test_incubator_word_is_descriptive_only.py` from four surfaces to three (`/apply/`,
`/build/`, `/registry/`) - the landing's own copy of `INCUBATOR_SENTENCE` was retired as a
duplicate of `/build/`'s "What follows" section - and added
`test_landing_never_uses_incubator_in_main`, holding `/` to exactly ZERO uses of "incubator" in
`<main>`. The file's own `tmp_path`-scratch controls prove the CHECKER FUNCTIONS can fail; this
artefact is the real-tree counterpart RED-044/045/046 established as the standard: a plant in the
REAL `web/dist`, the real tests run as subprocesses against it, the verbatim red output kept, then
each plant removed and the suite proven clean again.

TWO PLANTS, RUN SEQUENTIALLY, EACH RESTORED BEFORE THE NEXT:

  1. `INCUBATOR_SENTENCE`'s own text is planted into the real `web/dist/index.html`'s `<main>` -
     the exact regression D2 forbids: the word coming back to the landing. Turns
     `test_landing_never_uses_incubator_in_main` red (count 1, not 0).

  2. An isolated "incubator" mention (no "holds no funds" nearby) is planted into the real
     `web/dist/build/index.html`'s `<main>`, beside the page's own real, compliant use. Turns
     `test_each_funnel_surface_uses_incubator_exactly_once_beside_the_funds_limit` red (count 2 on
     `/build/`, not 1).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / (
    "RED-048-incubator-back-on-the-landing-or-isolated-on-build-would-have-shipped.txt"
)
TEST_FILE = "tests/test_incubator_word_is_descriptive_only.py"
LANDING_TEST_NODE = f"{TEST_FILE}::test_landing_never_uses_incubator_in_main"
FUNNEL_TEST_NODE = (
    f"{TEST_FILE}::test_each_funnel_surface_uses_incubator_exactly_once_beside_the_funds_limit"
)
HOME_PAGE = ROOT / "web" / "dist" / "index.html"
BUILD_PAGE = ROOT / "web" / "dist" / "build" / "index.html"

INCUBATOR_PLANT = (
    '<p class="sr-only">That whole path is what we mean by an AI agent incubator: it holds no '
    "funds, and there is no cohort to join.</p>"
)
ISOLATED_PLANT = '<p class="sr-only">This is an incubator for testing purposes only.</p>'


def run_test(node: str) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", node, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def plant_and_run(path: Path, node: str, plant_html: str) -> tuple[int, str, int, str, int, str]:
    original = path.read_bytes()
    rc_before, out_before = run_test(node)
    if rc_before != 0:
        raise RuntimeError(f"REFUSED: {node} is not green before any plant (exit {rc_before}).\n{out_before}")
    try:
        text = original.decode("utf-8")
        if "</main>" not in text:
            raise RuntimeError(f"REFUSED: no </main> found in {path}.")
        mutated = text.replace("</main>", plant_html + "</main>", 1)
        if mutated == text:
            raise RuntimeError("REFUSED: the plant did not change the file.")
        path.write_bytes(mutated.encode("utf-8"))
        rc_red, out_red = run_test(node)
    finally:
        path.write_bytes(original)
    if path.read_bytes() != original:
        raise RuntimeError(f"REFUSED: {path} was not restored to its original bytes.")
    if rc_red == 0:
        raise RuntimeError(f"REFUSED: the plant did not turn {node} red (exit {rc_red}).\n{out_red}")
    rc_after, out_after = run_test(node)
    if rc_after != 0:
        raise RuntimeError(f"REFUSED: {node} is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
    return rc_before, out_before, rc_red, out_red, rc_after, out_after


def main() -> int:
    if not HOME_PAGE.is_file() or not BUILD_PAGE.is_file():
        print(f"REFUSED: {HOME_PAGE} or {BUILD_PAGE} is absent - run `npm run build` in web/ "
              "first (scripts/push.sh does exactly that before this generator would run).")
        return 1

    try:
        b1_rc, b1_out, r1_rc, r1_out, a1_rc, a1_out = plant_and_run(
            HOME_PAGE, LANDING_TEST_NODE, INCUBATOR_PLANT
        )
        b2_rc, b2_out, r2_rc, r2_out, a2_rc, a2_out = plant_and_run(
            BUILD_PAGE, FUNNEL_TEST_NODE, ISOLATED_PLANT
        )
    except RuntimeError as e:
        print(str(e))
        return 1

    if "should carry no" not in r1_out:
        print(f"REFUSED: the red run for the landing plant does not name the broken check.\n{r1_out}")
        return 1
    if "/build/" not in r2_out:
        print(f"REFUSED: the red run for the build plant does not name the broken surface.\n{r2_out}")
        return 1

    body = f"""# RED-048 - incubator back on the landing, or isolated on /build/, would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-048-generator.py, checked in beside this file so the two runs below can
# be repeated rather than believed. Closes the gap left after T-03 ruling-2 (D2) narrowed
# FUNNEL_ROUTES to three surfaces and added a zero-count rule for the landing: the file's own
# tmp_path-scratch controls prove the checker functions can fail, but no artefact proved a plant IN
# THE REAL BUILT TREE turns the REAL tests red, the standard RED-044/045/046 hold the other new
# gates in this repository to.
#
# SUBJECTS: {LANDING_TEST_NODE}; {FUNNEL_TEST_NODE}.

{"=" * 100}
PLANT 1 - INCUBATOR_SENTENCE's own text planted into the real web/dist/index.html's <main>,
the exact regression D2 forbids: the word coming back to the landing.
{"=" * 100}

--- before the plant, exit {b1_rc} ---
{b1_out}

--- with the plant in place, exit {r1_rc} ---
{r1_out}

--- after the plant was removed, exit {a1_rc} ---
{a1_out}

{"=" * 100}
PLANT 2 - an isolated "incubator" mention (no "holds no funds" nearby) planted into the real
web/dist/build/index.html's <main>, beside the page's own real, compliant use.
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
