"""T-0540 (SITE-AUDIT-1026 B-06/B-07): every emitted page names an og:image and a description of
at most 160 characters. Walks web/dist, so a page added later is held without being listed here.

A test that cannot fail is not a test (law 5): `_problems` is exercised on a head that lacks the
image and on a description of 161 characters before it is trusted on the build."""
from __future__ import annotations

import html
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
MAX_DESCRIPTION = 160

built = pytest.mark.skipif(not (DIST / "index.html").exists(), reason="site not built in this checkout")


def _problems(doc: str) -> list[str]:
    head = doc.split("</head>", 1)[0]
    out = []
    if not re.search(r'<meta property="og:image" content="https://provek\.dev/[^"]+"', head):
        out.append("no og:image")
    m = re.search(r'<meta name="description" content="([^"]*)"', head)
    if m is None:
        out.append("no description")
    elif len(html.unescape(m.group(1))) > MAX_DESCRIPTION:
        out.append(f"description is {len(html.unescape(m.group(1)))} characters")
    return out


def test_the_check_can_fail():
    ok = '<head><meta property="og:image" content="https://provek.dev/og-image.png"><meta name="description" content="x"></head>'
    assert _problems(ok) == []
    assert _problems(ok.replace("og:image", "og:imag")) == ["no og:image"]
    assert _problems(ok.replace('content="x"', 'content="%s"' % ("y" * 161))) == ["description is 161 characters"]


@built
def test_every_page_has_an_og_image_and_a_short_description():
    pages = sorted(DIST.rglob("*.html"))
    assert len(pages) > 30, "the walk found too few pages to mean anything"
    bad = {str(p.relative_to(DIST)): _problems(p.read_text(encoding="utf-8")) for p in pages}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, bad


@built
def test_the_default_image_is_a_1200_by_630_png():
    data = (DIST / "og-image.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert int.from_bytes(data[16:20], "big") == 1200 and int.from_bytes(data[20:24], "big") == 630
