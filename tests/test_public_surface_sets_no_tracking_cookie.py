"""T-WB-04 - the public surface counts page loads without a cookie or an identifier (D-78).

THE DEFECT. Every page shipped `googletagmanager.com/gtag/js`, which sets a cookie and an identifier
with no consent mechanism, and `/apply/` said so (audit M8). D-78 replaces it with Cloudflare Web
Analytics, which is cookieless.

WHAT THIS READS. The BUILT output - `web/dist/index.html`, `web/dist/404.html` and every
`web/dist/**/index.html` - plus the disclosure source `web/src/pages/Apply.tsx`. A missing dist is a
FAIL, never a skip (the T-WB-01 shape). Exactly ONE beacon per page: two is the double count the
account's auto-install produces on top of a tag in the shell.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "web" / "dist"
APPLY = ROOT / "web" / "src" / "pages" / "Apply.tsx"
HINT = "run `npm run build` first (push.sh step 6 does)"
BEACON = "static.cloudflareinsights.com/beacon.min.js"


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
    assert (DIST / "404.html").is_file(), f"{DIST}/404.html is missing: {HINT}"
    assert len(_pages()) > 2, f"fewer than 3 pages under {DIST}: {HINT}"


def test_no_shipped_page_loads_google_analytics():
    bad = {}
    for p in _pages():
        t = p.read_text(encoding="utf-8")
        n = t.count("googletagmanager.com") + t.count("gtag(")
        if n:
            bad[str(p.relative_to(DIST))] = n
    assert not bad, f"Google Analytics shipped in {len(bad)} page(s): {bad}"


def test_every_shipped_page_carries_exactly_one_cloudflare_beacon_with_a_token():
    bad = {}
    for p in _pages():
        t = p.read_text(encoding="utf-8")
        n = t.count(BEACON)
        tags = [m for m in re.findall(r"<script\b[^>]*>", t) if BEACON in m]
        ok = n == 1 and len(tags) == 1 and "data-cf-beacon" in tags[0] and '"token"' in tags[0]
        if not ok:
            bad[str(p.relative_to(DIST))] = n
    assert not bad, f"beacon missing, doubled or tokenless in {len(bad)} page(s): {bad}"


def test_apply_discloses_what_is_true_now():
    t = APPLY.read_text(encoding="utf-8")
    assert "Google Analytics" not in t
    assert "d-14-measurement" not in t
    assert "Cloudflare Web Analytics" in t
    assert "sets no cookie" in t
