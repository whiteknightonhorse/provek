"""T-WB-01 - no HTML comment ships to a visitor (audit H2, Fable ruling PROVEK-QA-1023 q-1).

THE DEFECT. `web/index.html` carries four source comments (commit hashes, who ruled what, a favicon
post-mortem, about 3.7 KB). `prerender.mjs` reads the built shell and injects it into every route
and into 404.html, so every page a visitor downloaded carried all four. The reasoning belongs in
the source and in DECISIONS.md, not in every byte on the wire.

WHAT THIS READS. The BUILT output - `web/dist/index.html`, `web/dist/404.html` and every
`web/dist/**/index.html` - because the source file is supposed to keep its comments; the claim is
about what ships. A missing dist is a FAIL, never a skip: a gate that skips when the thing it
guards is absent is green exactly when nothing was checked.

WHAT IS NOT ASSERTED. Comments inside inline `<script>` / `<style>` bodies are not parsed out as
a separate class; any `<!--` anywhere in the file counts, which is stricter and is the point.
"""
from pathlib import Path

DIST = Path(__file__).resolve().parent.parent / "web" / "dist"
HINT = "run `npm run build` first (push.sh step 6 does)"


def _pages():
    if not (DIST / "index.html").is_file():
        raise AssertionError(f"{DIST}/index.html is missing: {HINT}")
    pages = [DIST / "index.html", DIST / "404.html", *sorted(DIST.glob("**/index.html"))]
    seen, out = set(), []
    for p in pages:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def test_dist_exists_and_has_pages():
    pages = _pages()
    assert (DIST / "404.html").is_file(), f"{DIST}/404.html is missing: {HINT}"
    assert len(pages) > 2, f"only {len(pages)} page(s) under {DIST}: {HINT}"


def test_no_shipped_page_contains_an_html_comment():
    bad = {}
    for p in _pages():
        n = p.read_text(encoding="utf-8").count("<!--")
        if n:
            bad[str(p.relative_to(DIST))] = n
    assert not bad, f"HTML comments shipped in {len(bad)} page(s): {bad}"
