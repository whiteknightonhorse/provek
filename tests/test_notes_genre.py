"""LAW-NOTES-GENRE - the verification surface describes; it does not instruct.

ADR-0009 ruled that teaching and verification stay separated as components: a page titled as
teaching puts the institution's normative voice where a reader cannot tell it apart from the
instrument's descriptive one. That ruling was armed by `test_separation_single_reference.py` - but
only over `method/index.html`, so every page added under `/method/` afterwards would have walked
past it. A rule enforced on one page reports success on every other (L-6), and a gate that does not
stop is not a gate (L-4).

This module arms the ruling over the SOURCES, which exist in every checkout, and over every emitted
page under `/method/` when the site has been built.

The second-person imperative is not a style rule here. It is the exact boundary the ADR draws: a
sentence that tells a subject what to do has crossed from describing an instrument to instructing
its candidates, and the examiner coaching candidates is what the separation exists to prevent.
"""
from __future__ import annotations

import re

import pytest

from .notes_support import DIST, emitted, paragraphs, sources, strip_tags

# ADR-0009's own vocabulary, plus the shapes that reintroduce it under another name.
INSTRUCTION = [
    r"\blearn to\b", r"\btutorial\b", r"\bcourse\b", r"\bhow to build autonomous\b",
    r"\byou should\b", r"\byou need to\b", r"\byou must\b", r"\byou can simply\b",
    r"\byour score\b", r"\bimprove your\b", r"\bboost your\b", r"\bmaximi[sz]e your\b",
    r"\bget verified faster\b", r"\bstep-by-step guide\b", r"\bbest practices for\b",
]

# The tells of prose assembled rather than written. Each one is a phrase a person editing their own
# text would cut, which is exactly why a generator that never edits leaves them in.
FILLER = [
    r"\bin today's\b", r"\blet's dive\b", r"\bdive into\b", r"\bin conclusion\b",
    r"\bit'?s important to note\b", r"\bit is important to note\b", r"\bwhether you'?re\b",
    r"\bwhether you are\b", r"\bunlock\b", r"\bleverage\b", r"\bseamless\b", r"\brobust\b",
    r"\bgame.changer\b", r"\bdelve\b", r"\bin the world of\b", r"\bwhen it comes to\b",
    r"\bat the end of the day\b", r"\bthe key takeaway\b", r"\bin this article\b",
]

ROUTE_WORDS = ("learn", "guide", "how-to", "blog", "tips", "academy")
LIST_SHARE_MAX = 0.40

pytestmark = pytest.mark.skipif(not sources(), reason="no method notes captured in this checkout")


def test_no_note_instructs_its_reader():
    for front, body in sources():
        subject = " ".join([front["title"], front["h1"], front["description"], body])
        for pat in INSTRUCTION:
            m = re.search(pat, subject, re.I)
            assert not m, f"{front['slug']}: reads as instruction, not description: {m.group(0)!r}"


def test_no_note_is_written_in_the_voice_of_a_generator():
    for front, body in sources():
        for pat in FILLER:
            m = re.search(pat, body, re.I)
            assert not m, f"{front['slug']}: filler phrase {m.group(0)!r}"


def test_no_heading_is_a_how_to():
    """35% of the question rows in the keyword base begin with 'how to'. That is the demand, and it
    is precisely the demand this surface may not serve: the highest-volume one in the base is
    'how to build an ai agent'. The gate stands between the base and the temptation."""
    for front, body in sources():
        for h in re.findall(r"^#{2,3} (.+)$", body, re.M):
            assert not re.match(r"^how to\b", h.strip(), re.I), f"{front['slug']}: heading {h!r}"


def test_the_route_never_names_the_genre_it_is_not():
    for front, _ in sources():
        assert not any(w in front["slug"] for w in ROUTE_WORDS), (
            f"{front['slug']}: the address itself announces a genre this surface does not publish")


def test_prose_is_not_a_list_in_disguise():
    for front, body in sources():
        listed = sum(len(ln) for ln in body.splitlines() if ln.strip().startswith(("- ", "* ", "|")))
        share = listed / len(body)
        assert share <= LIST_SHARE_MAX, (
            f"{front['slug']}: {share:.0%} of the body is list or table rows (max {LIST_SHARE_MAX:.0%})")


def test_no_two_consecutive_paragraphs_open_on_the_same_word():
    for front, body in sources():
        starts = [p.split()[0].lower().strip(",.") for p in paragraphs(body) if p.split()]
        for a, b in zip(starts, starts[1:], strict=False):
            assert a != b, f"{front['slug']}: two paragraphs in a row open with {a!r}"


def test_every_note_says_what_drafted_it():
    """We measure how much of somebody else's business runs without a human in the loop. Publishing
    prose drafted by two models without saying so would be the same omission, committed by the
    party that named it."""
    for front, _body in sources():
        assert front["provenance"]["plan_model"] and front["provenance"]["prose_model"]


def test_the_genre_holds_on_every_emitted_page_under_method():
    """Including the index, and including the Method page itself - the ruling is about the surface,
    not about a file."""
    if not DIST.exists():
        pytest.skip("site not built in this checkout")
    pages = sorted((DIST / "method").rglob("index.html"))
    assert pages, "nothing was emitted under /method/"
    for page in pages:
        body = page.read_text(encoding="utf-8").split('<script>window.__PROVEK__', 1)[0]
        text = strip_tags(body)
        for pat in INSTRUCTION + FILLER:
            m = re.search(pat, text, re.I)
            assert not m, f"{page.relative_to(DIST)}: {m.group(0)!r}"


def test_the_emitted_notes_carry_the_provenance_line_where_a_reader_sees_it():
    pages = emitted()
    if not pages:
        pytest.skip("site not built in this checkout")
    for slug, html in pages.items():
        text = strip_tags(html)
        assert "claude-sonnet-5" in text and "claude-haiku-4-5" in text, (
            f"{slug}: the models that drafted it are not disclosed on the page")
