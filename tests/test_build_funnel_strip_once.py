"""ADR-0011 section 6.4, SPEC 3.7 item 5 - the funnel strip is the one permitted link from a
template page to the instrument, and it is the only appearance `/apply/` may make on that page's
own content: no counters, no tiers, no level outside a passport, no "verified" wording anywhere
under `/build/`.

WHY THE CHECK IS SCOPED TO `<main>`. The masthead's own "Request verification" button and its
`/apply/` link are sitewide chrome that predates this task and appears identically on every page
of the site (`/method/`, `/registry/`, `/apply/` itself) - reading the whole document would make
this check permanently unsatisfiable by any page on the site, which is not what the boundary means.
`Chrome.tsx`'s `Page` component wraps a route's own content in a `<main>` tag nested inside the
masthead/footer, which is the one place these words are the PAGE's, not the CHROME's.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist" / "build"

FORBIDDEN_LEVEL = re.compile(r"\bL[0-5]\b")
FORBIDDEN_VERIFIED = re.compile(r"\bverified\b", re.IGNORECASE)
FORBIDDEN_COUNTER = re.compile(r"[0-9]{1,3}(?:,[0-9]{3})+ agents")


def _main_content(html: str) -> str:
    m = re.search(r"<main[^>]*>([\s\S]*)</main>", html)
    assert m, "no <main> element found - Chrome.tsx's Page component changed shape"
    return m.group(1)


def _build_pages() -> list[Path]:
    assert DIST.is_dir(), (
        f"{DIST} is absent, so this gate measured nothing. Run `npm run build` in web/ - "
        "scripts/push.sh does exactly that before the suite. A skip here would be a gate present "
        "but not armed."
    )
    return sorted(DIST.rglob("index.html"))


def test_apply_appears_on_a_template_page_only_via_the_funnel_strip_once():
    pages = _build_pages()
    assert pages, "no page emitted under dist/build/"
    bad = {}
    for p in pages:
        main = _main_content(p.read_text(encoding="utf-8"))
        count = main.count('href="/apply/"')
        if count != 1:
            bad[str(p.relative_to(ROOT))] = count
    assert not bad, f"expected exactly one /apply/ link (the funnel strip) per page's own content: {bad}"


def test_no_level_token_verified_wording_or_counter_under_build():
    pages = _build_pages()
    offenders = {}
    for p in pages:
        main = _main_content(p.read_text(encoding="utf-8"))
        found = {
            "level_token": FORBIDDEN_LEVEL.findall(main),
            "verified": FORBIDDEN_VERIFIED.findall(main),
            "counter": FORBIDDEN_COUNTER.findall(main),
        }
        found = {k: v for k, v in found.items() if v}
        if found:
            offenders[str(p.relative_to(ROOT))] = found
    assert not offenders, f"forbidden vocabulary under dist/build/: {offenders}"


# --- control: the checks above must be able to fail -------------------------------------------

def test_the_apply_once_check_catches_a_second_link():
    main = '<main><a href="/apply/">a</a><a href="/apply/">b</a></main>'
    count = _main_content(main).count('href="/apply/"')
    assert count == 2, "fixture setup failed to plant two links"


def test_the_vocabulary_check_catches_each_forbidden_form():
    main = _main_content("<main>This subject is verified at L4, and 1,234 agents were built.</main>")
    assert FORBIDDEN_LEVEL.search(main)
    assert FORBIDDEN_VERIFIED.search(main)
    assert FORBIDDEN_COUNTER.search(main)
