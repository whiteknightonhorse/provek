#!/usr/bin/env python3
"""Produces evidence/RED-061-a-page-missing-the-x-account-would-have-shipped.txt.

T-PX-01-x-account-link (PROVEK-x-link-0928.ruling-1.md): `tests/test_x_account_link.py` sweeps
every emitted page for `twitter:site` and the footer link to `https://x.com/provek_dev`. Both
plants below run against the REAL `web/dist` (never a `tmp_path` copy), because the two things
this gate exists to catch are per-page rewrite bugs in the real build pipeline, not bugs a checker
function could be shown in isolation (invariant 5):

  PLANT 1 removes `twitter:site` from the real `web/dist/404.html` - the one document
  `prerender.mjs` strips other head tags from by hand (`canonical`, `og:url`), so it is the page
  most likely to lose a tag nobody else's page loses.

  PLANT 2 removes the footer's `href="https://x.com/provek_dev"` from the real
  `web/dist/method/notes/index.html` - a `staticPage()` route (`renderStatic`, not `renderRoute`),
  the other code path `Shell` is reached through.

Each plant is restored before the next runs, and the real tree is confirmed byte-identical to what
`npm run build` produced before this script exits.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import evidence_stamp  # noqa: E402

OUT = ROOT / "evidence" / "RED-061-a-page-missing-the-x-account-would-have-shipped.txt"
TEST_NODE = "tests/test_x_account_link.py::test_every_emitted_page_names_the_x_account_in_the_head_and_the_footer"
NOT_FOUND = ROOT / "web" / "dist" / "404.html"
NOTES_INDEX = ROOT / "web" / "dist" / "method" / "notes" / "index.html"

TWITTER_SITE = '<meta name="twitter:site" content="@provek_dev" />'
X_HREF = 'href="https://x.com/provek_dev"'


def run_test() -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_NODE, "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120, check=False,
    )
    return p.returncode, (p.stdout + p.stderr).strip()


def plant_and_run(path: Path, needle: str) -> tuple[int, str, int, str, int, str]:
    original = path.read_bytes()
    rc_before, out_before = run_test()
    if rc_before != 0:
        raise RuntimeError(f"REFUSED: {TEST_NODE} is not green before any plant (exit {rc_before}).\n{out_before}")
    try:
        text = original.decode("utf-8")
        if needle not in text:
            raise RuntimeError(f"REFUSED: {needle!r} is not present in {path} - nothing to plant.")
        mutated = text.replace(needle, "", 1)
        path.write_bytes(mutated.encode("utf-8"))
        rc_red, out_red = run_test()
    finally:
        path.write_bytes(original)
    if path.read_bytes() != original:
        raise RuntimeError(f"REFUSED: {path} was not restored to its original bytes.")
    if rc_red == 0:
        raise RuntimeError(f"REFUSED: the plant did not turn {TEST_NODE} red (exit {rc_red}).\n{out_red}")
    rc_after, out_after = run_test()
    if rc_after != 0:
        raise RuntimeError(f"REFUSED: {TEST_NODE} is not green again after the plant was removed (exit {rc_after}).\n{out_after}")
    return rc_before, out_before, rc_red, out_red, rc_after, out_after


def main() -> int:
    for path in (NOT_FOUND, NOTES_INDEX):
        if not path.is_file():
            print(f"REFUSED: {path} is absent - run `npm run build` in web/ first "
                  "(scripts/push.sh does exactly that before this generator would run).")
            return 1

    try:
        b1_rc, b1_out, r1_rc, r1_out, a1_rc, a1_out = plant_and_run(NOT_FOUND, TWITTER_SITE)
        b2_rc, b2_out, r2_rc, r2_out, a2_rc, a2_out = plant_and_run(NOTES_INDEX, X_HREF)
    except RuntimeError as e:
        print(str(e))
        return 1

    if "404.html" not in r1_out:
        print(f"REFUSED: the red run for the 404-page plant does not name the broken page.\n{r1_out}")
        return 1
    if "method/notes" not in r2_out.replace("\\", "/"):
        print(f"REFUSED: the red run for the notes-page plant does not name the broken page.\n{r2_out}")
        return 1

    body = f"""# RED-061 - a page missing the X account link would have shipped
#
# {evidence_stamp.tree_stamp()}
#
# Produced by evidence/RED-061-generator.py, checked in beside this file so both runs below can be
# repeated rather than believed. Two plants, run sequentially against the real web/dist, each
# restored before the next.
#
# SUBJECT: {TEST_NODE}.

{"=" * 100}
PLANT 1 - remove `twitter:site` from the real web/dist/404.html.
{"=" * 100}

--- before the plant, exit {b1_rc} ---
{b1_out}

--- with the plant in place, exit {r1_rc} ---
{r1_out}

--- plant reverted, exit {a1_rc} ---
{a1_out}

{"=" * 100}
PLANT 2 - remove the footer's X href from the real web/dist/method/notes/index.html.
{"=" * 100}

--- before the plant, exit {b2_rc} ---
{b2_out}

--- with the plant in place, exit {r2_rc} ---
{r2_out}

--- plant reverted, exit {a2_rc} ---
{a2_out}
"""
    OUT.write_text(body, encoding="utf-8")
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
