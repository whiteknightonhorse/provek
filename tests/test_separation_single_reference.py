"""The site side of the teaching/verification separation.

The specification's mitigation for the conflict — a party that teaches people to pass its own
verification grades work it set itself — is that teaching and verification stay separated as
components. The corpus repository enforces its half by refusing to name this instrument. This
enforces the other half: the verification surface references the corpus exactly once, on the Method
page, framed as provenance.

Scanned over the EMITTED site rather than the source, because what a reader receives is the thing
that has to hold. A component boundary maintained only in the code that generates the boundary is
not one.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
CORPUS = "provek-method"

pytestmark = pytest.mark.skipif(not DIST.exists(), reason="site not built in this checkout")


def _pages() -> list[Path]:
    return sorted(DIST.rglob("*.html"))


def test_the_corpus_is_referenced_exactly_once_across_the_whole_site():
    hits = []
    for page in _pages():
        text = page.read_text(encoding="utf-8")
        # The inlined bootstrap data repeats the page markup; count the rendered document only.
        body = text.split('<script>window.__PROVEK__', 1)[0]
        n = len(re.findall(rf"github\.com/[\w-]+/{CORPUS}", body))
        if n:
            hits.append((page.relative_to(DIST).as_posix(), n))
    assert hits, "the provenance link is missing entirely"
    assert len(hits) == 1, f"referenced from more than one page: {hits}"
    page, n = hits[0]
    assert page == "method/index.html", f"the reference belongs on Method, found on {page}"
    assert n == 1, f"referenced {n} times on one page; one sentence, one link"


def test_the_reference_is_framed_as_provenance_not_as_instruction():
    text = (DIST / "method" / "index.html").read_text(encoding="utf-8")
    body = text.split('<script>window.__PROVEK__', 1)[0]
    assert "provenance, not instruction" in body
    assert "has no effect on any verdict" in body
    for forbidden in ("learn to", "tutorial", "course", "how to build autonomous"):
        assert forbidden.lower() not in body.lower(), f"reads as teaching: {forbidden}"


def test_the_corpus_never_appears_in_navigation():
    """A nav entry would make the corpus a component OF this surface - integration, not
    separation - and DESIGN.md rule 4 forbids the retrofit independently."""
    for page in _pages():
        nav = re.search(r"<nav\b.*?</nav>", page.read_text(encoding="utf-8"), re.S)
        if nav:
            assert CORPUS not in nav.group(0), page.name
