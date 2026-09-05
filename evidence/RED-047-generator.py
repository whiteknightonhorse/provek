#!/usr/bin/env python3
"""Produces evidence/RED-047-the-two-phases-out-of-order-would-have-shipped.txt.

WHAT THIS PROVES (invariant 5: "the section exists" is not a test). Fable, T-03 ruling-2
(`03-landing-never-names-the-agents.ruling-2.md`, D1) rewrote
`tests/test_design_handoff_form.py::test_home_states_the_two_phases_in_order` to read the two
funnel phases out of `FUNNEL_SENTENCE`'s own words ("request verification" before "take orders")
after the landing's separate "Step 1 / Step 2" strip - which used to carry the same two phases in
its own headings - was retired (D1: it restated, in different words, what the sentence already
says, and sat orphaned below the registry rail on wide screens). The rewritten test has no
`tmp_path`-scratch control of its own; this artefact is that control, run against the REAL
`web/dist/index.html`, the real test run as a subprocess against it, the verbatim red output kept,
then the plant removed and the suite proven clean again - the same standard RED-044/045/046 hold
the other new gates to.

THE PLANT: the real `web/dist/index.html` carries `FUNNEL_SENTENCE` verbatim, "...request
verification for a free passport, and take orders once the registry lists you." - "request
verification" appears (lowercase, mid-sentence) strictly before "take orders". Reversing that one
clause's word order in the emitted HTML - "...take orders once the registry lists you, and request
verification for a free passport." - keeps both phrases present (so the test does not fail for the
wrong reason, an absent phrase) but makes "take orders" appear first, which is exactly the ordering
defect the test exists to catch.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-047-the-two-phases-out-of-order-would-have-shipped.txt"
TEST_FILE = "tests/test_design_handoff_form.py"
TEST_NODE = f"{TEST_FILE}::test_home_states_the_two_phases_in_order"
HOME_PAGE = ROOT / "web" / "dist" / "index.html"

ORIGINAL_CLAUSE = (
    "request verification for a free "
    "passport, and take orders once the registry lists you."
)
REVERSED_CLAUSE = (
    "take orders once the registry lists you, and request verification for a free passport."
)


def run_test() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_NODE, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def main() -> int:
    if not HOME_PAGE.is_file():
        print(f"REFUSED: {HOME_PAGE} is absent - run `npm run build` in web/ first "
              "(scripts/push.sh does exactly that before this generator would run).")
        return 1

    original = HOME_PAGE.read_bytes()

    rc_before, out_before = run_test()
    if rc_before != 0:
        print(f"REFUSED: {TEST_NODE} is not green before any plant (exit {rc_before}).\n{out_before}")
        return 1

    try:
        text = original.decode("utf-8")
        if ORIGINAL_CLAUSE not in text:
            print(f"REFUSED: {ORIGINAL_CLAUSE!r} not found in {HOME_PAGE} - nothing to reverse.")
            return 1
        mutated = text.replace(ORIGINAL_CLAUSE, REVERSED_CLAUSE, 1).encode("utf-8")
        HOME_PAGE.write_bytes(mutated)

        rc_red, out_red = run_test()
    finally:
        HOME_PAGE.write_bytes(original)

    if HOME_PAGE.read_bytes() != original:
        print(f"REFUSED: {HOME_PAGE} was not restored to its original bytes.")
        return 1
    if rc_red == 0:
        print(f"REFUSED: reversing the clause did not turn the test red (exit {rc_red}).\n{out_red}")
        return 1
    if "not stated in order" not in out_red:
        print(f"REFUSED: the red run does not name the broken assertion.\n{out_red}")
        return 1

    rc_after, out_after = run_test()
    if rc_after != 0:
        print(f"REFUSED: the test is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
        return 1

    body = f"""# RED-047 - the two phases out of order would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-047-generator.py, checked in beside this file so the run below can be
# repeated rather than believed. T-03 ruling-2 (D1) rewrote
# test_home_states_the_two_phases_in_order to read the two funnel phases out of FUNNEL_SENTENCE's
# own words rather than out of the now-retired Step 1/2 strip's headings; this closes the gap of
# there being no real-tree red run for that rewritten assertion, the same standard RED-044/045/046
# hold the other new gates in this repository to.
#
# SUBJECT: {TEST_NODE}.
# CHANNEL PLANTED: web/dist/index.html, the FUNNEL_SENTENCE clause's word order reversed so
# "take orders" appears before "request verification".

{"=" * 100}
BEFORE THE PLANT - `python3 -m pytest {TEST_NODE} -q`, exit {rc_before}
{"=" * 100}

{out_before}

{"=" * 100}
THE PLANT - in the real web/dist/index.html:
  {ORIGINAL_CLAUSE!r}
  ->
  {REVERSED_CLAUSE!r}
restored from the original bytes in a `finally` regardless of outcome.
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
