"""Passport clarity (phase-2 plan): `InfoDot` must actually reach a keyboard and a touch reader,
not merely claim to - checked over the EMITTED HTML of a live passport (L-3), not the component
source alone.

WHY `<details>`/`<summary>` NEEDS NO SEPARATE KEYBOARD TEST OF ITS OWN. The HTML specification
makes `<summary>` a focusable, Enter/Space-operable disclosure widget - that guarantee comes from
the browser, not from this codebase, and re-testing browser conformance would be testing something
this project does not own. What this project DOES own, and what these tests hold it to, is that
`InfoDot` is actually built on `<details>`/`<summary>` (rather than, say, a `<div onMouseOver>` that
LOOKS the same and is invisible to exactly the two audiences this task exists to reach), and that
the badges named in the operator's brief ("current `title=` on touch") were actually converted
rather than merely joined by new ones beside them.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INFODOT_TSX = ROOT / "web" / "src" / "components" / "InfoDot.tsx"
PASSPORT_TSX = ROOT / "web" / "src" / "pages" / "Passport.tsx"
PASSPORT_PAGE = ROOT / "web" / "dist" / "p" / "git_whiteknightonhorse_provek" / "index.html"

emitted = pytest.mark.skipif(not PASSPORT_PAGE.exists(), reason="site not built in this checkout")


def test_infodot_is_built_on_a_native_details_element():
    src = INFODOT_TSX.read_text(encoding="utf-8")
    assert "<details" in src and "<summary" in src, (
        "InfoDot must be a native <details>/<summary> disclosure - that is what makes it "
        "keyboard- and touch-operable for free, per the HTML spec's own guarantee"
    )
    # NOT a hover-only affordance smuggled back in under a different name.
    assert "onMouseOver" not in src and "onMouseEnter" not in src


def test_infodots_own_trigger_carries_no_bare_title_attribute():
    """The one thing InfoDot must not become: a `<summary title="...">` that merely moved the
    invisible-on-touch problem one component deeper."""
    src = INFODOT_TSX.read_text(encoding="utf-8")
    # `title="` (with the opening quote) is the real JSX attribute shape; the docstring above
    # names the bare word `title=` in prose without a following quote, which this pattern skips.
    assert 'title="' not in src


@pytest.mark.parametrize("phrase", [
    "self-declared",           # AccFact's register badge (was a bare title=)
    "assumed, unverified",     # the treasury-control claim badge (was a bare title=)
    "identity binding",        # the binding-strength badge (was a bare title=)
    "inferred",                # the operation confidence badge (was title="" - EMPTY)
])
def test_the_named_badges_no_longer_carry_a_bare_title(phrase):
    """Each of these four badges is named in the operator's brief as the concrete defect ("current
    `title=` on touch are not visible, this is the main clarity defect") - checked on the page's
    OWN source, since not every live passport necessarily exercises every one of the four states
    (a subject with no treasury claim never renders that badge at all)."""
    src = PASSPORT_TSX.read_text(encoding="utf-8")
    i = src.find(phrase)
    assert i != -1, f"{phrase!r} no longer appears in Passport.tsx - update this test"
    window = src[max(0, i - 200):i]
    assert "title=" not in window, f"{phrase!r} still sits behind a bare title= attribute"


@emitted
def test_the_emitted_passport_page_actually_contains_multiple_infodots():
    """Not merely "the component exists" (L-16: present is not the same as armed) - the built page
    for a real subject must contain more than one real `<details>` disclosure, proving InfoDot is
    actually used across the sections named in the brief (self-reported, coverage, binding), not
    written and left uncalled."""
    html = PASSPORT_PAGE.read_text(encoding="utf-8")
    # `<details` also covers the "How to read this passport" intro, deliberately - it is the same
    # accessible-disclosure mechanism, and its presence is exactly what this test measures for.
    count = len(re.findall(r"<details\b", html))
    assert count >= 5, f"only {count} <details> disclosures found on a live passport page"


@emitted
def test_how_to_read_this_passport_intro_is_present_and_collapsible():
    html = PASSPORT_PAGE.read_text(encoding="utf-8")
    i = html.find("How to read this passport")
    assert i != -1
    # It must sit inside a <summary>, not a plain heading - a heading cannot be collapsed.
    window = html[max(0, i - 200):i]
    assert "<summary" in window
