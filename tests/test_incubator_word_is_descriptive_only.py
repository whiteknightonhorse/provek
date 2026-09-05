"""T-78 (Fable ruling, 78-texts-for-the-incubator-funnel.ruling-1.md): "incubator" is admitted to
describe the product only in one shape, and this is the gate that holds it there.

THE RULING'S TWO HALVES, CHECKED SEPARATELY.

  1. Site-wide, on every emitted page: the word is never capitalised (never a title-case brand,
     which is exactly what ADR-0011 rejected as this surface's name - "Provek, AI Business
     Incubator" - and never inside a `<title>`, an `<h1>`-`<h6>`, the masthead `<nav>`, or any
     `<meta ...>` tag, which is the concrete meaning of "never a title/H1/nav label/meta". Zero
     measured demand for the word (`seo/keywords.csv`, 0 of 1418 rows) is ADR-0011's own reason;
     this file does not re-measure that, it enforces the ruling's conclusion.

  2. On THREE of the four funnel surfaces this task rewrote - `/apply/`, `/build/`, `/registry/` -
     exactly one lowercase, descriptive use is required in `<main>`, and it must sit beside the
     "holds no funds" limit rather than floating free, because that limit is what keeps the word
     from implying a fund or a cohort that do not exist (the ruling's own stated reason to reject
     both). `web/src/copy.ts`'s `INCUBATOR_SENTENCE` is what actually satisfies this on all three;
     this test does not import that constant, it reads the built HTML, so a future rewrite that
     drops the shared sentence but keeps compliant prose still passes, and one that keeps the
     import but breaks the placement still fails.

  2a. AMENDED (Fable, T-03 ruling-2, D2, 03-landing-never-names-the-agents.ruling-2.md): the
      landing (`/`) dropped its own copy of `INCUBATOR_SENTENCE` - it duplicated, word for word,
      the same sentence `/build/`'s "What follows" section already carries, and the word has 0 of
      1418 measured rows of demand (T-70 ruling-1 §1.1) to justify saying it twice on one surface.
      The landing is now held to exactly ZERO uses of "incubator" in `<main>`, not one; `/apply/`,
      `/build/` and `/registry/` are unchanged, still exactly one each, beside the limit.

  This is deliberately NOT applied to `/method/` or `/phase-2/`: both used the word, in the same
  lowercase/descriptive shape, before this ruling and outside its scope (T-78's brief named four
  surfaces, not these two) - re-litigating pre-existing, out-of-scope prose here would be a defect
  of its own (CLAUDE.md invariant: do not reopen what nobody asked to change). Rule 1 above still
  binds them, because "never a brand, never in a heading" is a site-wide constraint by its own
  terms, not a per-surface one.

THE CONTROLS RUN FIRST (CLAUDE.md invariant 5), one per half: a capitalised plant for rule 1, an
isolated plant (no "holds no funds" nearby) for rule 2 - each shown turning its own check red on a
scratch copy before the real tree is trusted to have none. The rule-2 control now plants its
isolated mention on `/build/` (real count 1, planted count 2) rather than on `/` (real count now
0, planted count 1) - a plant on `/`'s real-zero baseline would only prove the count check works,
not that an isolated second mention beside a real one is caught.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"

FUNNEL_ROUTES = {"/apply/", "/build/", "/registry/"}

WORD_RE = re.compile(r"[Ii]ncubator")
TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>")
HEADING_RE = re.compile(r"<h[1-6][^>]*>([\s\S]*?)</h[1-6]>")
NAV_RE = re.compile(r"<nav[^>]*>([\s\S]*?)</nav>")
META_RE = re.compile(r"<meta\b[^>]*>")
MAIN_RE = re.compile(r"<main[^>]*>([\s\S]*)</main>")
PARA_RE = re.compile(r"<p\b[^>]*>([\s\S]*?)</p>")


def _route_of(p: Path, dist: Path) -> str:
    if p.name == "404.html":
        return "/404.html"
    r = p.parent.relative_to(dist).as_posix()
    return "/" if r == "." else f"/{r}/"


def _pages(dist: Path) -> list[Path]:
    assert dist.is_dir(), (
        f"{dist} is absent, so this gate measured nothing. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite. A skip here would be a gate present "
        "but not armed."
    )
    return sorted([*dist.rglob("index.html"), *dist.glob("404.html")])


def _forbidden_placements(dist: Path) -> dict[str, list[str]]:
    """route -> reasons the word appeared somewhere rule 1 forbids it."""
    offenders: dict[str, list[str]] = {}
    for p in _pages(dist):
        html = p.read_text(encoding="utf-8")
        found: list[str] = []
        for label, rx in (("title", TITLE_RE), ("heading", HEADING_RE), ("nav", NAV_RE)):
            for m in rx.finditer(html):
                if WORD_RE.search(m.group(1)):
                    found.append(label)
        for m in META_RE.finditer(html):
            if WORD_RE.search(m.group(0)):
                found.append("meta")
        # Capitalisation is checked over the WHOLE document, title/heading/nav/meta included -
        # a capitalised brand there is already caught above, and a capitalised occurrence buried
        # in ordinary prose is still the defect rule 1 names.
        if re.search(r"\bIncubator\b", html) or re.search(r"\bINCUBATOR\b", html):
            found.append("capitalised")
        if found:
            offenders[_route_of(p, dist)] = found
    return offenders


def _funnel_surface_reading(dist: Path, route: str) -> dict:
    """count of lowercase "incubator" inside <main>, and whether each occurrence's own <p> block
    also carries "holds no funds"."""
    path = dist / route.lstrip("/") / "index.html" if route != "/" else dist / "index.html"
    html = path.read_text(encoding="utf-8")
    m = MAIN_RE.search(html)
    assert m, f"{route}: no <main> element found - Chrome.tsx's Page component changed shape"
    main = m.group(1)
    count = len(re.findall(r"incubator", main))
    beside_limit = []
    for para in PARA_RE.findall(main):
        if "incubator" in para:
            beside_limit.append("holds no funds" in para.lower())
    return {"count": count, "beside_limit": beside_limit}


def test_the_capitalisation_and_placement_check_catches_a_planted_brand(tmp_path):
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this control has nothing to copy. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    scratch = tmp_path / "dist"
    shutil.copytree(DIST, scratch)

    before = _forbidden_placements(scratch)
    assert not before, f"the scratch copy was already dirty before any plant: {before}"

    index = scratch / "index.html"
    text = index.read_text(encoding="utf-8")
    planted = text.replace("<title>", "<title>Incubator ", 1)
    assert planted != text, "the plant did not change the file - <title> was not found"
    index.write_text(planted, encoding="utf-8")

    after = _forbidden_placements(scratch)
    assert "title" in after.get("/", []) or "capitalised" in after.get("/", []), (
        f"planting a capitalised brand word in <title> was not caught: {after}"
    )


def test_the_beside_the_limit_check_catches_an_isolated_mention(tmp_path):
    """Rebased to /build/ (Fable, T-03 ruling-2, D2): the landing's real count is now 0, so a
    single plant there would only prove the counter can count to one, not that an isolated SECOND
    mention beside a real, compliant one is caught. /build/ still carries its own real, compliant
    INCUBATOR_SENTENCE use, so planting a second, isolated one there is the actual case this half
    of the gate exists to catch."""
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this control has nothing to copy. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite."
    )
    scratch = tmp_path / "dist"
    shutil.copytree(DIST, scratch)

    index = scratch / "build" / "index.html"
    text = index.read_text(encoding="utf-8")
    m = MAIN_RE.search(text)
    assert m, "no <main> element in the scratch copy"
    planted = text.replace(
        "</main>",
        '<p class="sr-only">This is an incubator for testing purposes only.</p></main>',
        1,
    )
    assert planted != text, "the plant did not change the file - </main> was not found"
    index.write_text(planted, encoding="utf-8")

    reading = _funnel_surface_reading(scratch, "/build/")
    assert reading["count"] == 2, f"expected the real mention plus the planted one: {reading}"
    assert False in reading["beside_limit"], (
        f"a second, isolated mention with no nearby funds limit was not caught: {reading}"
    )


def test_incubator_is_never_capitalised_or_placed_in_a_title_heading_nav_or_meta_tag():
    offenders = _forbidden_placements(DIST)
    assert not offenders, f"forbidden placement or capitalisation of 'incubator': {offenders}"


def test_each_funnel_surface_uses_incubator_exactly_once_beside_the_funds_limit():
    bad = {}
    for route in sorted(FUNNEL_ROUTES):
        reading = _funnel_surface_reading(DIST, route)
        if reading["count"] != 1 or reading["beside_limit"] != [True]:
            bad[route] = reading
    assert not bad, f"funnel surfaces failing the one-sentence-beside-the-limit rule: {bad}"


def test_landing_never_uses_incubator_in_main():
    """Fable, T-03 ruling-2, D2: the landing's own copy of INCUBATOR_SENTENCE was retired as a
    duplicate of /build/'s "What follows" section. Unlike the other three funnel surfaces, `/`
    is now held to ZERO uses in <main>, not one - a future re-addition (even a compliant,
    beside-the-limit one) is the defect this test exists to catch."""
    reading = _funnel_surface_reading(DIST, "/")
    assert reading["count"] == 0, f"the landing should carry no 'incubator' mention in <main>: {reading}"
