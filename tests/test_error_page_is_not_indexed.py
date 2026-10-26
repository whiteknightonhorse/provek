"""T-0567: the 404 document is not indexed, and the badge's "no such passport" image says so in
a header. `/404` answers 200 on some paths and `/badge/<unknown>.svg` answers 200 by design
(embedded images), so the status cannot keep them out of an index; an explicit noindex does."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
NOT_FOUND = WEB / "dist" / "404.html"


@pytest.mark.skipif(not NOT_FOUND.exists(), reason="web/dist not built")
def test_404_html_carries_exactly_one_noindex():
    html = NOT_FOUND.read_text(encoding="utf-8")
    assert len(re.findall(r'<meta name="robots" content="noindex">', html)) == 1
    assert html.index('name="robots"') < html.index("</head>")


def test_the_prerender_adds_noindex_to_the_404_branch_only():
    src = (WEB / "prerender.mjs").read_text(encoding="utf-8")
    assert src.count('content="noindex"') == 1
    assert src.index('content="noindex"') > src.index("const notFound = page(")
    assert src.index('content="noindex"') < src.index('writeFileSync(join(DIST, "404.html")')


def test_the_badge_marks_only_the_no_such_passport_answer_noindex():
    src = (WEB / "functions" / "badge" / "[id].js").read_text(encoding="utf-8")
    assert src.count("NOINDEX") == 3  # definition + the two "no such passport" returns
    for line in src.splitlines():
        if "NOINDEX)" in line:
            assert "no such passport" in line, line
