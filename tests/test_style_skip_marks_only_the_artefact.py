"""T-SH-03 - `data-style-skip` marks only the artefact text of a /build/<slug>/ page.

The fleet style lint (~/taskloop/lib/site-style.py) drops every element that carries `data-style-skip`.
A template's text is bound byte for byte to a witnessed dry run (LAW-TEMPLATE-WAS-RUN) and is never
reworded for style, so the template pages mark exactly that text. Anywhere else the attribute would hide
the site's own prose from the lint, so its places and its number are pinned here. A new use needs a card
that changes the pinned number (SITE-HUMANITY-1113 ruling-3, decision 1).

Reads the source tree and the BUILT output. A missing dist is a FAIL, never a skip.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "src"
DIST = ROOT / "web" / "dist"
ATTR = "data-style-skip"
PINNED_IN_SOURCE = 4  # BuildTemplate.tsx: businessOperation p, forWhom p, description p, sections div
HINT = "run `npm run build` in web/ first (push.sh does)"


def _slugs():
    return sorted(p.name for p in (ROOT / "templates").iterdir() if p.is_dir() and (p / "SKILL.md").exists())


def test_source_carries_the_attribute_only_in_build_template_at_the_pinned_count():
    found = {}
    for p in SRC.rglob("*"):
        if p.is_file():
            n = p.read_text(encoding="utf-8", errors="replace").count(ATTR)
            if n:
                found[str(p.relative_to(SRC))] = n
    assert found == {"pages/BuildTemplate.tsx": PINNED_IN_SOURCE}, found


def test_dist_carries_the_attribute_only_on_the_seven_template_pages_equally():
    assert (DIST / "index.html").is_file(), f"{DIST}/index.html is missing: {HINT}"
    slugs = _slugs()
    assert len(slugs) == 7, slugs
    found = {}
    for p in DIST.rglob("*.html"):
        n = p.read_text(encoding="utf-8").count(ATTR)
        if n:
            found[p.relative_to(DIST).as_posix()] = n
    want = {f"build/{s}/index.html": PINNED_IN_SOURCE for s in slugs}
    assert found == want, f"found {found}"


def test_no_template_file_carries_the_attribute_inside_the_pre_text():
    for slug in _slugs():
        d = DIST / "build" / slug
        assert d.is_dir(), f"{d} is missing: {HINT}"
        checked = 0
        for p in d.rglob("*"):
            if not p.is_file():
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(rf'<pre id="skill-source-{re.escape(slug)}"[^>]*>([\s\S]*?)</pre>', text):
                checked += 1
                assert ATTR not in m.group(1), f"{p}: attribute inside the skill-source pre"
        assert checked >= 1, f"no skill-source pre found under {d}"
