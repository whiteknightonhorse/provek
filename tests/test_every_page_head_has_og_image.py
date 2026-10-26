"""T-0540 (SITE-AUDIT-1026 B-06/B-07): every emitted page names an og:image and a description of
at most 160 characters. Walks web/dist, so a page added later is held without being listed here.

A test that cannot fail is not a test (law 5): `_problems` is exercised on a head that lacks the
image and on a description of 161 characters before it is trusted on the build."""
from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "web" / "dist"
MAX_DESCRIPTION = 160
# T-WB-05: the operator's designed card (provek-og-image.png, 1200x630). The hash is the design's.
EXPECTED_SHA256 = "993e35e9f3288fa9ace3709baa9bac27bb5694d1cacf9dfed52e10d076f4a00f"

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


def test_the_share_image_is_the_designed_asset():
    data = (ROOT / "web" / "public" / "og-image.png").read_bytes()
    assert hashlib.sha256(data).hexdigest() == EXPECTED_SHA256


def _unresolved(doc: str, dist: Path) -> list[str]:
    head = doc.split("</head>", 1)[0]
    out = []
    for url in re.findall(r'<meta (?:property="og:image"|name="twitter:image") content="([^"]*)"', head):
        prefix = "https://provek.dev/"
        if not url.startswith(prefix):
            out.append(f"{url} is not on https://provek.dev/")
        elif not (dist / url[len(prefix):]).is_file():
            out.append(f"{url} has no built file")
    return out


def test_the_resolve_check_can_fail(tmp_path):
    (tmp_path / "og-image.png").write_bytes(b"x")
    ok = '<head><meta property="og:image" content="https://provek.dev/og-image.png"><meta name="twitter:image" content="https://provek.dev/og-image.png"></head>'
    assert _unresolved(ok, tmp_path) == []
    assert len(_unresolved(ok.replace("og-image.png", "gone.png"), tmp_path)) == 2
    assert len(_unresolved(ok.replace("https://provek.dev/", "https://x.example/"), tmp_path)) == 2


@built
def test_every_image_tag_resolves_to_a_built_file():
    bad = {str(p.relative_to(DIST)): _unresolved(p.read_text(encoding="utf-8"), DIST) for p in sorted(DIST.rglob("*.html"))}
    bad = {k: v for k, v in bad.items() if v}
    assert not bad, bad
