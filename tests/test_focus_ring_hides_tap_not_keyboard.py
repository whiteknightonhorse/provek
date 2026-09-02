"""T-30-mobile-blue-bars: the operator saw a full-width blue bar on an iPhone at the top and
bottom of `#main` after a tap navigation - `:focus-visible` ringing a script-focused `<div>` that a
tap could never have earned a ring for. 4133b08 fixed this by tracking input modality ourselves
(`usingKeyboard` in App.tsx) and gating a `.no-focus-ring` class the CSS honours.

INVARIANT 5 (CLAUDE.md): a test that only checks the fix is PRESENT would still pass if a future
edit quietly reintroduced either half of the regression it guards against - the artifact returning
for a tap, OR (the more dangerous direction, since nothing on a phone would look wrong) keyboard
focus becoming invisible for everyone. This file checks BOTH halves can still be told apart:

  1. The GLOBAL `:focus-visible` rule still rings something for a keyboard user. Deleting it is
     the regression "focus is invisible for everyone" - a worse accessibility break than the bug
     this task fixes, and nothing about the tap-artifact would look wrong if it happened.
  2. `#main.no-focus-ring:focus-visible { outline: none; }` still exists to specifically silence
     the script-focused `<div>` for a tap. Deleting it is the regression "the blue bars are back."
  3. The suppression is GATED ON TRACKED MODALITY (`!usingKeyboard`), not a constant. A toggle
     hard-coded to always suppress would pass checks 1 and 2 above (both rules still exist) while
     silently blinding a keyboard user - the exact failure mode the operator's brief warned against
     ("removing focus entirely breaks accessibility").
  4. The skip-link clears a stale suppression on focus, so a tap navigation followed by a keyboard
     Tab to the skip link is never left wrongly silenced.

`evidence/RED-041-generator.py` proves each of these four checks can actually fail, by making the
regression it names and watching the corresponding test here go red.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INDEX_CSS = ROOT / "web" / "src" / "index.css"
APP_TSX = ROOT / "web" / "src" / "App.tsx"
DIST_CSS_DIR = ROOT / "web" / "dist" / "assets"

GLOBAL_RING_RE = re.compile(r":focus-visible\s*\{\s*outline:\s*2px solid\b")
MAIN_OVERRIDE_RE = re.compile(r"#main\.no-focus-ring:focus-visible\s*\{\s*outline:\s*none\s*;?\s*\}")


def _dist_css_text() -> str | None:
    if not DIST_CSS_DIR.is_dir():
        return None
    css_files = sorted(DIST_CSS_DIR.glob("*.css"))
    if not css_files:
        return None
    return "\n".join(f.read_text(encoding="utf-8") for f in css_files)


emitted = pytest.mark.skipif(
    _dist_css_text() is None, reason="site not built in this checkout (web/dist/assets/*.css missing)"
)


def test_global_focus_visible_rule_still_rings_something():
    css = INDEX_CSS.read_text(encoding="utf-8")
    assert GLOBAL_RING_RE.search(css), (
        "no global `:focus-visible { outline: 2px solid ... }` rule in index.css - "
        "removing it makes keyboard focus invisible EVERYWHERE, not just quiet on #main"
    )


def test_main_tap_suppression_rule_still_present():
    css = INDEX_CSS.read_text(encoding="utf-8")
    assert MAIN_OVERRIDE_RE.search(css), (
        "no `#main.no-focus-ring:focus-visible { outline: none; }` rule in index.css - "
        "without it the tap-triggered blue bars the operator saw on an iPhone are back"
    )


def test_suppression_is_gated_on_tracked_modality_not_a_constant():
    src = APP_TSX.read_text(encoding="utf-8")
    assert 'classList.toggle("no-focus-ring", !usingKeyboard)' in src, (
        "the no-focus-ring toggle must be driven by tracked input modality (!usingKeyboard), "
        "not a hard-coded value - a constant would silently blind keyboard users too"
    )
    # The tracker itself: a Tab keydown sets it true, any pointerdown sets it false. Losing either
    # listener collapses the toggle back to "always one state", which the assertion above alone
    # cannot distinguish from a working tracker if both listeners point at the same variable.
    assert re.search(r'addEventListener\("keydown".*usingKeyboard\s*=\s*true', src), (
        "no keydown handler setting usingKeyboard = true - Tab navigation would stop earning a "
        "visible ring"
    )
    assert re.search(r'addEventListener\("pointerdown".*usingKeyboard\s*=\s*false', src), (
        "no pointerdown handler setting usingKeyboard = false - a tap would stop being "
        "distinguishable from a keyboard route change"
    )


def test_skip_link_clears_stale_suppression_on_focus():
    src = APP_TSX.read_text(encoding="utf-8")
    i = src.find('href="#main"')
    assert i != -1, "the skip-link target #main has moved or been removed - update this test"
    window = src[i:i + 600]
    assert 'classList.remove("no-focus-ring")' in window, (
        "the skip-link's onFocus no longer clears a stale no-focus-ring suppression - a tap "
        "navigation followed by Tab-to-skip-link could be left wrongly silenced"
    )


@emitted
def test_built_css_carries_both_rules():
    css = _dist_css_text()
    assert css is not None
    assert GLOBAL_RING_RE.search(css) or re.search(r":focus-visible\{outline:2px solid", css), (
        "built CSS has no global :focus-visible rule"
    )
    assert MAIN_OVERRIDE_RE.search(css) or "#main.no-focus-ring:focus-visible{outline:none}" in css, (
        "built CSS has no #main.no-focus-ring:focus-visible{outline:none} override"
    )


def test_the_checks_themselves_can_fail():
    """A regex that always matches would pass every test above by accident. Prove both patterns
    respond to their own absence, over the source they actually check."""
    assert not GLOBAL_RING_RE.search("body { color: red; }")
    assert not MAIN_OVERRIDE_RE.search("#main:focus-visible { outline: none; }")  # missing .no-focus-ring
