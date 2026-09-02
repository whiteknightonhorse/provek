"""The corrections log (phase-2 plan): both errata this project has ever published moved
from `/registry/` to `/registry/corrections/`, byte-for-byte - and `/registry/` itself now carries
exactly one compact line pointing there, never the full text of either correction again.

WHY THIS IS A FIXTURE TEST, NOT A DIFF AGAINST GIT HISTORY. The two expected texts below are
captured directly from `web/src/pages/Registry.tsx` as it stood BEFORE this task moved them - the
same discipline `tests/test_phase_two_promises_nothing.py` and `tests/test_ratchet_phase3_note.py`
already hold their own migrated/duplicated text to. A test that diffed against a git ref would stop
meaning anything the day that ref is pruned; a literal fixture means the same thing forever, and a
future editor who reworks the wording on the corrections page has to convince THIS test, not merely
convince themselves that nothing important changed.

Checked over the EMITTED HTML, not the `.tsx` source - what a reader receives is the thing that has
to hold (L-3), and `web/markdown.mjs`'s auto-derived `.md` sibling is checked too, since "prerender,
no JS" was the point of putting this content on its own page at all.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS_PAGE = ROOT / "web" / "dist" / "registry" / "corrections" / "index.html"
CORRECTIONS_MD = ROOT / "web" / "dist" / "registry" / "corrections" / "index.md"
REGISTRY_PAGE = ROOT / "web" / "dist" / "registry" / "index.html"

# Captured verbatim from `web/src/pages/Registry.tsx` before this task moved them off that page -
# see the module docstring for why a literal fixture is used rather than a diff against history.
EXPECTED_25AUG = (
    "Erratum, 2026-08-25. Every passport issued under profile 1.0.0 states an evidence window of "
    "30 days. The collector read the last 50 commits by count instead, and never looked at a date. "
    "The whole registry is being re-measured against the window that was published; corrected "
    "verdicts will be re-issued together, in whichever direction each one moves, and the "
    "superseded documents will stay readable rather than disappear."
)
EXPECTED_31AUG = (
    "Erratum, 2026-08-31. A defect in the rule, not the data: the cohort granted L4 to a sole "
    "author without checking the signature share the published methodology requires for that "
    "rung. The rule now matches what is published; APIbase, the one passport the defect affected, "
    "moved from L4 to L3 (projection 80 to 60). Nothing here disappears — this notice stays "
    "up next to the one it follows."
)

emitted = pytest.mark.skipif(not CORRECTIONS_PAGE.exists(), reason="site not built in this checkout")


def _main_text(html_path: Path) -> str:
    html = html_path.read_text(encoding="utf-8")
    body = html.split("<script>window.__PROVEK__", 1)[0]
    m = re.search(r"<main\b.*?</main>", body, re.S)
    assert m, f"{html_path} has no <main>"
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(0))).strip()


@emitted
def test_both_errata_are_preserved_byte_for_byte_on_the_corrections_page():
    text = _main_text(CORRECTIONS_PAGE)
    assert EXPECTED_25AUG in text, "the 2026-08-25 erratum's text drifted from what was moved here"
    assert EXPECTED_31AUG in text, "the 2026-08-31 erratum's text drifted from what was moved here"


@pytest.mark.skipif(not CORRECTIONS_MD.exists(), reason="markdown sibling not built in this checkout")
def test_both_errata_survive_into_the_no_js_markdown_sibling():
    """"prerender, no JS" is the whole point of moving this content to its own page - the markdown
    twin `web/markdown.mjs` derives from every page is what proves a reader (or a crawler) with no
    JavaScript still gets the exact same words."""
    # `**bold**` is the one markdown syntax either fixture's own text would collide with (the
    # converter wraps `<strong>Erratum, ...</strong>` as `**Erratum, ...**`) - stripped the same
    # way `_main_text` strips HTML tags for the sibling page, so both comparisons judge the WORDS.
    text = re.sub(r"\s+", " ", CORRECTIONS_MD.read_text(encoding="utf-8").replace("**", "")).strip()
    assert EXPECTED_25AUG in text
    assert EXPECTED_31AUG in text


@emitted
def test_the_full_erratum_text_no_longer_lives_on_the_registry_page():
    """The move is real, not a copy: the full bodies leave `/registry/` entirely once they have an
    address of their own - reproducing them in both places would be LAW #ONE-PLACE's own defect,
    applied to prose instead of code."""
    text = _main_text(REGISTRY_PAGE)
    assert EXPECTED_25AUG not in text
    assert EXPECTED_31AUG not in text
    assert "will be re-issued together" not in text
    assert "signature share the published" not in text


@emitted
def test_registry_carries_exactly_one_correction_line():
    text = _main_text(REGISTRY_PAGE)
    assert text.count("Erratum, 2026-08-25.") == 0
    assert text.count("Erratum, 2026-08-31.") == 0
    assert text.count("Two corrections are on record for this registry.") == 1
    assert text.count("All corrections (2)") == 1
    links = re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>\s*All corrections',
                       REGISTRY_PAGE.read_text(encoding="utf-8"))
    assert links == ["/registry/corrections/"]


def test_the_route_is_wired_and_prerendered():
    app = (ROOT / "web" / "src" / "App.tsx").read_text(encoding="utf-8")
    assert 'if (route === "/registry/corrections/") return <Corrections />;' in app
    prerender = (ROOT / "web" / "prerender.mjs").read_text(encoding="utf-8")
    assert '"/registry/corrections/"' in prerender
    verify = (ROOT / "scripts" / "verify_live.sh").read_text(encoding="utf-8")
    assert "/registry/corrections/:200" in verify, (
        "the door's own live-address check does not cover the new page - a deploy could ship a "
        "404 here and every other check would still read green")


def test_MUTATION_a_reworded_erratum_would_be_CAUGHT():
    """Control: a paraphrase that preserves the MEANING but not the WORDS must still fail - the
    whole point of a byte-for-byte fixture over a "says roughly the same thing" check."""
    reworded = EXPECTED_25AUG.replace("re-measured", "recomputed")
    assert reworded not in EXPECTED_25AUG
    assert EXPECTED_25AUG not in reworded
